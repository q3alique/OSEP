<#
    PathMaster Standalone (Windows - Safe Version)
    Goal: Unified Collection & Analysis for OSEP
    Version: 2.1 (Enhanced Compatibility & Safety)
#>

# 0. Safety & Platform Check
if ($env:OS -ne 'Windows_NT') {
    Write-Host "[!] PLATFORM MISMATCH: You are attempting to run a Windows PowerShell script on a non-Windows OS." -ForegroundColor Red
    Write-Host "    Please use PathMaster_Standalone.sh for Linux environments." -ForegroundColor Yellow
    exit
}

if ($PSVersionTable.PSVersion.Major -lt 5) {
    Write-Host "[!] VERSION WARNING: This script is optimized for PowerShell 5.1+. Some features may fail." -ForegroundColor Yellow
}

function Show-PathMasterReport {
    Write-Host "`n" + ("-" * 60) -ForegroundColor Yellow
    Write-Host "      PathMaster Standalone: OSEP Attack Path Report (Safe)" -ForegroundColor Yellow
    Write-Host ("-" * 60) -ForegroundColor Yellow

    # Global storage for DACL-based delegation paths (RBCD/Targeted Kerberoast)
    $DACLDelegations = New-Object System.Collections.Generic.List[PSObject]

    # 1. AD Classic
    Write-Host "`n=== AD CLASSIC ATTACK PATHS ===" -ForegroundColor Cyan
    
    $Searcher = $null

    try {
        # Method 1: The "Default" Way - Let Windows find the DC and Path automatically
        # This is the most reliable method for a domain-joined machine.
        $Searcher = New-Object System.DirectoryServices.DirectorySearcher
        
        # Verify it works by getting the root path
        $DomainPath = $Searcher.SearchRoot.Path
        Write-Host "[*] Successfully connected to Domain (Automatic): $DomainPath" -ForegroundColor Green
    } catch {
        # Fallback: Manual discovery if automatic fails
        try {
            $DnsDomain = $env:USERDNSDOMAIN
            if (-not $DnsDomain) {
                $DnsDomain = if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) { (Get-CimInstance Win32_ComputerSystem).Domain } else { (Get-WmiObject Win32_ComputerSystem).Domain }
            }
            
            if ($null -ne $DnsDomain -and $DnsDomain -notmatch "WORKGROUP") {
                $DomainPath = "DC=" + ($DnsDomain -replace "\.", ",DC=")
                $SearchRoot = [ADSI]"LDAP://$DomainPath"
                $Searcher = New-Object System.DirectoryServices.DirectorySearcher($SearchRoot)
                Write-Host "[*] Successfully connected to Domain (Manual): $DomainPath" -ForegroundColor Green
            }
        } catch {
            Write-Host "[!] General AD analysis failed: Could not bind to the domain." -ForegroundColor Red
            Write-Host "    Error: $($_.Exception.Message)" -ForegroundColor Gray
        }
    }

    if ($Searcher) {
        try {
            # Domain Admins (Try by name and common variations)
            $DAGroup = $null
            foreach ($Name in @("Domain Admins", "Administradores del dominio")) {
                $Searcher.Filter = "(&(objectCategory=group)(name=$Name))"
                $DAGroup = $Searcher.FindOne()
                if ($DAGroup) { break }
            }

            if ($DAGroup) {
                Write-Host "[*] Domain Admins Group Members:" -ForegroundColor Cyan
                $DAGroup.GetDirectoryEntry().member | ForEach-Object {
                    $Name = ($_ -split ",")[0] -replace "CN=", ""
                    Write-Host "    -> $Name" -ForegroundColor Yellow
                }
                Write-Host ""
            }

            # Domain Users Visibility Check
            $Searcher.Filter = "(objectCategory=person)"
            $UserCount = $Searcher.FindAll().Count
            Write-Host "[*] Total Domain Users Found: $UserCount" -ForegroundColor Cyan

            # Printer Bug / Coerced Auth (Spooler)
            try {
                $Domain = [System.DirectoryServices.ActiveDirectory.Domain]::GetCurrentDomain()
                $DCs = $Domain.DomainControllers
                if ($DCs) {
                    Write-Host "[*] Checking for Printer Bug (Coerced Auth) on DCs:" -ForegroundColor Cyan
                    foreach ($DC in $DCs) {
                        $DCName = $DC.Name
                        $NetBIOSName = ($DCName -split "\.")[0]
                        $Vulnerable = $false
                        foreach ($Target in @($DCName, $NetBIOSName)) {
                            if (Get-Item "\\$Target\pipe\spoolss" -ErrorAction SilentlyContinue) {
                                $Vulnerable = $true; break
                            }
                        }
                        if ($Vulnerable) {
                            Write-Host "    [!] VULNERABLE: ${DCName} has Spooler pipe active!" -ForegroundColor Red
                            Write-Host "        Action: Use SpoolSample or PetitPotam to coerce auth" -ForegroundColor Gray
                        } else {
                            Write-Host "    [.] ${DCName}: Spooler pipe not accessible" -ForegroundColor Gray
                        }
                    }
                    Write-Host ""
                }
            } catch {}

            # Kerberoast
            $Searcher.Filter = "(&(servicePrincipalName=*)(UserAccountControl:1.2.840.113556.1.4.803:=512)(!(UserAccountControl:1.2.840.113556.1.4.803:=2)))"
            $Searcher.FindAll() | ForEach-Object {
                Write-Host "[!] KERBEROASTING: $($_.Properties.name[0]) (SPN: $($_.Properties.serviceprincipalname -join ', '))" -ForegroundColor Red
            }

            # ASREPRoast
            $Searcher.Filter = "(&(objectCategory=person)(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))"
            $Searcher.FindAll() | ForEach-Object {
                Write-Host "[!] ASREPROASTING: $($_.Properties.name[0])" -ForegroundColor Red
            }

            # AD OBJECT CONTROL & DACL PATHS
            Write-Host "`n[*] Analyzing AD Object Control (High-Signal DACL Paths):" -ForegroundColor Cyan
            try {
                $Searcher.Filter = "(|(objectClass=computer)(objectClass=user)(objectClass=group)(objectClass=domainDNS))"
                $Searcher.PageSize = 1000
                $Searcher.FindAll() | ForEach-Object {
                    $Entry = $_.GetDirectoryEntry()
                    $TargetName = $Entry.name
                    $Ads = $Entry.psbase.ObjectSecurity
                    if ($Ads) {
                        $Rules = $Ads.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])
                        foreach ($Ace in $Rules) {
                            $Rights = $Ace.ActiveDirectoryRights.ToString()
                            $Guid = $Ace.ObjectType.ToString()
                            $Sid = $Ace.IdentityReference.Value
                            $Mask = [int]$Ace.ActiveDirectoryRights
                            
                            if ($Sid -match "^S-1-5-18$|^S-1-5-10$|^S-1-3-0$|^S-1-5-32-(544|548|549|550|551)$|^S-1-5-21-.*-(498|512|516|519|521)$") { continue }
                            
                            $PathType = ""; $Action = ""; $IsDelegationPath = $false

                            if ($Rights -match "GenericAll|WriteDacl|WriteOwner" -or ($Mask -band 0xf01ff) -eq 0xf01ff) {
                                $PathType = "FULL CONTROL"; $Action = "Take ownership, modify DACL, or reset password"
                            }
                            elseif ($Rights -match "GenericWrite" -or ($Mask -band 0x20034) -eq 0x20034 -or ($Rights -match "WriteProperty" -and ($Guid -eq "00000000-0000-0000-0000-000000000000" -or $Guid -eq "28be3a31-2529-11d1-a964-00c04f79f805"))) {
                                $IsDelegationPath = $true
                            }
                            elseif ($Guid -eq "00299570-246d-11d0-a768-00aa006e0529") {
                                $PathType = "FORCE CHANGE PASSWORD"; $Action = "Reset user password without knowing current one"
                            }
                            elseif ($Guid -eq "bf9679c0-0de6-11d0-a285-00aa003049e2" -or ($Rights -match "Self" -and $Guid -eq "bf9679c0-0de6-11d0-a285-00aa003049e2")) {
                                $PathType = "ADD MEMBER"; $Action = "Add yourself or others to this group"
                            }
                            elseif ($Guid -match "1131f6ad-9c07-11d1-f79f-00c04fc2dcd2|1131f6aa-9c07-11d1-f79f-00c04fc2dcd2") {
                                if ($Sid -match "^S-1-5-9$") { continue }
                                $PathType = "DCSYNC"; $Action = "Dump domain hashes via DS-Replication"
                            }
                            elseif ($Guid -match "e9ee9d55-7bc2-443d-996b-9f2447b99294|3d0cd1bc-5658-406a-939e-27038a834244") {
                                $PathType = "SECRET READ (LAPS/GMSA)"; $Action = "Read plaintext passwords from attributes"
                            }

                            if ($PathType -or $IsDelegationPath) {
                                try { $Ident = $Ace.IdentityReference.Translate([System.Security.Principal.NTAccount]).Value } catch { $Ident = $Sid }
                                if ($Ident -match "Key Admins|Cert Publishers") { continue }
                                
                                $HexMask = "0x{0:X}" -f $Mask
                                if ($IsDelegationPath) {
                                    $DACLDelegations.Add([PSCustomObject]@{Ident=$Ident; Target=$TargetName; Mask=$HexMask; Rights=$Rights})
                                } else {
                                    Write-Host "    [!] ${PathType}: $Ident -> $TargetName (Mask: $HexMask)" -ForegroundColor Red
                                    Write-Host "        Action: $Action" -ForegroundColor Gray
                                }
                            }
                        }
                    }
                }
                Write-Host ""
            } catch { Write-Host "[!] DACL analysis failed: $($_.Exception.Message)" -ForegroundColor Gray }

            # Delegations (Enhanced)
            Write-Host "`n[*] Analyzing Delegation Relationships:" -ForegroundColor Cyan
            try {
                foreach ($Path in $DACLDelegations) {
                    Write-Host "    [!] DACL-BASED: $($Path.Ident) -> $($Path.Target) (Mask: $($Path.Mask))" -ForegroundColor Red
                    Write-Host "        Rights: $($Path.Rights)" -ForegroundColor Yellow
                    Write-Host "        Action: Configure RBCD (Computers) or Targeted Kerberoast (Users)" -ForegroundColor Gray
                }

                $Searcher.Filter = "(|(userAccountControl:1.2.840.113556.1.4.803:=524288)(msDS-AllowedToDelegateTo=*)(msDS-AllowedToActOnBehalfOfOtherIdentity=*))"
                $Searcher.FindAll() | ForEach-Object {
                    $Entry = $_.GetDirectoryEntry()
                    $Name = $Entry.name
                    $UAC = [int]$Entry.useraccountcontrol[0]
                    $AllowedToDelegate = $Entry."msds-allowedtodelegateto"
                    $RBCD = $Entry."msds-allowedtoactonbehalfofotheridentity"

                    if ($UAC -band 524288) {
                        Write-Host "    [!] UNCONSTRAINED: $Name" -ForegroundColor Red
                        Write-Host "        Action: Compromise this host and wait for DA to connect" -ForegroundColor Gray
                    }
                    if ($AllowedToDelegate) {
                        $ProtoTransition = if ($UAC -band 16777216) { "WITH Protocol Transition" } else { "NO Protocol Transition" }
                        Write-Host "    [!] CONSTRAINED: $Name ($ProtoTransition)" -ForegroundColor Red
                        foreach ($SPN in $AllowedToDelegate) { Write-Host "        -> Can Delegate To: $SPN" -ForegroundColor Yellow }
                    }
                    if ($RBCD) {
                        Write-Host "    [!] RBCD: $Name (Resource-Based)" -ForegroundColor Red
                        Write-Host "        Note: msDS-AllowedToActOnBehalfOfOtherIdentity is set" -ForegroundColor Gray
                    }
                }
                Write-Host ""
            } catch { Write-Host "[!] Delegation analysis failed: $($_.Exception.Message)" -ForegroundColor Gray }

        } catch { Write-Host "[!] Specific AD component analysis failed: $($_.Exception.Message)" -ForegroundColor Gray }
    }

    # 2. Network & Pivoting
    Write-Host "`n=== NETWORK & PIVOTING ===" -ForegroundColor Cyan
    try {
        $Interfaces = if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) {
            Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object { $_.IPAddress -ne $null }
        } else {
            Get-WmiObject Win32_NetworkAdapterConfiguration | Where-Object { $_.IPAddress -ne $null }
        }
        foreach ($Int in $Interfaces) {
            $IPs = $Int.IPAddress -join ", "
            $Desc = $Int.Description
            Write-Host "[*] Interface: $Desc" -ForegroundColor Yellow
            Write-Host "    -> IPs: $IPs" -ForegroundColor White
        }
        
        # Check for multiple active subnets (potential dual-homing)
        $SubnetList = New-Object System.Collections.Generic.List[string]
        foreach ($Int in $Interfaces) {
            foreach ($Addr in $Int.IPAddress) {
                if ($Addr -match "^\d{1,3}\.\d{1,3}\.\d{1,3}\.\d{1,3}$" -and $Addr -notmatch "^127\.") {
                    $SubnetList.Add(($Addr -split "\.")[0..2] -join ".")
                }
            }
        }
        $UniqueSubnets = $SubnetList | Select-Object -Unique
        if ($UniqueSubnets.Count -gt 1) {
            Write-Host "[!] MULTI-HOMED HOST DETECTED: Potential pivoting point!" -ForegroundColor Red
            Write-Host "    Subnets discovered: $($UniqueSubnets -join ', ')" -ForegroundColor Gray
        }
    } catch {
        Write-Host "[!] Network analysis failed via WMI, falling back to ipconfig..." -ForegroundColor Gray
        ipconfig /all | Select-String "Description", "IPv4 Address", "Subnet Mask" | ForEach-Object { Write-Host "    $($_.ToString().Trim())" -ForegroundColor White }
    }

    # 3. Privileges
    Write-Host "`n=== DANGEROUS PRIVILEGES / LPE ===" -ForegroundColor Cyan
    try {
        $Privs = whoami /priv /fo csv | ConvertFrom-Csv
        $Privs | Where-Object { $_.PrivilegeName -match "SeImpersonate|SeAssignPrimary|SeBackup|SeRestore" } | ForEach-Object {
            Write-Host "[!] PRIVILEGE: $($_.PrivilegeName) ($($_.State))" -ForegroundColor Red
            if ($_.PrivilegeName -match "SeImpersonate") { Write-Host "    Action: Use PrintSpoofer or GodPotato" -ForegroundColor Gray }
        }
    } catch {}

    # 4. User Data, Flags & SSH Keys
    Write-Host "`n=== OSEP FLAGS, SSH KEYS & CREDENTIALS ===" -ForegroundColor Cyan
    $IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $TargetProfiles = if ($IsAdmin) { Get-ChildItem "C:\Users" -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName } else { @($env:USERPROFILE) }

    foreach ($Profile in $TargetProfiles) {
        if ($Profile -match "Public|Default|All Users") { continue }
        $UserName = Split-Path $Profile -Leaf
        
        # OSEP Flags Search
        foreach ($Sub in @("", "Desktop", "Documents")) {
            $SearchPath = Join-Path $Profile $Sub
            if (Test-Path $SearchPath) {
                Get-ChildItem -Path $SearchPath -Include "local.txt", "proof.txt", "secret.txt" -File -ErrorAction SilentlyContinue | ForEach-Object {
                    Write-Host "[!] FLAG FOUND ($UserName): $($_.FullName)" -ForegroundColor Red
                }
            }
        }

        # SSH Keys Search
        $SSHPath = Join-Path $Profile ".ssh"
        if (Test-Path $SSHPath) {
            $Keys = Get-ChildItem -Path $SSHPath -File -ErrorAction SilentlyContinue
            if ($Keys) {
                Write-Host "[*] SSH Folder found for $UserName" -ForegroundColor Yellow
                $Keys | ForEach-Object { Write-Host "    -> SSH Artifact: $($_.Name)" -ForegroundColor Gray }
            }
        }

        # Credential & Config Harvester (Scoped to User Profiles)
        foreach ($Sub in @("Documents", "Downloads", "Desktop")) {
            $Path = Join-Path $Profile $Sub
            if (Test-Path $Path) {
                Get-ChildItem -Path $Path -Include "*.config","*.xml","*.ps1","*.txt" -Recurse -Depth 2 -ErrorAction SilentlyContinue | ForEach-Object {
                    $Content = Get-Content $_.FullName -ErrorAction SilentlyContinue
                    foreach ($K in @("password", "pwd", "connectionstring", "secret")) {
                        if ($Content -match $K) {
                            Write-Host "[!] SECRET in $($_.FullName) (Keyword: $K)" -ForegroundColor Red; break
                        }
                    }
                }
            }
        }
    }

    # Global Credential Checks (Non-user specific)
    if (Test-Path "C:\inetpub\wwwroot") {
        Get-ChildItem -Path "C:\inetpub\wwwroot" -Include "*.config","*.xml","*.ps1","*.txt" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $Content = Get-Content $_.FullName -ErrorAction SilentlyContinue
            foreach ($K in @("password", "pwd", "connectionstring", "secret")) {
                if ($Content -match $K) {
                    Write-Host "[!] SECRET in $($_.FullName) (Keyword: $K)" -ForegroundColor Red; break
                }
            }
        }
    }

    # 5. Expert (CLM, ADCS)
    Write-Host "`n=== OSEP EXPERT PATHS ===" -ForegroundColor Cyan
    Write-Host "[*] CLM Status: $($ExecutionContext.SessionState.LanguageMode)" -ForegroundColor White
    if ($ExecutionContext.SessionState.LanguageMode -eq "ConstrainedLanguage") {
        Write-Host "[!] SYSTEM IS IN CLM - Use Custom Runspace or MSBuild bypass" -ForegroundColor Red
    }
    try {
        $ConfigDN = ([ADSI]"LDAP://RootDSE").Get("configurationNamingContext")
        $Searcher = New-Object System.DirectoryServices.DirectorySearcher([ADSI]"LDAP://CN=Public Key Services,CN=Services,$ConfigDN")
        $Searcher.Filter = "(objectClass=pKIEnrollmentService)"
        $Searcher.FindAll() | ForEach-Object {
            $Entry = $_.GetDirectoryEntry()
            Write-Host "    [!] ADCS CA: $($Entry.name) (Host: $($Entry.dnshostname))" -ForegroundColor Red
        }
        $Searcher.Filter = "(objectClass=pKICertificateTemplate)"
        $Searcher.FindAll() | ForEach-Object {
            $Entry = $_.GetDirectoryEntry()
            if ($Entry.Contains("mspki-certificate-name-flag") -and ([int]$Entry."mspki-certificate-name-flag"[0] -band 0x1)) {
                Write-Host "    [!] ESC1 TEMPLATE: $($Entry.name) (Enrollee Supplies SAN)" -ForegroundColor Red
            }
        }
    } catch {}

    Write-Host ("-" * 60) -ForegroundColor Yellow
}

Show-PathMasterReport

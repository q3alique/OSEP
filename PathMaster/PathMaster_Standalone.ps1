<#
    PathMaster Standalone (Windows)
    Goal: Unified Collection & Analysis for OSEP
    Version: 3.2 (OSEP Master - Contextual Secrets)
    Focus: On-Prem Attack Paths, Service Pivoting, and Lateral Movement.
#>

# 0. Safety & Platform Check
if ($env:OS -ne 'Windows_NT') {
    Write-Host "[!] PLATFORM MISMATCH: You are attempting to run a Windows PowerShell script on a non-Windows OS." -ForegroundColor Red
    Write-Host "    Please use PathMaster_Standalone.sh for Linux environments." -ForegroundColor Yellow
    exit
}

function Invoke-DeepSecretParser {
    param([string]$Content, [string]$Source)
    $Patterns = @{
        "OSEP Secret/Password" = "(?i)(password|passwd|pwd|secret|key|login|cred|connect)[\s:=]+['""]?([a-zA-Z0-9!@#$%^&*()_+={}\[\]|\\:;<>,.?/~`-]{6,})['""]?"
        "Database Connection" = "(?i)(Data Source|Server|User ID|Initial Catalog|Password|Pwd)=[^;]+"
        "JDBC/Connection"     = "(jdbc|mysql|postgresql|mongodb|oracle|sqlserver)://[a-zA-Z0-9_]+:[^@]+@[a-zA-Z0-9.-]+"
        "VNC/RDP/SSH Creds"   = "(?i)(vnc|rdp|ssh|ftp)[\s:=]+[^ ]*"
    }

    foreach ($Name in $Patterns.Keys) {
        if ($Content -match $Patterns[$Name]) {
            Write-Host "    [!] $Name found in $Source" -ForegroundColor Red
            Write-Host "        Match: $($Matches[0].Trim())" -ForegroundColor Gray
        }
    }
}

function Get-OSEPContextualSecrets {
    param($Profile, $UserName)
    
    # 1. Common OSEP Service Artifacts
    $ServicePaths = @{
        "mRemoteNG" = "AppData\Roaming\mRemoteNG\confCons.xml"
        "WinSCP"    = "AppData\Roaming\WinSCP.ini"
        "FileZilla" = "AppData\Roaming\FileZilla\sitemanager.xml"
        "PuTTY"     = "Software\SimonTatham\PuTTY\Sessions" # This is Registry, handled below
        "StickyNotes" = "AppData\Local\Packages\Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe\LocalState\plum.sqlite"
    }

    foreach ($Name in $ServicePaths.Keys) {
        $Path = Join-Path $Profile $ServicePaths[$Name]
        if (Test-Path $Path) {
            Write-Host "[!] $Name Artifact Found for ${UserName}: $Path" -ForegroundColor Red
            if ($Name -eq "mRemoteNG") { Write-Host "    Action: Decrypt XML using mRemoteNG-Decrypt or similar" -ForegroundColor Gray }
        }
    }

    # 2. Unattended & Deployment Files
    $UnattendPaths = @(
        "C:\Windows\Panther\Unattend.xml",
        "C:\Windows\Panther\Unattended.xml",
        "C:\Windows\System32\Sysprep\unattend.xml",
        "C:\Windows\System32\Sysprep\Panther\unattend.xml"
    )
    foreach ($Path in $UnattendPaths) {
        if (Test-Path $Path) {
            Write-Host "[!] UNATTENDED INSTALL FILE: $Path" -ForegroundColor Red
            $Content = Get-Content $Path -ErrorAction SilentlyContinue
            if ($Content -match "Password") { Write-Host "    Action: Check for <Password> tags in XML" -ForegroundColor Yellow }
        }
    }

    # 3. RDP & Saved Credentials
    if ($Profile -eq $env:USERPROFILE) {
        $SavedCreds = cmdkey /list | Select-String "Target:" -ErrorAction SilentlyContinue
        if ($SavedCreds) {
            Write-Host "[*] Saved Credentials Found (cmdkey):" -ForegroundColor Yellow
            $SavedCreds | ForEach-Object { Write-Host "    -> $($_.ToString().Trim())" -ForegroundColor Gray }
        }
    }
}

function Show-PathMasterReport {
    Write-Host "`n" + ("-" * 60) -ForegroundColor Yellow
    Write-Host "      PathMaster OSEP Master: Unified Attack Path Report" -ForegroundColor Yellow
    Write-Host ("-" * 60) -ForegroundColor Yellow

    $DACLDelegations = New-Object System.Collections.Generic.List[PSObject]

    # 1. AD Classic
    Write-Host "`n=== AD CLASSIC ATTACK PATHS ===" -ForegroundColor Cyan
    $Searcher = $null
    try {
        $DnsDomain = if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) { (Get-CimInstance Win32_ComputerSystem).Domain } else { (Get-WmiObject Win32_ComputerSystem).Domain }
        if ($null -ne $DnsDomain -and $DnsDomain -notmatch "WORKGROUP") {
            $DomainPath = "DC=" + ($DnsDomain -replace "\.", ",DC=")
            $SearchRoot = [ADSI]"LDAP://$DomainPath"
            $Searcher = New-Object System.DirectoryServices.DirectorySearcher($SearchRoot)
            Write-Host "[*] Connected to Domain: $DomainPath" -ForegroundColor Green
        }
    } catch { $Searcher = $null }

    if ($Searcher) {
        try {
            # AD Checks (DA, PrinterBug, Roasting, DACLs, Delegations)
            $DAGroup = $null
            foreach ($Name in @("Domain Admins", "Administradores del dominio")) {
                $Searcher.Filter = "(&(objectCategory=group)(name=$Name))"
                $DAGroup = $Searcher.FindOne()
                if ($DAGroup) { break }
            }
            if ($DAGroup) {
                Write-Host "[*] Domain Admins:" -ForegroundColor Cyan
                $DAGroup.GetDirectoryEntry().member | ForEach-Object { Write-Host "    -> $((($_ -split ',')[0]) -replace 'CN=', '')" -ForegroundColor Yellow }
            }

            # Printer Bug
            try {
                $DCs = [System.DirectoryServices.ActiveDirectory.Domain]::GetCurrentDomain().DomainControllers
                if ($DCs) {
                    Write-Host "[*] Checking Printer Bug on DCs:" -ForegroundColor Cyan
                    foreach ($DC in $DCs) {
                        if (Get-Item "\\$($DC.Name)\pipe\spoolss" -ErrorAction SilentlyContinue) {
                            Write-Host "    [!] VULNERABLE: $($DC.Name) spoolss pipe active!" -ForegroundColor Red
                        }
                    }
                }
            } catch {}

            # Kerberoast & ASREPRoast
            $Searcher.Filter = "(&(servicePrincipalName=*)(UserAccountControl:1.2.840.113556.1.4.803:=512)(!(UserAccountControl:1.2.840.113556.1.4.803:=2)))"
            $Searcher.FindAll() | ForEach-Object { Write-Host "[!] KERBEROASTABLE: $($_.Properties.name[0])" -ForegroundColor Red }
            $Searcher.Filter = "(&(objectCategory=person)(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))"
            $Searcher.FindAll() | ForEach-Object { Write-Host "[!] ASREPROASTABLE: $($_.Properties.name[0])" -ForegroundColor Red }

            # DACL & Delegations (Simplified Master Logic)
            $Searcher.Filter = "(|(objectClass=computer)(objectClass=user)(objectClass=group)(objectClass=domainDNS))"
            $Searcher.PageSize = 500
            $Searcher.FindAll() | ForEach-Object {
                $Entry = $_.GetDirectoryEntry()
                $TargetName = $Entry.name
                $Ads = $Entry.psbase.ObjectSecurity
                if ($Ads) {
                    $Rules = $Ads.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])
                    foreach ($Ace in $Rules) {
                        $Rights = $Ace.ActiveDirectoryRights.ToString()
                        $Mask = [int]$Ace.ActiveDirectoryRights
                        $Sid = $Ace.IdentityReference.Value
                        if ($Sid -match "^S-1-5-18$|^S-1-5-10$|^S-1-3-0$|^S-1-5-32-54[4-9]|^S-1-5-21-.*-(498|51[269]|521)$") { continue }
                        
                        if ($Rights -match "GenericAll|WriteDacl|WriteOwner" -or ($Mask -band 0xf01ff) -eq 0xf01ff) {
                            try { $Ident = $Ace.IdentityReference.Translate([System.Security.Principal.NTAccount]).Value } catch { $Ident = $Sid }
                            Write-Host "    [!] FULL CONTROL: $Ident -> $TargetName" -ForegroundColor Red
                        }
                    }
                }
                # Delegation Check
                if ($Entry.Properties.Contains("userAccountControl") -and ($Entry.useraccountcontrol[0] -band 524288)) { Write-Host "    [!] UNCONSTRAINED DELEGATION: $TargetName" -ForegroundColor Red }
                if ($Entry.Properties.Contains("msDS-AllowedToDelegateTo")) { Write-Host "    [!] CONSTRAINED DELEGATION: $TargetName" -ForegroundColor Red }
            }
        } catch {}
    }

    # 2. Network & Pivoting
    Write-Host "`n=== NETWORK & PIVOTING ===" -ForegroundColor Cyan
    try {
        $Interfaces = if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) { Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object { $_.IPAddress -ne $null } } else { Get-WmiObject Win32_NetworkAdapterConfiguration | Where-Object { $_.IPAddress -ne $null } }
        $Subnets = @()
        foreach ($Int in $Interfaces) {
            $IPs = $Int.IPAddress -join ", "
            Write-Host "[*] Interface: $($Int.Description) -> $IPs" -ForegroundColor White
            $Int.IPAddress | ForEach-Object { if ($_ -match "^\d+\.\d+\.\d+") { $Subnets += ($Matches[0]) } }
        }
        if (($Subnets | Select-Object -Unique).Count -gt 1) { Write-Host "[!] MULTI-HOMED HOST: Pivoting potential detected!" -ForegroundColor Red }
    } catch {}

    # 3. System & Privileges
    Write-Host "`n=== SYSTEM SECURITY & PRIVILEGES ===" -ForegroundColor Cyan
    try {
        whoami /priv /fo csv | ConvertFrom-Csv | Where-Object { $_.PrivilegeName -match "SeImpersonate|SeAssignPrimary|SeBackup|SeRestore" } | ForEach-Object { Write-Host "[!] PRIVILEGE: $($_.PrivilegeName)" -ForegroundColor Red }
        Get-ChildItem Env: | Where-Object { $_.Name -match "PASS|SECRET|TOKEN|KEY|USER" } | ForEach-Object { Write-Host "    -> ENV: $($_.Name)=$($_.Value)" -ForegroundColor Gray }
    } catch {}

    # 4. OSEP Contextual Secrets & Harvesting
    Write-Host "`n=== OSEP CONTEXTUAL SECRETS & HARVESTING ===" -ForegroundColor Cyan
    $IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
    $TargetProfiles = if ($IsAdmin) { Get-ChildItem "C:\Users" -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName } else { @($env:USERPROFILE) }

    foreach ($Profile in $TargetProfiles) {
        if ($Profile -match "Public|Default|All Users") { continue }
        $UserName = Split-Path $Profile -Leaf
        Write-Host "`n[*] Analyzing Profile: $UserName" -ForegroundColor Yellow
        
        # OSEP Artifacts (mRemoteNG, WinSCP, etc.)
        Get-OSEPContextualSecrets -Profile $Profile -UserName $UserName
        
        # PowerShell History & Profiles
        $HistoryPaths = @(
            "AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt",
            "Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1",
            ".ssh\known_hosts"
        )
        foreach ($RelPath in $HistoryPaths) {
            $FullPath = Join-Path $Profile $RelPath
            if (Test-Path $FullPath) {
                Write-Host "[*] Checking: $RelPath" -ForegroundColor Gray
                Get-Content $FullPath -ErrorAction SilentlyContinue | ForEach-Object { Invoke-DeepSecretParser -Content $_ -Source $RelPath }
            }
        }

        # Targeted Credential Search
        foreach ($Sub in @("Documents", "Downloads", "Desktop", "AppData\Local\Temp")) {
            $Path = Join-Path $Profile $Sub
            if (Test-Path $Path) {
                Get-ChildItem -Path $Path -Include "*.config","*.xml","*.ps1","*.txt","*.db","*.sqlite","*.sql" -Recurse -Depth 2 -ErrorAction SilentlyContinue | ForEach-Object {
                    if ($_.Extension -match "db|sqlite") { Write-Host "    [*] Database found: $($_.Name)" -ForegroundColor Gray }
                    else {
                        $Content = Get-Content $_.FullName -ErrorAction SilentlyContinue
                        Invoke-DeepSecretParser -Content $Content -Source $_.Name
                    }
                }
            }
        }
    }

    # IIS & Shared Services
    if (Test-Path "C:\inetpub\wwwroot") {
        Write-Host "`n[*] Checking IIS Infrastructure:" -ForegroundColor Cyan
        Get-ChildItem "C:\inetpub\wwwroot" -Include "web.config","*.php","*.asp","*.aspx" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
            $Content = Get-Content $_.FullName -ErrorAction SilentlyContinue
            Invoke-DeepSecretParser -Content $Content -Source $_.FullName
        }
    }

    # 5. Expert (CLM, ADCS)
    Write-Host "`n=== OSEP EXPERT PATHS ===" -ForegroundColor Cyan
    Write-Host "[*] CLM Status: $($ExecutionContext.SessionState.LanguageMode)" -ForegroundColor White
    try {
        $ConfigDN = ([ADSI]"LDAP://RootDSE").Get("configurationNamingContext")
        $ADCSearcher = New-Object System.DirectoryServices.DirectorySearcher([ADSI]"LDAP://CN=Public Key Services,CN=Services,$ConfigDN")
        $ADCSearcher.Filter = "(objectClass=pKIEnrollmentService)"
        $ADCSearcher.FindAll() | ForEach-Object { Write-Host "    [!] ADCS CA: $($_.GetDirectoryEntry().name)" -ForegroundColor Red }
        $ADCSearcher.Filter = "(objectClass=pKICertificateTemplate)"
        $ADCSearcher.FindAll() | ForEach-Object {
            $Entry = $_.GetDirectoryEntry()
            if ($Entry.Contains("mspki-certificate-name-flag") -and ([int]$Entry."mspki-certificate-name-flag"[0] -band 0x1)) {
                Write-Host "    [!] ESC1 TEMPLATE: $($Entry.name)" -ForegroundColor Red
            }
        }
    } catch {}

    Write-Host ("-" * 60) -ForegroundColor Yellow
}

Show-PathMasterReport

<# PathMaster Module: AD DACL & Delegations #>
Write-Host "=== AD DACL & DELEGATIONS ===" -ForegroundColor Cyan
try {
    $DnsDomain = if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) { (Get-CimInstance Win32_ComputerSystem).Domain } else { (Get-WmiObject Win32_ComputerSystem).Domain }
    if ($null -ne $DnsDomain -and $DnsDomain -notmatch "WORKGROUP") {
        $Searcher = New-Object System.DirectoryServices.DirectorySearcher([ADSI]"LDAP://DC=" + ($DnsDomain -replace "\.", ",DC="))
        $Searcher.Filter = "(|(objectClass=computer)(objectClass=user)(objectClass=group)(objectClass=domainDNS))"
        $Searcher.PageSize = 500
        $Searcher.FindAll() | ForEach-Object {
            $Entry = $_.GetDirectoryEntry()
            $TargetName = $Entry.name
            $Ads = $Entry.psbase.ObjectSecurity
            if ($Ads) {
                $Rules = $Ads.GetAccessRules($true, $true, [System.Security.Principal.SecurityIdentifier])
                foreach ($Ace in $Rules) {
                    if ($Ace.ActiveDirectoryRights.ToString() -match "GenericAll|WriteDacl|WriteOwner" -or ([int]$Ace.ActiveDirectoryRights -band 0xf01ff) -eq 0xf01ff) {
                        $Sid = $Ace.IdentityReference.Value
                        if ($Sid -match "^S-1-5-18$|^S-1-5-10$|^S-1-3-0$|^S-1-5-32-54[4-9]|^S-1-5-21-.*-(498|51[269]|521)$") { continue }
                        try { $Ident = $Ace.IdentityReference.Translate([System.Security.Principal.NTAccount]).Value } catch { $Ident = $Sid }
                        Write-Host "    [!] FULL CONTROL: $Ident -> $TargetName" -ForegroundColor Red
                    }
                }
            }
            if ($Entry.Properties.Contains("userAccountControl") -and ($Entry.useraccountcontrol[0] -band 524288)) { Write-Host "    [!] UNCONSTRAINED DELEGATION: $TargetName" -ForegroundColor Red }
            if ($Entry.Properties.Contains("msDS-AllowedToDelegateTo")) { Write-Host "    [!] CONSTRAINED DELEGATION: $TargetName" -ForegroundColor Red }
        }
    }
} catch { Write-Host "[!] Error: $($_.Exception.Message)" -ForegroundColor Red }

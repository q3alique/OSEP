<# PathMaster Module: AD Audit #>
Write-Host "=== AD CLASSIC AUDIT ===" -ForegroundColor Cyan
try {
    $DnsDomain = if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) { (Get-CimInstance Win32_ComputerSystem).Domain } else { (Get-WmiObject Win32_ComputerSystem).Domain }
    if ($null -ne $DnsDomain -and $DnsDomain -notmatch "WORKGROUP") {
        $DomainPath = "DC=" + ($DnsDomain -replace "\.", ",DC=")
        $SearchRoot = [ADSI]"LDAP://$DomainPath"
        $Searcher = New-Object System.DirectoryServices.DirectorySearcher($SearchRoot)
        
        # Domain Admins
        foreach ($Name in @("Domain Admins", "Administradores del dominio")) {
            $Searcher.Filter = "(&(objectCategory=group)(name=$Name))"
            $DAGroup = $Searcher.FindOne()
            if ($DAGroup) {
                Write-Host "[*] Domain Admins:" -ForegroundColor Cyan
                $DAGroup.GetDirectoryEntry().member | ForEach-Object { Write-Host "    -> $((($_ -split ',')[0]) -replace 'CN=', '')" -ForegroundColor Yellow }
                break
            }
        }

        # Printer Bug
        try {
            $DCs = [System.DirectoryServices.ActiveDirectory.Domain]::GetCurrentDomain().DomainControllers
            foreach ($DC in $DCs) {
                if (Get-Item "\\$($DC.Name)\pipe\spoolss" -ErrorAction SilentlyContinue) {
                    Write-Host "[!] VULNERABLE: $($DC.Name) spoolss pipe active (Printer Bug)!" -ForegroundColor Red
                }
            }
        } catch {}

        # Roasting
        $Searcher.Filter = "(&(servicePrincipalName=*)(UserAccountControl:1.2.840.113556.1.4.803:=512)(!(UserAccountControl:1.2.840.113556.1.4.803:=2)))"
        $Searcher.FindAll() | ForEach-Object { Write-Host "[!] KERBEROASTABLE: $($_.Properties.name[0])" -ForegroundColor Red }
        $Searcher.Filter = "(&(objectCategory=person)(objectClass=user)(userAccountControl:1.2.840.113556.1.4.803:=4194304))"
        $Searcher.FindAll() | ForEach-Object { Write-Host "[!] ASREPROASTABLE: $($_.Properties.name[0])" -ForegroundColor Red }
    } else { Write-Host "[.] System is not in a domain." -ForegroundColor Gray }
} catch { Write-Host "[!] Error: $($_.Exception.Message)" -ForegroundColor Red }

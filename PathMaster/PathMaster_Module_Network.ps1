<# PathMaster Module: Network & Pivoting #>
Write-Host "=== NETWORK & PIVOTING ===" -ForegroundColor Cyan
try {
    $Interfaces = if (Get-Command Get-CimInstance -ErrorAction SilentlyContinue) { Get-CimInstance Win32_NetworkAdapterConfiguration | Where-Object { $_.IPAddress -ne $null } } else { Get-WmiObject Win32_NetworkAdapterConfiguration | Where-Object { $_.IPAddress -ne $null } }
    $Subnets = @()
    foreach ($Int in $Interfaces) {
        $IPs = $Int.IPAddress -join ", "
        Write-Host "[*] Interface: $($Int.Description) -> $IPs" -ForegroundColor White
        $Int.IPAddress | ForEach-Object { if ($_ -match "^\d+\.\d+\.\d+") { $Subnets += ($Matches[0]) } }
    }
    $UniqueSubnets = $Subnets | Select-Object -Unique
    if ($UniqueSubnets.Count -gt 1) {
        Write-Host "[!] MULTI-HOMED HOST DETECTED!" -ForegroundColor Red
        Write-Host "    Subnets: $($UniqueSubnets -join ', ')" -ForegroundColor Gray
    }
} catch { Write-Host "[!] Error: $($_.Exception.Message)" -ForegroundColor Red }

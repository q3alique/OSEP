<#
.SYNOPSIS
    Reliably enable all available token privileges using NtObjectManager.
    
.DESCRIPTION
    This script leverages NtObjectManager to open a real handle to the 
    current process token and attempts to enable every privilege 
    individually. This is the most reliable and 'clean' modern approach.

.USAGE
    PS C:\> . .\Enable-AllPrivileges.ps1
#>

# 1. Ensure NtObjectManager is available
if (-not (Get-Module -Name NtObjectManager)) {
    Write-Host "[*] NtObjectManager not found. Attempting to import/install..." -ForegroundColor Yellow
    try {
        Import-Module NtObjectManager -ErrorAction Stop
    } catch {
        Write-Host "[*] Installing NtObjectManager for current user..." -ForegroundColor Cyan
        Install-Module NtObjectManager -Scope CurrentUser -Force -SkipPublisherCheck
        Import-Module NtObjectManager
    }
}

# 2. Main Logic
try {
    # Open a REAL handle to the current process token (more stable than pseudo)
    $Token = Get-NtToken -Primary
    
    # Get all privileges present in the token
    $Privs = $Token.Privileges
    
    Write-Host "[*] Attempting to enable $($Privs.Count) privileges one-by-one..." -ForegroundColor Cyan
    
    foreach ($P in $Privs) {
        $Name = $P.Name
        if ($P.Enabled) {
            Write-Host "  [*] $Name is already enabled." -ForegroundColor DarkGray
            continue
        }

        try {
            # Attempt to enable individually
            Set-NtTokenPrivilege -Token $Token -Privileges $Name -ErrorAction Stop
            Write-Host "  [+] Successfully enabled: $Name" -ForegroundColor Green
        } catch {
            # Silently fail for privileges we don't have permission to adjust
            # (Matches your 'one-by-one' philosophy)
        }
    }
    
    Write-Host "`n[*] Done. Current Privilege State:" -ForegroundColor Cyan
    $Token.Privileges | Select-Object Name, Enabled | Format-Table -AutoSize

} catch {
    Write-Error "A critical error occurred: $_"
} finally {
    if ($Token) { $Token.Close() }
}

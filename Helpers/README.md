# Helpers

A collection of PowerShell and Python utility scripts designed for various stages of an engagement, from initial enumeration to post-exploitation.

## AppLocker-Enum.ps1
This script identifies writable directories that are likely permitted by AppLocker. It checks common paths and attempts to create a temporary file to verify access.

### Usage
```powershell
. .\AppLocker-Enum.ps1
```

## Credential Dumping
Scripts to extract credentials from various sources:
- **decrypt_chromium.py**: Extracts and decrypts stored passwords from Chromium-based browsers.
- **Dump-BrowserCredentials.ps1**: PowerShell script for browser credential extraction.
- **Dump-LSASecrets.ps1**: Extracts LSA secrets from the registry.
- **Dump-SAMHashes.ps1**: Dumps SAM hashes for offline cracking.

## AVDisarm
A specialized folder for AV and EDR evasion techniques.
- **AMSI-Bypass.ps1**: Techniques to bypass Anti-Malware Scan Interface.
- **ETW-Bypass.ps1**: Disables Event Tracing for Windows.
- **Enum-Protections.ps1**: Identifies active security products and protections.
- **Kill-Defender**: Scripts and C# sources to disable or interfere with Windows Defender.
- **Kill-Firewall**: Methods to disable the host-based firewall.

## InstallUtilBypass
Provides templates to bypass application whitelisting using the `InstallUtil.exe` binary.
- **AssemblyLoader**: Loads C# assemblies in-memory.
- **ProcessInjector**: Injects shellcode into another process.
- **ShellcodeRunner**: Standard shellcode execution via `InstallUtil.exe`.

## PowerShellRunner
C# source code to execute PowerShell commands from within a .NET assembly, effectively bypassing some PowerShell execution policies and restricted language modes.

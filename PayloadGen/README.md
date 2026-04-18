# PayloadGen (Project Genesis)

A multi-stage payload infrastructure generator designed to produce advanced C# source code and automated loaders for sophisticated execution techniques. This tool automates the process of generating, obfuscating, and compiling payloads for various injection methods suitable for OSEP-level engagements.

## Execution Techniques & Assets

### Dynamic Loaders (C# / EXE)
- **Process Hollowing**: Spawns a suspended process (svchost.exe) and replaces its entry point with the malicious payload.
- **Memory Migrator (Sections)**: Injects shellcode into an existing process (explorer.exe) using shared memory sections to avoid `WriteProcessMemory`.
- **EarlyBird Runner (APC)**: Uses `QueueUserAPC` to execute shellcode early in a new process's (notepad.exe) initialization, bypassing some startup hooks.
- **HollyBird Phantom (Sections + APC)**: Combines shared section mapping and APC triggering for a highly stealthy execution without entry point patching.

### Script-Based Loaders
- **Reflective Loader (.txt)**: In-memory AMSI bypass combined with reflective shellcode injection via PowerShell.
- **XOR Stager (.ps1)**: Lightweight stage-0 downloader and XOR-decrypted executor.
- **VBA Macro**: Office macro using WMI de-chaining for stealthy execution.
- **HTA Stager**: HTML Application stager for initial access.
- **ASPX Shell**: XOR-encrypted ASPX web shell for persistence.

## Features
- **MSFvenom & Sliver Integration**: Automatically generates shellcode for Metasploit and Sliver C2 frameworks.
- **Automated Compilation**: Uses `mcs` to compile C# source code into 64-bit executables directly on Linux.
- **Polymorphic Obfuscation**: Randomizes symbols, namespaces, and class names in the generated source code.
- **Encrypted Payloads**: Shellcode is automatically encrypted using XOR with a randomly generated or user-specified key.
- **Infrastructure Guide**: Automatically generates a deployment guide and listener commands for both MSF and Sliver.

## Usage

### Required Parameters
- `--lhost <IP/IFACE>`: The IP address or network interface (e.g., eth0, tun0) of the listener.

### Optional Parameters
- `--key <INT>`: Specified XOR encryption key (default: random).
- `--sli-port-x64 <PORT>`: Listening port for Sliver x64 (default: 4443).
- `--sli-port-x86 <PORT>`: Listening port for Sliver x86 (default: 5553).
- `--met-port-x64 <PORT>`: Listening port for Metasploit x64 (default: 2223).
- `--met-port-x86 <PORT>`: Listening port for Metasploit x86 (default: 1113).

### Example
Generate a full infrastructure for a listener on `eth0`:
```bash
python3 PayloadGen.py --lhost eth0
```

## Output
All generated assets, including compiled EXEs, source code, and a custom `README.md` for the specific deployment, are saved in a directory named after the LHOST IP (e.g., `output/10-10-10-10/`).

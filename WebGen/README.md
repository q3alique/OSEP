# WebGen

A comprehensive generator for web-based payloads including interactive web shells and reverse shells for major server-side technologies (ASPX, PHP, JSP). This tool simplifies the creation of ready-to-use payloads for web-based initial access and post-exploitation, with built-in randomization and obfuscation.

## Supported Technologies & Suites

### ASPX (IIS / .NET)
- **Webshell**: Interactive web shell with a secret-key access mechanism.
- **Classic Revshell**: TCP client-based reverse shell for standard `nc` listeners.
- **Meterpreter Runner**: XOR-encrypted shellcode runner using delegates for evasion.
- **Sliver Runner**: Advanced shellcode injection runner specifically for Sliver C2.

### PHP (Apache / Nginx)
- **Webshell**: Lightweight, password-protected interactive web shell.
- **Classic Revshell**: Standard PHP reverse shell for Linux/Windows.
- **Meterpreter (Pure PHP)**: Pure PHP implementation of the Meterpreter reverse shell.
- **Sliver (Stager)**: MSF-compatible PHP stager for Sliver.

### JSP (Tomcat / Java)
- **Webshell**: Java-based interactive web shell with password protection.
- **Classic Revshell**: Standard JSP reverse shell.
- **Meterpreter (Pure Java)**: Pure Java implementation of the JSP reverse shell.

## Features
- **Polymorphic Randomization**: Automatically randomizes variable names, function names, and secret keys within the templates to evade signature-based detection.
- **MSFvenom & Sliver Integration**: Automatically generates and integrates shellcode and pure-language payloads for both frameworks.
- **XOR Encryption**: Shellcode-based runners utilize XOR encryption with random or specified keys.
- **Deployment Guide**: Generates a custom `README.md` and appropriate listener commands for every generated payload suite.

## Usage

### Parameters
- `--lhost <IP/IFACE>`: (Required) The IP address or network interface (e.g., eth0) of the target server.
- `--callback-host <IP>`: The callback IP for reverse shells (defaults to `--lhost`).
- `--key <INT>`: Specified XOR encryption key (default: random).
- `--msf-port <PORT>`: Listening port for Metasploit-related payloads (default: 2223).
- `--sliver-port <PORT>`: Listening port for Sliver-related payloads (default: 4443).

### Example
Generate a full web arsenal for a target on `10.10.10.10` with a callback to your local IP:
```bash
python3 WebGen.py --lhost 10.10.10.10 --callback-host 10.10.14.5
```

## Output
All generated assets, including the web files and a deployment `README.md`, are saved in a directory named after the target host (e.g., `output/10-10-10-10/`).

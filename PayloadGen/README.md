# PayloadGen (Project Genesis)

A multi-stage payload infrastructure generator designed to produce advanced C# source code for sophisticated execution techniques. This tool automates the process of generating, obfuscating, and preparing payloads for various injection methods.

## Execution Techniques
- **Process Hollowing**: Creates a new process in a suspended state and replaces its memory with the malicious payload.
- **Process Injection**: Injects shellcode into an existing process's memory space.
- **Early Bird Injection**: An advanced technique that uses `QueueUserAPC` to execute shellcode early in a process's initialization.
- **Injector**: Standard C# injector template with multiple evasion options.

## Features
- **Dynamic Obfuscation**: Randomizes variable and function names in the generated C# source code.
- **Encrypted Payloads**: Shellcode is automatically encrypted using XOR with a randomly generated key.
- **Configurable Network Info**: Easily specify LHOST and LPORT for the shellcode to be used within the templates.

## Usage
Generate a process hollowing payload with XOR-encrypted shellcode:
```bash
python3 PayloadGen.py --technique hollowing --shellcode /path/to/payload.bin --lhost 10.10.10.10 --lport 443 -o hollower.cs
```

Create an Early Bird injection source file:
```bash
python3 PayloadGen.py --technique earlybird --shellcode /path/to/payload.bin --lhost 10.10.10.10 --lport 443 -o earlybird_payload.cs
```

### Arguments
- `--technique`: Execution technique to use (hollowing, injection, earlybird, injector).
- `--shellcode`: Path to the raw shellcode .bin file.
- `--lhost/--lport`: Local network configuration for the payload.
- `-o, --output`: Filename for the generated C# source file.

## Templates
- **templates/hollowing.cs**: Base source for process hollowing.
- **templates/earlybird.cs**: Base source for Early Bird injection.
- **templates/injector.cs**: Standard injection template.

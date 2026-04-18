# PayloadCompiler

An automated C# compiler designed to produce executable payloads with built-in evasion and obfuscation. It supports both classic Mono-based compilation for small binaries and modern .NET Core for self-contained execution, with specialized logic for handling common OSEP-related dependencies.

## Features
- **Multiple Compilation Modes**: Choose between `classic` (uses `mcs` / Mono) for minimal file size and `sota` (uses `dotnet publish`) for self-contained binaries.
- **Aggressive Obfuscation**: Level-based source obfuscation (`none`, `basic`, `aggressive`) that includes string encryption (XOR), keyword randomization, and metadata stripping.
- **Shellcode Injection**: Injects shellcode from a `.bin` file into a C# source template using combined XOR and ROT encryption.
- **Universal Dependency Resolver**: Injects logic to automatically resolve and load missing DLLs from common system paths or the local directory at runtime.
- **Dependency Oracle**: Automatically analyzes compilation errors and suggests which missing DLLs are needed and where to find them in a standard Windows environment.

## Usage

### Required Parameters
- `-p, --path <FILE>`: Path to the C# source file (`.cs`) to compile.

### Optional Parameters
- `-m, --mode <MODE>`: Compilation mode (`classic`, `sota`). Default is `classic`.
- `-f, --format <EXT>`: Output format (`exe`, `dll`). Default is `exe`.
- `-o, --output <NAME>`: Custom name for the generated output file.
- `--obfuscate <LEVEL>`: Obfuscation level (`none`, `basic`, `aggressive`). Default is `none`.
- `--shellcode <PATH>`: Path to a raw shellcode `.bin` file to inject into the source.
- `--auto-resolve`: Enable the Universal Dependency Resolver logic.
- `-h, --help`: Show the detailed help message.

### Examples

Compile a standard C# file with aggressive obfuscation:
```bash
python3 PayloadCompiler.py -p my_payload.cs --obfuscate aggressive -o stealth.exe
```

Inject shellcode into a template and enable the dependency resolver:
```bash
python3 PayloadCompiler.py -p injector_template.cs --shellcode beacon.bin --auto-resolve -o final_payload.exe
```

Compile a C# DLL using Mono:
```bash
python3 PayloadCompiler.py -p library.cs -f dll -o helper.dll
```

## Dependency Management
The compiler looks for additional DLLs in:
1. The local directory of the source file.
2. A central repository at `/home/kali/OSEP-TOOLS/PayloadCompiler/Refs/`.
3. Standard Mono library paths.

If a compilation fails due to missing namespaces (e.g., `System.Management.Automation`), the **Dependency Oracle** will provide specific advice on which DLL to add to the `Refs` folder.

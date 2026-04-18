# PayloadCompiler

An automated C# compiler designed to produce executable payloads with built-in evasion and obfuscation. It supports both classic Mono-based compilation for small binaries and modern .NET Core for self-contained execution.

## Features
- **Multiple Compilation Modes**: Choose between `classic` (Mono) for minimal file size and `sota` (Dotnet Publish) for self-contained binaries.
- **Built-in Obfuscation**: Three levels of source-level obfuscation: `none`, `basic`, and `aggressive`.
- **Shellcode Injection**: Seamlessly inject XOR+ROT encrypted shellcode into any C# template.
- **Universal Dependency Resolver**: Automatically injects logic to resolve missing DLLs at runtime.
- **Binary Packing**: Integrates with UPX to pack the final executable and reduce its on-disk footprint.

## Usage
Compile a classic executable with aggressive obfuscation:
```bash
python3 PayloadCompiler.py -m classic --obfuscate aggressive /path/to/source.cs -o payload.exe
```

Inject shellcode into a C# template and pack the resulting binary:
```bash
python3 PayloadCompiler.py -m classic --shellcode /path/to/shellcode.bin --pack /path/to/template.cs -o injector.exe
```

### Arguments
- `-m, --mode`: Compilation mode (classic, sota).
- `--obfuscate`: Obfuscation level (none, basic, aggressive).
- `--shellcode`: Path to a shellcode .bin file for injection.
- `--auto-resolve`: Injects dependency resolution logic.
- `--pack`: Enables UPX packing.

## Requirements
- **Mono (mcs)**: Required for `classic` mode.
- **.NET SDK**: Required for `sota` mode.
- **UPX**: Required if the `--pack` flag is used.

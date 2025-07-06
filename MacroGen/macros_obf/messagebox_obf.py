metadata = {
    "name": "MessageBox_Obfuscated",
    "description": "Displays a message box with obfuscation techniques applied.",
    "parameters": []
}

def generate_macro_code(params):
    return '''
Sub AutoOpen()
    Dim m(), i As Integer, s As String
    m = Array(77, 97, 99, 114, 111, 32, 84, 101, 115, 116, 33)
    For i = 0 To UBound(m)
        s = s & Chr(m(i))
    Next
    MsgBox s
End Sub

Sub Document_Open()
    AutoOpen
End Sub
'''

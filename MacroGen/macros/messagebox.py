metadata = {
    "name": "MessageBox",
    "description": "Shows a simple message box to confirm macro execution.",
    "parameters": []
}

def generate_macro_code(params):
    return '''
Sub AutoOpen()
    MsgBox "Macro Test!"
End Sub
Sub Document_Open()
    AutoOpen
End Sub
'''
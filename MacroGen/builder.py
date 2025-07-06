import platform

IS_WINDOWS = platform.system() == "Windows"

if IS_WINDOWS:
    import win32com.client

    def create_docm(macro_code, output_path):
        word = win32com.client.Dispatch("Word.Application")
        word.Visible = False
        doc = word.Documents.Add()
        doc.Content.Text = "This document contains macros. Enable content to view."

        vbproj = doc.VBProject
        module = vbproj.VBComponents.Add(1)
        module.CodeModule.AddFromString(macro_code)

        doc.SaveAs(output_path, FileFormat=13)
        doc.Close(False)
        word.Quit()
else:
    def create_docm(*args, **kwargs):
        raise NotImplementedError("DOCM generation is only supported on Windows.")

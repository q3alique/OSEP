#!/usr/bin/env python3
import os
import zipfile
import shutil
import olefile
import io
import struct
import argparse
import random
import traceback
import sys
from rich.console import Console
from rich.panel import Panel
from rich.table import Table

console = Console()

BANNER = r"""
[bold yellow]  ██╗   ██╗██████╗  █████╗     ███████╗████████╗ ██████╗ ███╗   ███╗██████╗ ███████╗██████╗ [/bold yellow]
[bold yellow]  ██║   ██║██╔══██╗██╔══██╗    ██╔════╝╚══██╔══╝██╔═══██╗████╗ ████║██╔══██╗██╔════╝██╔══██╗[/bold yellow]
[bold yellow]  ██║   ██║██████╔╝███████║    ███████╗   ██║   ██║   ██║██╔████╔██║██████╔╝█████╗  ██████╔╝[/bold yellow]
[bold yellow]  ╚██╗ ██╔╝██╔══██╗██╔══██║    ╚════██║   ██║   ██║   ██║██║╚██╔╝██║██╔═══╝ ██╔══╝  ██╔══██╗[/bold yellow]
[bold yellow]   ╚████╔╝ ██████╔╝██║  ██║    ███████║   ██║   ╚██████╔╝██║ ╚═╝ ██║██║     ███████╗██║  ██║[/bold yellow]
[bold yellow]    ╚═══╝  ╚═════╝ ╚═╝  ╚═╝    ╚══════╝   ╚═╝    ╚═════╝ ╚═╝     ╚═╝╚═╝     ╚══════╝╚═╝  ╚═╝[/bold yellow]
[bold cyan]                                  --- OSEP VBA STOMPER ---[/bold cyan]
[bold black]                            Developed by: q3alique | Version: 1.0[/bold black]
"""

# --- MS-OVBA COMPRESSION/DECOMPRESSION ---
# Reference: [MS-OVBA]: Office VBA File Format Structure
# Section 2.4.1 VBA Compression Algorithm

def decompress_ovba(container):
    """
    Decompresses data using the MS-OVBA algorithm.
    """
    if not container or container[0] != 0x01:
        return None
    
    out = bytearray()
    i = 1
    while i < len(container):
        if i + 2 > len(container):
            break
        
        chunk_header = struct.unpack("<H", container[i:i+2])[0]
        i += 2
        
        # 2.4.1.1.5 CompressedChunkHeader
        # Size is (Header & 0x0FFF) + 3
        # Flag is (Header & 0x8000) >> 15 (1 for compressed, 0 for raw)
        size = (chunk_header & 0x0FFF) + 3
        is_compressed = (chunk_header & 0x8000) != 0
        
        if i + size - 2 > len(container):
            size = len(container) - i + 2
            
        chunk_data_len = size - 2
        chunk_data = container[i:i+chunk_data_len]
        i += chunk_data_len
        
        if not is_compressed:
            out.extend(chunk_data)
        else:
            j = 0
            while j < len(chunk_data):
                flag_byte = chunk_data[j]
                j += 1
                for bit in range(8):
                    if j >= len(chunk_data):
                        break
                    
                    if not (flag_byte & (1 << bit)):
                        # Literal Token
                        out.append(chunk_data[j])
                        j += 1
                    else:
                        # Copy Token
                        if j + 2 > len(chunk_data):
                            break
                        copy_token = struct.unpack("<H", chunk_data[j:j+2])[0]
                        j += 2
                        
                        difference = len(out)
                        n = 0
                        while (1 << (4 + n)) < difference:
                            n += 1
                        if n > 8: n = 8
                        
                        bit_count = 4 + n
                        length_mask = 0xFFFF >> bit_count
                        offset_mask = ~length_mask & 0xFFFF
                        
                        length = (copy_token & length_mask) + 3
                        offset = ((copy_token & offset_mask) >> (16 - bit_count)) + 1
                        
                        for _ in range(length):
                            out.append(out[-offset])
    return bytes(out)

def compress_ovba(data):
    """
    Compresses data using a simple MS-OVBA implementation (mostly literals).
    """
    res = bytearray([0x01]) # SignatureByte
    
    i = 0
    while i < len(data):
        chunk_data = data[i:i+4096]
        i += 4096
        
        chunk_out = bytearray()
        j = 0
        while j < len(chunk_data):
            # Flag byte for 8 tokens
            flag_byte = 0 # All literals
            tokens = chunk_data[j:j+8]
            j += 8
            
            chunk_out.append(flag_byte)
            chunk_out.extend(tokens)
        
        # header = 0xB000 | size_field
        header = 0xB000 | (len(chunk_out) + 2 - 3)
        res.extend(struct.pack("<H", header))
        res.extend(chunk_out)
        
    return bytes(res)

# --- DIR STREAM PARSING ---

def parse_dir_stream(data):
    """
    Parses the decompressed dir stream to find module names and offsets.
    """
    modules = []
    i = 0
    current_module = {}
    
    while i < len(data):
        if i + 6 > len(data): break
        tag = struct.unpack("<H", data[i:i+2])[0]
        size = struct.unpack("<I", data[i+2:i+6])[0]
        i += 6
        
        if tag == 0x0009: size = 6
        elif tag == 0x0003: size = 2
            
        content = data[i:i+size]
        
        if tag == 0x0019: # MODULESTREAMNAME
            current_module['name'] = content.decode('utf-8', errors='ignore')
        elif tag == 0x0031: # MODULEOFFSET
            current_module['offset'] = struct.unpack("<I", content)[0]
            modules.append(current_module)
            current_module = {}
            
        i += size
    return modules

def stomp_vba_project(vba_project_bin_path):
    """
    Stomps a vbaProject.bin file.
    """
    if not os.path.exists(vba_project_bin_path):
        return False, f"File {vba_project_bin_path} not found.", []

    stomp_details = []
    try:
        with olefile.OleFileIO(vba_project_bin_path, write_mode=True) as ole:
            vba_storage = None
            for root in ['', 'Macros', '_VBA_PROJECT_CUR']:
                dir_path = f"{root}/VBA/dir" if root else "VBA/dir"
                if ole.exists(dir_path):
                    vba_storage = root + "/VBA" if root else "VBA"
                    break
            
            if not vba_storage:
                return False, "VBA storage not found.", []
            
            dir_path = f"{vba_storage}/dir"
            dir_compressed = ole.openstream(dir_path).read()
            dir_decompressed = decompress_ovba(dir_compressed)
            if not dir_decompressed:
                return False, "Failed to decompress dir stream.", []
            
            modules = parse_dir_stream(dir_decompressed)
            
            for mod in modules:
                name = mod.get('name', 'Unknown')
                offset = mod.get('offset', 0)
                
                stream_path = f'{vba_storage}/{name}'
                if not ole.exists(stream_path):
                    continue
                
                module_data = ole.openstream(stream_path).read()
                
                realistic_stubs = [
                    f"Public Sub {name}()\r\n    ' Update document properties\r\nEnd Sub\r\n",
                    f"Sub {name}()\r\n    ' Internal processing logic\r\n    Dim x As Integer\r\n    x = 1\r\nEnd Sub\r\n",
                    f"Private Sub {name}()\r\n    ' Initialize component\r\nEnd Sub\r\n"
                ]
                fake_code = random.choice(realistic_stubs).encode('utf-8')
                compressed_fake = compress_ovba(fake_code)
                
                new_module_data = module_data[:offset] + compressed_fake
                
                if len(new_module_data) < len(module_data):
                    new_module_data += b'\x00' * (len(module_data) - len(new_module_data))
                elif len(new_module_data) > len(module_data):
                    new_module_data = new_module_data[:len(module_data)]

                ole.write_stream(stream_path, new_module_data)
                
                stomp_details.append({"module": name, "replacement_size": len(compressed_fake)})
                    
        return True, "VBA Stomping: Source code successfully decoupled from P-Code.", stomp_details
    except Exception as e:
        return False, f"Stomping error: {str(e)}", []

def apply_stomping(doc_path):
    """
    Applies VBA stomping to a document.
    """
    # 1. Check if it's a legacy OLE file (.doc, .xls)
    # Some legacy files might contain ZIP metadata at the end, causing zipfile.is_zipfile to be True.
    # We prioritize OLE detection.
    if olefile.isOleFile(doc_path):
        return stomp_vba_project(doc_path)
        
    # 2. Check if it's an OpenXML ZIP file (.docm, .xlsm)
    if zipfile.is_zipfile(doc_path):
        temp_dir = doc_path + "_temp_stomp"
        if os.path.exists(temp_dir):
            shutil.rmtree(temp_dir)
        os.makedirs(temp_dir)
            
        try:
            vba_internal_path = None
            with zipfile.ZipFile(doc_path, 'r') as zip_ref:
                for member in zip_ref.namelist():
                    norm_name = member.replace('\\', '/')
                    if norm_name.lower() in ['word/vbaproject.bin', 'xl/vbaproject.bin']:
                        vba_internal_path = member
                    
                    target_path = os.path.join(temp_dir, norm_name)
                    os.makedirs(os.path.dirname(target_path), exist_ok=True)
                    
                    if not member.endswith(('/', '\\')):
                        with zip_ref.open(member) as source, open(target_path, "wb") as target:
                            shutil.copyfileobj(source, target)
                
            if not vba_internal_path:
                shutil.rmtree(temp_dir)
                return False, "vbaProject.bin not found in document.", []
                
            vba_fs_path = os.path.join(temp_dir, vba_internal_path)
            success, msg, details = stomp_vba_project(vba_fs_path)
            if not success:
                shutil.rmtree(temp_dir)
                return False, msg, []
                
            os.remove(doc_path)
            with zipfile.ZipFile(doc_path, 'w', zipfile.ZIP_DEFLATED) as zip_out:
                for root, dirs, files in os.walk(temp_dir):
                    for file in files:
                        full_path = os.path.join(root, file)
                        rel_path = os.path.relpath(full_path, temp_dir)
                        zip_out.write(full_path, rel_path.replace(os.sep, '/'))
                        
            shutil.rmtree(temp_dir)
            return True, "VBA Stomping successful.", details
        except Exception as e:
            if os.path.exists(temp_dir):
                shutil.rmtree(temp_dir)
            return False, f"Error during stomping process: {str(e)}", []
            
    return False, "Unsupported file format or not a valid Office document.", []

def main():
    console.print(BANNER)
    parser = argparse.ArgumentParser(description="VbaStomper - VBA Stomping Tool", add_help=False)
    parser.add_argument("file", help="Path to the .doc, .docm, .xls, or .xlsm file")
    parser.add_argument("-h", "--help", action="store_true", help="Show help")
    
    args = parser.parse_args()
    
    if args.help or not args.file:
        table = Table(show_header=False, box=None, padding=(0, 2))
        table.add_column("Option", style="bold yellow", width=25)
        table.add_column("Description", style="white")
        table.add_row("file", "Path to the document to stomp (.doc, .docm, etc.)")
        table.add_row("-h, --help", "Show this help message and exit")
        console.print(table)
        sys.exit(0)

    if not os.path.exists(args.file):
        console.print(f"[bold red][-] Error: File '{args.file}' not found.[/bold red]")
        sys.exit(1)

    console.print(f"[bold blue][*] Applying VBA Stomping to: [white]{args.file}[/white][/bold blue]")
    
    success, msg, details = apply_stomping(args.file)
    
    if success:
        console.print(f"[bold green][+] {msg}[/bold green]")
        if details:
            table = Table(title="Stomped Modules")
            table.add_column("Module Name", style="cyan")
            table.add_column("Replacement Size", style="magenta")
            for det in details:
                table.add_row(det['module'], f"{det['replacement_size']} bytes")
            console.print(table)
        
        console.print(Panel(
            "VBA Stomping successful. The document's source code has been replaced with benign stubs, "
            "while the compiled P-Code remains. This will bypass static analysis that only looks at source code.",
            title="Success", border_style="green"
        ))
    else:
        console.print(f"[bold red][-] Stomping failed: {msg}[/bold red]")
        sys.exit(1)

if __name__ == "__main__":
    main()

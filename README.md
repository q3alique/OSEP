# OSEP - Offensive Security Experienced Penetration Tester Arsenal

This repository contains a collection of tools and scripts developed for the OSEP certification. These tools cover various aspects of advanced penetration testing, including evasion, post-exploitation, and payload generation.

## Tools Included

### Helpers
A collection of utility scripts for enumeration, credential dumping, and environment preparation.
- **AppLocker-Enum.ps1**: Enumerates writable directories allowed by AppLocker.
- **Credential Dumping**: Scripts for SAM, LSA, and Browser credentials.
- **AVDisarm**: Advanced techniques for bypassing AMSI, ETW, and disabling Defender/Firewall.
- **InstallUtilBypass**: C# templates for bypassing application whitelisting using InstallUtil.exe.

### JscriptGen
A generator for JScript, HTA, and XSL payloads. It utilizes DotNetToJScript to wrap C# assemblies or shellcode into script-based formats suitable for initial access.

### MacroGen
A comprehensive VBA macro generator for Microsoft Office documents. Supports various execution methods including WMI, PowerShell, WinAPI, and stealthy shellcode injection.

### PathMaster
A unified post-exploitation tool for both Windows and Linux. It focuses on identifying attack paths, discovering sensitive configuration files, and extracting credentials from various services such as mRemoteNG and WinSCP.

### PayloadCompiler
An automated C# compiler designed for evasion. Supports Mono and .NET Core compilation, XOR-based shellcode encryption, and UPX packing.

### PayloadGen (Project Genesis)
A multi-stage payload infrastructure generator. It creates C# source code for advanced techniques like Process Hollowing, Injection, and Early Bird injection.

### SimpleShell
A versatile reverse shell generator with support for multiple languages including Bash, Python, Perl, and PHP across different operating systems.

### VbaStomper
A specialized tool for VBA stomping, allowing the modification of VBA source code in Office documents while keeping the compiled P-Code intact to evade detection.

### WebGen
A generator for web-based payloads such as ASPX, JSP, and PHP, including reverse shells and interactive web shells.

## Usage

Each tool is located in its own directory with a detailed README.md explaining its specific usage and options.

## Disclaimer

These tools are for educational and authorized testing purposes only. Use them responsibly and only on systems you have permission to test.

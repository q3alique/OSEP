# PathMaster

A unified post-exploitation tool for identifying attack paths, discovering sensitive files, and extracting credentials from various services and configurations. This tool is designed to work across both Windows (PowerShell) and Linux (Bash) environments, providing a consistent analysis workflow during OSEP-level engagements.

## Features
- **Sensitive File Discovery**: Searches for configuration files, credentials, and artifacts from common services like mRemoteNG, WinSCP, FileZilla, and Putty.
- **Deep Secret Parsing**: Uses regex-based parsing to extract passwords, database connection strings, and other secrets from identified files.
- **Service Analysis**: Identifies service-related lateral movement opportunities.
- **Platform Agnostic**: Provides a PowerShell standalone script for Windows and a Bash script for Linux.

## Modules
- **PathMaster_Standalone.ps1**: The primary Windows analysis script.
- **PathMaster_Standalone.sh**: The primary Linux analysis script.
- **PathMaster_Module_AD_Audit.ps1**: Analyzes Active Directory configurations for common misconfigurations.
- **PathMaster_Module_AD_DACL.ps1**: Evaluates Domain Object Control Access Lists.
- **PathMaster_Module_Network.ps1**: Gathers detailed network configuration and connectivity information.
- **PathMaster_Module_Privs_Expert.ps1**: Identifies privilege escalation opportunities based on token privileges and system settings.
- **PathMaster_Module_Secrets.ps1**: Dedicated module for deep credential searching and decryption.

## Usage
Running on a Windows host:
```powershell
. .\PathMaster_Standalone.ps1
```

Running on a Linux host:
```bash
./PathMaster_Standalone.sh
```

### Options
The standalone scripts are designed for automated execution, but individual modules can be imported and executed for more targeted analysis.

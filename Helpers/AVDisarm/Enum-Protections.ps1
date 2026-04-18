<#
.SYNOPSIS
    OSEP Comprehensive Protection Enumerator
    Part of the AVDisarm Arsenal.
    Works at Medium Integrity.
#>

function Write-Header($text) {
    Write-Host "`n[###] $text [###]" -ForegroundColor Cyan
}

function Write-Info($text) {
    Write-Host "[*] $text" -ForegroundColor Gray
}

function Write-Warning($text) {
    Write-Host "[!] $text" -ForegroundColor Yellow
}

function Write-Success($text) {
    Write-Host "[+] $text" -ForegroundColor Green
}

Write-Header "ENUMERATING HOST PROTECTIONS"

# 1. Check Antivirus Status
Write-Info "Checking Antivirus Status..."
try {
    $avProducts = Get-WmiObject -Namespace "root\SecurityCenter2" -Class "AntiVirusProduct" -ErrorAction SilentlyContinue
    if ($avProducts) {
        foreach ($av in $avProducts) {
            $state = $av.productState
            # Decode WMI state (Basic check for 'Enabled')
            if ($state -match "262144" -or $state -match "397312" -or $state -match "397568") {
                Write-Success "Found: $($av.displayName) (Status: ENABLED)"
            } else {
                Write-Warning "Found: $($av.displayName) (Status: Likely Disabled or Mixed)"
            }
        }
    } else {
        Write-Warning "No 3rd party AV found via WMI. Checking Windows Defender..."
    }
} catch {
    Write-Warning "Failed to query CenterCenter2 (Standard on Servers)."
}

# 2. Windows Defender Specifics (Best with High Integrity, but we try)
if (Get-Command Get-MpComputerStatus -ErrorAction SilentlyContinue) {
    $defStatus = Get-MpComputerStatus -ErrorAction SilentlyContinue
    if ($defStatus) {
        Write-Info "Defender Details:"
        Write-Host "    - Real-time Protection: $($defStatus.RealTimeProtectionEnabled)"
        Write-Host "    - Cloud-based Protection: $($defStatus.IsCloudProtectionEnabled)"
        Write-Host "    - Behavior Monitor: $($defStatus.BehaviorMonitorEnabled)"
        Write-Host "    - IOAV Protection: $($defStatus.IOAVProtectionEnabled)"
    }
}

# 3. Firewall Status
Write-Header "FIREWALL CONFIGURATION"
try {
    $profiles = Get-NetFirewallProfile -ErrorAction SilentlyContinue
    if ($profiles) {
        foreach ($p in $profiles) {
            if ($p.Enabled -eq "True") {
                Write-Warning "Profile $($p.Name) is ENABLED"
            } else {
                Write-Success "Profile $($p.Name) is DISABLED"
            }
        }
    } else {
        # Fallback to netsh if cmdlets missing
        netsh advfirewall show allprofiles | Select-String "State"
    }
} catch { Write-Warning "Could not query firewall status." }

# 4. PowerShell Environment (AMSI/CLM)
Write-Header "POWERSHELL ENVIRONMENT"
$clm = $ExecutionContext.SessionState.LanguageMode
if ($clm -eq "ConstrainedLanguage") {
    Write-Warning "Language Mode: CONSTRAINED"
} else {
    Write-Success "Language Mode: $clm"
}

# 5. Kernel & Boot Protections
Write-Header "KERNEL & BOOT PROTECTIONS"
try {
    $vbs = Get-CimInstance -ClassName Win32_DeviceGuard -Namespace root\Microsoft\Windows\DeviceGuard -ErrorAction SilentlyContinue
    if ($vbs) {
        Write-Info "VBS Status: $($vbs.VirtualizationBasedSecurityStatus)"
        if ($vbs.RequiredSecurityProperties -contains 1) { Write-Warning "HVCI (Hypervisor-Enforced Code Integrity) is REQUIRED" }
        if ($vbs.SecurityServicesRunning -contains 1) { Write-Warning "HVCI is RUNNING" }
    }
} catch { Write-Warning "Could not query DeviceGuard (VBS/HVCI)." }

# 6. Check for Known EDR/AV Processes
Write-Header "SENSITIVE PROCESS SCAN"
$edrList = @(
    "MsMpEng", "MsSense", "SenseIR", "cb.exe", "CylanceSvc", "SentinelAgent", "WinDefend",
    "elastic-agent", "elastic-endpoint", "tanclient", "xagt", "traps", "pccntmon", "McAfee"
)
$procs = Get-Process -ErrorAction SilentlyContinue
$found = $false
foreach ($e in $edrList) {
    if ($procs.Name -like "*$e*") {
        Write-Warning "Detected running security process: $e"
        $found = $true
    }
}
if (-not $found) { Write-Success "No common EDR/AV process names detected." }

Write-Header "ENUMERATION COMPLETE"

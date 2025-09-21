# Lookup-Proc.ps1
#Requires -Version 5.1
param(
    [Parameter(Mandatory)][string]$ModuleName,
    [Parameter(Mandatory)][string]$FunctionName,
    [switch]$AsHex
)

function Lookup-Proc {
    param(
        [Parameter(Mandatory)][string]$ModuleName,
        [Parameter(Mandatory)][string]$FunctionName
    )

    # Grab the UnsafeNativeMethods type from System.dll in the GAC
    $unsafeType = (
        [AppDomain]::CurrentDomain.GetAssemblies() |
            Where-Object { $_.GlobalAssemblyCache -and $_.Location.Split('\')[-1] -eq 'System.dll' }
    ).GetType('Microsoft.Win32.UnsafeNativeMethods')

    if (-not $unsafeType) {
        throw "Unable to locate Microsoft.Win32.UnsafeNativeMethods in System.dll"
    }

    $flags = [System.Reflection.BindingFlags] 'Public, NonPublic, Static'
    $allMethods = $unsafeType.GetMethods($flags)

    # Select the specific overloads we need
    $getModuleHandle = $allMethods |
        Where-Object {
            $_.Name -eq 'GetModuleHandle' -and
            $_.GetParameters().Count -eq 1 -and
            $_.GetParameters()[0].ParameterType -eq [string]
        } |
        Select-Object -First 1

    if (-not $getModuleHandle) {
        throw "GetModuleHandle overload (string) not found."
    }

    $getProcAddress = $allMethods |
        Where-Object {
            $_.Name -eq 'GetProcAddress' -and
            $_.GetParameters().Count -eq 2 -and
            $_.GetParameters()[0].ParameterType -eq [IntPtr] -and
            $_.GetParameters()[1].ParameterType -eq [string]
        } |
        Select-Object -First 1

    if (-not $getProcAddress) {
        throw "GetProcAddress overload (IntPtr, string) not found."
    }

    # Call GetModuleHandle to get the base, then GetProcAddress for the symbol
    $hModule = $getModuleHandle.Invoke($null, @($ModuleName))
    if ($hModule -eq [IntPtr]::Zero) {
        throw "Module '$ModuleName' not loaded (GetModuleHandle returned NULL)."
    }

    $ptr = $getProcAddress.Invoke($null, @($hModule, $FunctionName))
    return $ptr
}

try {
    $ptr = Lookup-Proc -ModuleName $ModuleName -FunctionName $FunctionName

    if ($AsHex) {
        # Normalize to 64-bit hex width for readability
        $val = $ptr.ToInt64()
        "{0}" -f ('0x{0:X16}' -f $val)
    } else {
        # Default: show IntPtr plus convenience decimal/hex
        $val = $ptr.ToInt64()
        [PSCustomObject]@{
            Function    = $FunctionName
            Module      = $ModuleName
            IntPtr      = $ptr
            Decimal     = $val
            Hex         = ('0x{0:X16}' -f $val)
        }
    }
}
catch {
    Write-Error $_.Exception.Message
    exit 1
}

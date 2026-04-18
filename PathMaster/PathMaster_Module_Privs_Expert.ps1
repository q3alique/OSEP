<# PathMaster Module: Privs & Expert Paths #>
Write-Host "=== PRIVILEGES & EXPERT PATHS ===" -ForegroundColor Cyan
# Privs
whoami /priv /fo csv | ConvertFrom-Csv | Where-Object { $_.PrivilegeName -match "SeImpersonate|SeAssignPrimary|SeBackup|SeRestore" } | ForEach-Object { Write-Host "[!] PRIVILEGE: $($_.PrivilegeName)" -ForegroundColor Red }
# CLM
Write-Host "[*] Language Mode: $($ExecutionContext.SessionState.LanguageMode)" -ForegroundColor White
# ADCS
try {
    $ConfigDN = ([ADSI]"LDAP://RootDSE").Get("configurationNamingContext")
    $S = New-Object System.DirectoryServices.DirectorySearcher([ADSI]"LDAP://CN=Public Key Services,CN=Services,$ConfigDN")
    $S.Filter = "(objectClass=pKIEnrollmentService)"
    $S.FindAll() | ForEach-Object { Write-Host "[!] ADCS CA Found: $($_.GetDirectoryEntry().name)" -ForegroundColor Red }
    $S.Filter = "(objectClass=pKICertificateTemplate)"
    $S.FindAll() | ForEach-Object {
        $E = $_.GetDirectoryEntry()
        if ($E.Contains("mspki-certificate-name-flag") -and ([int]$E."mspki-certificate-name-flag"[0] -band 0x1)) {
            Write-Host "    [!] ESC1 TEMPLATE: $($E.name) (Enrollee Supplies SAN)" -ForegroundColor Red
        }
    }
} catch {}

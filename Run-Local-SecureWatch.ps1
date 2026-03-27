<#
.SYNOPSIS
    Runs the SecureWatch Agent locally.
.DESCRIPTION
    Runs the agent against the local workspace to check for secrets and git hygiene issues before committing or pushing.
#>

$ScriptPath = Split-Path -Parent $MyInvocation.MyCommand.Definition
Set-Location $ScriptPath

Write-Host "============================" -ForegroundColor Cyan
Write-Host "  SecureWatch Local Scan    " -ForegroundColor Cyan
Write-Host "============================" -ForegroundColor Cyan
Write-Host ""

Write-Host "[1/2] Auditing Git Hygiene (checking tracked files and .gitignore)" -ForegroundColor Yellow
python agents\security-agent\scripts\audit_git.py .
if ($LASTEXITCODE -ne 0) {
    Write-Host ">>> Git Hygiene Failed! Fix the above issues. <<<" -ForegroundColor Red
} else {
    Write-Host ">>> Git Hygiene Passed. <<<" -ForegroundColor Green
}

Write-Host ""
Write-Host "[2/2] Scanning entire workspace for leaked secrets (.txt, .py, etc.)" -ForegroundColor Yellow
python agents\security-agent\scripts\scan_secrets.py .
if ($LASTEXITCODE -ne 0) {
    Write-Host ">>> Secrets Found! Please remove them and replace with os.environ.get() variables. <<<" -ForegroundColor Red
} else {
    Write-Host ">>> No Leaked Secrets Found. <<<" -ForegroundColor Green
}

Write-Host ""
Write-Host "Press any key to exit..."
$Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown") | Out-Null

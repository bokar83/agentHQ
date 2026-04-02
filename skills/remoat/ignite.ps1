Write-Host " "
Write-Host "AntiGravity Ignition Starting..." -ForegroundColor Cyan

Write-Host "Step 1: Opening AntiGravity IDE..." -ForegroundColor Gray
remoat open

Start-Sleep -Seconds 3

# Load environment variables from .env to ensure the latest token is present
$envFile = Join-Path (Get-Location) ".env"
if (Test-Path $envFile) {
    Get-Content $envFile | ForEach-Object {
        if ($_ -match "^\s*([^#=]+)\s*=\s*(.*)\s*$") {
            $key = $matches[1].Trim()
            $value = $matches[2].Trim()
            [Environment]::SetEnvironmentVariable($key, $value, "Process")
        }
    }
}

Write-Host "Step 2: Connecting @CatalystWorksRemoat_bot..." -ForegroundColor Cyan
# Bridging custom .env names and injecting directly into the new process for safety
$botToken = $env:REMOAT_TELEGRAM_BOT_TOKEN
$allowedIds = $env:REMOAT_ALLOWED_USER_IDS
$baseDir = $env:WORKSPACE_BASE_DIR

$cmd = "`$env:TELEGRAM_BOT_TOKEN = '$botToken'; `$env:ALLOWED_USER_IDS = '$allowedIds'; `$env:WORKSPACE_BASE_DIR = '$baseDir'; remoat start"
Start-Process powershell -ArgumentList "-NoExit", "-Command", "$cmd" -WindowStyle Minimized

Write-Host "Ignition Successful!" -ForegroundColor Green
Write-Host "You can now control AntiGravity from your Telegram phone app." -ForegroundColor Gray

Write-Host " "
Write-Host "AntiGravity Ignition Starting..." -ForegroundColor Cyan

Write-Host "Step 1: Opening AntiGravity IDE..." -ForegroundColor Gray
remoat open

Start-Sleep -Seconds 3

Write-Host "Step 2: Connecting @CatalystWorksRemoat_bot..." -ForegroundColor Cyan
# Bridging custom .env names to what Remoat CLI expects
$env:TELEGRAM_BOT_TOKEN = $env:REMOAT_TELEGRAM_BOT_TOKEN
$env:ALLOWED_USER_IDS = $env:REMOAT_ALLOWED_USER_IDS
Start-Process powershell -ArgumentList "-NoExit", "-Command", "remoat start" -WindowStyle Minimized

Write-Host "Ignition Successful!" -ForegroundColor Green
Write-Host "You can now control AntiGravity from your Telegram phone app." -ForegroundColor Gray

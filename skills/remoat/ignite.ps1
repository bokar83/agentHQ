Write-Host " "
Write-Host "🚀 AntiGravity Ignition Starting..." -ForegroundColor Cyan

# 1. Start AntiGravity with Remote Debugging (CDP 9222 default)
Write-Host "📡 Step 1: Opening AntiGravity IDE..." -ForegroundColor Gray
remoat open

# 2. Give the IDE a moment to bind the port
Write-Host "⏳ Step 2: Waiting for CDP port binding..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# 3. Start the Telegram Bot bridge in a background PowerShell window
Write-Host "🤖 Step 3: Connecting @CatalystWorksRemoat_bot..." -ForegroundColor Cyan
Start-Process powershell -ArgumentList "-NoExit", "-Command", "remoat start" -WindowStyle Minimized

Write-Host " "
Write-Host "✅ Ignition Successful!" -ForegroundColor Green
Write-Host "You can now control AntiGravity from your Telegram phone app." -ForegroundColor Gray

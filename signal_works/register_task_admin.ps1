# register_task_admin.ps1
# Run this ONCE from an elevated (Run as Administrator) PowerShell window.
# Creates a Windows Task Scheduler job that runs the Signal Works morning
# pipeline at 07:00 MT every day, even when no user session is open.
#
# Usage (elevated PS):
#   powershell -ExecutionPolicy Bypass -File "D:\Ai_Sandbox\agentsHQ\signal_works\register_task_admin.ps1"

$python   = "D:\Ai_Sandbox\agentsHQ\.venv\Scripts\python.exe"
$script   = "D:\Ai_Sandbox\agentsHQ\signal_works\morning_runner.py"
$workDir  = "D:\Ai_Sandbox\agentsHQ"
$taskName = "SignalWorksMorning"
$logFile  = "D:\Ai_Sandbox\agentsHQ\logs\signal_works_task.log"

$action   = New-ScheduledTaskAction -Execute $python -Argument "`"$script`"" -WorkingDirectory $workDir
$trigger  = New-ScheduledTaskTrigger -Daily -At "07:00AM"
$settings = New-ScheduledTaskSettingsSet `
    -ExecutionTimeLimit  (New-TimeSpan -Minutes 30) `
    -RestartCount        1 `
    -RestartInterval     (New-TimeSpan -Minutes 5) `
    -StartWhenAvailable  `
    -MultipleInstances   IgnoreNew

# SYSTEM account so it runs even when the laptop is locked
$principal = New-ScheduledTaskPrincipal -UserId "SYSTEM" -LogonType ServiceAccount -RunLevel Highest

Register-ScheduledTask `
    -TaskName   $taskName `
    -Action     $action `
    -Trigger    $trigger `
    -Settings   $settings `
    -Principal  $principal `
    -Description "Signal Works: bounce scan + lead harvest + Gmail drafts at 07:00 MT" `
    -Force

Write-Host ""
Write-Host "Task '$taskName' registered. Verify:" -ForegroundColor Green
schtasks /query /tn $taskName /fo list | Select-String "TaskName|Status|Next Run"
Write-Host ""
Write-Host "To test immediately:" -ForegroundColor Yellow
Write-Host "  schtasks /run /tn $taskName"
Write-Host "  Get-Content $logFile -Wait  # stream the log"

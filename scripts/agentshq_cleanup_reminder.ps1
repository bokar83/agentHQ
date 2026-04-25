Add-Type -AssemblyName System.Windows.Forms
Add-Type -AssemblyName System.Drawing

$repoPath = "d:\Ai_Sandbox\agentsHQ"
$logPath = "$repoPath\scripts\.cleanup_reminder.log"
$claudeExe = "C:\Users\HUAWEI\.local\bin\claude.exe"

$body = @"
agentsHQ structure cleanup

You flagged on 2026-04-25 that agentsHQ has duplicate files and folders and needs a structural cleanup pass after Atlas wraps for the day.

Ready to do it now? Yes opens Claude Code in the repo.
"@

$result = [System.Windows.Forms.MessageBox]::Show(
    $body,
    "agentsHQ Reminder",
    [System.Windows.Forms.MessageBoxButtons]::YesNo,
    [System.Windows.Forms.MessageBoxIcon]::Question,
    [System.Windows.Forms.MessageBoxDefaultButton]::Button2
)

if ($result -eq [System.Windows.Forms.DialogResult]::Yes) {
    $kickoffPrompt = "Continue the agentsHQ structure cleanup that was scheduled on 2026-04-25. Goal: find duplicate files and folders, identify structural issues, and propose a simplified layout that works for Boubacar and the agents and tools, without breaking anything. Start by mapping the current top-level structure and flagging duplicates."

    $inner = "Set-Location '$repoPath'; & '$claudeExe' `"$kickoffPrompt`""

    Start-Process -FilePath "wt.exe" -ArgumentList @(
        "-d", $repoPath,
        "powershell.exe", "-NoExit", "-Command", $inner
    )

    "$(Get-Date -Format o) ACCEPTED" | Out-File -FilePath $logPath -Append
} else {
    "$(Get-Date -Format o) DISMISSED" | Out-File -FilePath $logPath -Append
}

exit 0

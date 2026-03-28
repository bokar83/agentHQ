$WshShell = New-Object -comObject WScript.Shell
$Shortcut = $WshShell.CreateShortcut("d:\Ai_Sandbox\agentsHQ\SecureWatch Local Scan.lnk")
$Shortcut.TargetPath = "d:\Ai_Sandbox\agentsHQ\Run-Local-SecureWatch.bat"
$Shortcut.WorkingDirectory = "d:\Ai_Sandbox\agentsHQ"
$Shortcut.IconLocation = "d:\Ai_Sandbox\agentsHQ\ninja.ico"
$Shortcut.Description = "Scan workspace for secrets"
$Shortcut.Save()

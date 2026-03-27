@echo off
:: ============================================================
:: SecureWatch Local Scan Runner
:: Runs Git Hygiene checks and deep secrets scan
:: ============================================================
color 0B
echo ============================
echo   SecureWatch Local Scan
echo ============================
echo.

color 0E
echo [1/2] Auditing Git Hygiene (checking tracked files and .gitignore)
python agents\security-agent\scripts\audit_git.py .
IF %ERRORLEVEL% NEQ 0 (
    color 0C
    echo ^>^>^> Git Hygiene Failed! Fix the above issues. ^<^<^<
) ELSE (
    color 0A
    echo ^>^>^> Git Hygiene Passed. ^<^<^<
)

echo.
color 0E
echo [2/2] Scanning entire workspace for leaked secrets (.txt, .py, etc.)
python agents\security-agent\scripts\scan_secrets.py .
IF %ERRORLEVEL% NEQ 0 (
    color 0C
    echo ^>^>^> Secrets Found! Please remove them and replace with os.environ.get() variables. ^<^<^<
) ELSE (
    color 0A
    echo ^>^>^> No Leaked Secrets Found. ^<^<^<
)

echo.
color 07
pause

@echo off
REM Signal Works Morning Runner
REM Run this at 07:00 MT to top up leads and export draft payloads.
REM Claude Code session then reads draft_payloads.json and creates Gmail drafts.

echo === Signal Works Morning Run %date% %time% ===

cd /d d:\Ai_Sandbox\agentsHQ

REM Step 1: Top up leads to 10 minimum
echo [1/2] Topping up leads...
python -m signal_works.topup_leads --minimum 10 --niches "roofer,pediatric dentist" --city "Salt Lake City"
if %errorlevel% neq 0 (
    echo WARNING: Could not reach 10 email leads. Check output above.
)

REM Step 2: Export draft payloads
echo [2/2] Exporting draft payloads...
python -m signal_works.send_drafts --export --limit 10

echo === Done. Open Claude Code and say: "Create the Signal Works drafts from draft_payloads.json" ===
pause

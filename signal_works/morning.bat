@echo off
REM Signal Works Morning Runner
REM Run at 07:00 MT -- tops up leads across all Utah Wasatch Front cities + 3 niches,
REM then creates Gmail drafts in boubacar@catalystworks.consulting.

echo === Signal Works Morning Run %date% %time% ===
cd /d d:\Ai_Sandbox\agentsHQ

REM Step 0: Scan boubacar@catalystworks.consulting for bounces, null bad emails in DB
echo [0/2] Scanning for bouncebacks...
python -m signal_works.bounce_scanner --days 2

REM Step 1: Top up to 10 email leads (roofer + pediatric dentist + hvac, all Utah cities)
echo [1/3] Topping up leads...
python -m signal_works.topup_leads --minimum 10
if %errorlevel% neq 0 (
    echo WARNING: Could not reach 10 email leads. Check output above. Proceeding anyway.
)

REM Step 2: Create drafts in boubacar@catalystworks.consulting and mark as drafted
echo [2/3] Creating Gmail drafts...
python -m signal_works.send_drafts --run

echo === Done. Check boubacar@catalystworks.consulting Drafts folder. ===
pause

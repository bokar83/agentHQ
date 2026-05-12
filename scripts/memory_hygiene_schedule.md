# Memory Hygiene Agent — Schedule Wiring (Compass C9)

Schedules `scripts/memory_hygiene_agent.py` to run autonomously on the operator workstation. Two options below — pick one. Windows Task Scheduler = default (works on Windows native, no extra deps).

## Option A — Windows Task Scheduler (default)

### One-shot install (PowerShell, admin)

```powershell
$action = New-ScheduledTaskAction -Execute "python.exe" -Argument "D:\Ai_Sandbox\agentsHQ\scripts\memory_hygiene_agent.py" -WorkingDirectory "D:\Ai_Sandbox\agentsHQ"
$trigger = New-ScheduledTaskTrigger -Monthly -DaysOfMonth 1 -At "06:00"
$settings = New-ScheduledTaskSettingsSet -StartWhenAvailable -AllowStartIfOnBatteries -DontStopIfGoingOnBatteries -RunOnlyIfNetworkAvailable
$principal = New-ScheduledTaskPrincipal -UserId "$env:USERNAME" -LogonType Interactive -RunLevel Limited
Register-ScheduledTask -TaskName "agentsHQ_memory_hygiene" -Action $action -Trigger $trigger -Settings $settings -Principal $principal -Description "Compass C9: monthly memory-hygiene agent. Reports into digest + Telegram on exception."
```

### Verify

```powershell
Get-ScheduledTask -TaskName "agentsHQ_memory_hygiene"
Get-ScheduledTaskInfo -TaskName "agentsHQ_memory_hygiene"
```

### Manual run (test)

```powershell
Start-ScheduledTask -TaskName "agentsHQ_memory_hygiene"
# Or run script directly:
python D:\Ai_Sandbox\agentsHQ\scripts\memory_hygiene_agent.py --dry-run
```

### Disable / remove

```powershell
Disable-ScheduledTask -TaskName "agentsHQ_memory_hygiene"
# Or hard-delete:
Unregister-ScheduledTask -TaskName "agentsHQ_memory_hygiene" -Confirm:$false
```

## Option B — WSL cron (fallback if Task Scheduler unavailable)

### Install

```bash
# In WSL Ubuntu
crontab -e
# Add line:
0 6 1 * * cd /mnt/d/Ai_Sandbox/agentsHQ && /usr/bin/python3 scripts/memory_hygiene_agent.py >> /tmp/memory_hygiene.log 2>&1
```

Cron expression: `0 6 1 * *` = 06:00 on day 1 of every month.

## Acceptance check

After install, run dry-run to confirm:

```powershell
python D:\Ai_Sandbox\agentsHQ\scripts\memory_hygiene_agent.py --dry-run
```

Expected output:

```
[memory_hygiene] severity=OK|WARN|BLOCK lines=<N> candidates=<N> cold=<N>
[memory_hygiene] digest written: D:\Ai_Sandbox\agentsHQ\agent_outputs\memory_hygiene\memory_hygiene_<DATE>.md
[memory_hygiene] DRY RUN: would have sent Telegram alert   (only if exception)
```

Digest file persists at `agent_outputs/memory_hygiene/memory_hygiene_<YYYY-MM-DD>.md` for review.

## Telegram exception contract

Sends to `OWNER_TELEGRAM_CHAT_ID` (or `TELEGRAM_CHAT_ID`) via `ORCHESTRATOR_TELEGRAM_BOT_TOKEN` (or `TELEGRAM_BOT_TOKEN`). Reads from `.env` at repo root.

Exception triggers (any one):
- MEMORY.md line count >180 (BLOCK tier)
- Promotion candidates present (≥1 rule fired 3+ times in distinct sessions over last 30 days)

Silent otherwise — digest file only. No noise on quiet months.

## First production run

Next fire = **2026-06-01 06:00 MT** under Option A.

If first-month signal is too noisy (17 candidates surfaced in 2026-05-12 smoke test), tune `PROMOTION_FIRE_THRESHOLD` in script (currently 3). Bump to 5 after monitoring first 2 cycles. Keep cap thresholds (`LINE_CAP_*`) as-is.

## Retirement

C9 retires when:
- Tiered-memory architecture ships (Atlas/Hermes orchestrator-memory milestone covers local Claude Code memory), OR
- agentmemory v1.0 reopen condition fires AND we install it

Remove via `Unregister-ScheduledTask` above.

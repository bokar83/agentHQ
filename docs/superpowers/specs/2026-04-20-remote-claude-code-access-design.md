# Remote Claude Code Access Design

**Date:** 2026-04-20
**Save point:** `savepoint-2026-04-20-pre-remote-claude` (rewind: `git reset --hard savepoint-2026-04-20-pre-remote-claude`)

## Goal

From a Pixel 9 Pro phone, anywhere in the world, land in a live Claude Code session running on the always-on Windows 11 home PC with zero manual startup steps after a reboot. Keep the existing `.\ignite` Antigravity bot untouched and working.

## Non-Goals

- No Telegram bot for Claude Code (existing remoat handles Antigravity, Claude Code is SSH-only).
- No custom bot code, no Claude API key on disk, no separate billing. Use the existing Claude Code subscription auth.
- No public internet exposure of the PC. SSH reachable only inside the Tailscale tailnet.

## Architecture

Three existing tools, composed. Nothing custom.

```
Pixel 9 Pro                            Windows 11 PC (always on)
-----------                            ------------------------
Tailscale (client)    <-- WireGuard --> Tailscale (client)
Termius SSH client    ---- SSH key ---> OpenSSH Server (Windows built-in)
                                        |
                                        v
                                        tmux session "claude" (Git Bash)
                                        |
                                        v
                                        claude (CLI, interactive)
```

### Components

**On the PC:**

| Component | Location | Size | Role |
|---|---|---|---|
| Tailscale | `C:\Program Files\Tailscale\` | ~40 MB | WireGuard VPN. Required on C; Windows service. |
| OpenSSH Server | Windows built-in feature | 0 | SSH daemon. Enabled as Windows optional feature. |
| Git for Windows | Already installed | 0 | Provides `bash.exe` and `tmux` binaries. |
| tmux config | `D:\Ai_Sandbox\agentsHQ\config\tmux.conf` | < 1 KB | Disables mouse mode, sets scrollback. |
| Task Scheduler entry | Windows registry | 0 | One-line command at user login. No external script file. |

**On the phone:**

| Component | Size | Role |
|---|---|---|
| Tailscale app | ~30 MB | Joins tailnet. |
| Termius | ~40 MB | SSH client with saved-snippet support. |

**Nothing on C: beyond Tailscale (~40 MB).** Everything else is D: or phone.

## Auth Model

**Tailscale:** Identity-based via the Boubacar tailnet. Phone and PC both log in once via OAuth. Tailscale SSH server is Linux/Mac only, so it is NOT used as the SSH daemon on Windows. Tailscale here is the encrypted transport only.

**SSH:** Standard keypair. Private key generated on the Pixel 9 Pro (in Termius), public key added to `C:\Users\HUAWEI\.ssh\authorized_keys` on the PC. Password auth disabled in `sshd_config`. Because SSH is only reachable via the tailnet (no port forwarding on the router), the attack surface is: Tailscale account compromise OR physical access to the Pixel's Termius app.

**Claude Code:** Uses existing Windows user-profile auth. No new tokens, no API keys.

**Revocation:**
- Lost phone: revoke the Pixel from Tailscale admin UI. SSH key becomes unreachable.
- Key rotation: generate a new keypair in Termius, replace `authorized_keys` line on PC.

## Boot Flow

```
PC boots -> Windows login
  -> Tailscale service auto-starts (built-in)
  -> OpenSSH Server auto-starts (built-in)
  -> Task Scheduler "RemoteClaudeBoot" fires at login:
       "C:\Program Files\Git\bin\bash.exe" -lc "tmux new-session -d -s claude -c /d/Ai_Sandbox/agentsHQ 'claude'"
     (inline; no .ps1 script)
  -> tmux session "claude" is now running in the background with claude CLI inside it
```

Phone connection flow:

```
Open Termius -> tap "home-pc" connection -> auto-run snippet "tmux attach -t claude"
  -> land inside the live Claude Code session, exactly where it was left
```

## What Happens When Things Go Wrong

| Event | Behavior |
|---|---|
| PC reboots | Tailscale + OpenSSH + Task Scheduler all re-fire at next Windows login. Same state. |
| Windows auto-update reboots overnight | PC sits at lock screen. Task Scheduler does NOT fire until next human login. Recovery: log in once; everything resumes. |
| Claude Code exits (via /exit or crash) | tmux session stays alive. Shell sits empty. Phone user reconnects, types `claude`, done. No auto-restart wrapper (rejected by Sankofa review as hostile UX). |
| Network drops | Tailscale auto-reconnects. tmux session on PC is unaffected. Phone reattaches. |
| Tailscale key expires | Key expiry disabled for the PC node in Tailscale admin (one checkbox, one time). Prevents 90-day silent disconnect. |
| Claude Code updates itself | No impact. tmux hosts whatever `claude` binary is on PATH at launch. Next exit + relaunch picks up the new version. |

## What Was Cut

Original design from brainstorming was pressure-tested by code-reviewer agent + Sankofa Council. These elements were cut for leanness or correctness:

| Cut | Reason |
|---|---|
| Tailscale SSH as auth mechanism | Not supported on Windows (server side). GitHub issue open since 2022. Replaced with standard SSH key. |
| zellij as session multiplexer | Windows support < 1 year old, mobile-SSH attach/detach not widely validated. Replaced with tmux (Git Bash), which has years of proven Windows behavior. |
| Log rotation (daily, 7-day retention) | Script runs once per login. One line per boot. Overhead for theoretical volume that takes years to matter. |
| Service verification step in boot script | Both services auto-start. If they are not running, SSH fails and the check is moot. Speculative robustness. |
| Auto-restart wrapper (`while true; do claude; sleep 2; done`) | Makes `/exit` hostile (respawns instantly, can't detach cleanly). If crash loops become real, add then. |
| Dedicated PowerShell script file (`remote-claude-boot.ps1`) | After the cuts above, the remaining logic fits inline in the Task Scheduler action field. No external file to maintain. |
| Log directory (`D:\Ai_Sandbox\agentsHQ\logs\remote-claude-boot.log`) | Task Scheduler already logs success/failure to Windows Event Viewer. Rebuilding that is waste. |

**Net:** design dropped from 6 files + rotation logic + service checks + restart daemon, down to 1 config file (`tmux.conf`, 3 lines) + 1 Task Scheduler entry.

## Files That Get Created

1. `D:\Ai_Sandbox\agentsHQ\config\tmux.conf` (~3 lines: disable mouse, set scrollback, optional status bar color)

That is it. No scripts, no logs, no Python, no PowerShell files.

## Files That Get Modified

None in the repo.

## Out-of-Repo System Changes (Windows)

These are required but do not touch the codebase. All reversible.

1. **Enable OpenSSH Server** as a Windows optional feature. Set service startup to Automatic.
2. **Add Pixel public key** to `C:\Users\HUAWEI\.ssh\authorized_keys`.
3. **Disable password auth** in `C:\ProgramData\ssh\sshd_config` (ensures only key-based auth works).
4. **Install Tailscale** from tailscale.com. Log in on PC.
5. **In Tailscale admin:** disable key expiry for the PC node.
6. **Install Tailscale + Termius** on the Pixel. Log into Tailscale (same account).
7. **Generate SSH key on Pixel in Termius**, copy public key to PC `authorized_keys`.
8. **Create Task Scheduler entry "RemoteClaudeBoot"** with trigger "At log on of HUAWEI user", action = the one-line bash command from the boot flow section.
9. **Save a Termius snippet** "attach claude" that runs `tmux attach -t claude` on connect.

## Rewind Path

If any step breaks something unexpectedly:

```
git reset --hard savepoint-2026-04-20-pre-remote-claude
```

For the Windows system changes (not in git), each is independently reversible:
- Task Scheduler entry: delete via `taskschd.msc`
- Tailscale: uninstall from Programs and Features
- OpenSSH Server: disable via Windows optional features
- `authorized_keys` and `sshd_config` edits: restore from backup copies taken before editing

## Success Criteria

1. After a PC reboot with no human action except logging into Windows, `tmux attach -t claude` from the Pixel's Termius lands in a live Claude Code prompt at `D:\Ai_Sandbox\agentsHQ`.
2. Closing Termius and reopening it 24 hours later reattaches to the same session with conversation history intact.
3. Typing `/exit` in Claude Code drops to an empty shell inside tmux. Typing `claude` again relaunches. tmux session survives both.
4. Running `.\ignite` in a separate PowerShell on the PC still works (existing Antigravity remoat flow is not affected).
5. Uninstalling Tailscale makes the PC unreachable from the phone (confirms no public exposure).

## Open Questions

None. All decisions locked.

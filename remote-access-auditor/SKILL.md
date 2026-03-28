---
name: remote-access-auditor
description: >
  Performs a full unauthorized remote access audit on a Windows machine using Desktop Commander.
  Use this skill whenever the user asks to: scan for remote access tools, check if anyone is
  accessing their computer, run a security scan, audit running services, check for suspicious
  software, or verify whether their PC is clean. Also trigger automatically when a scheduled
  security check is requested. The skill checks active network connections, running processes,
  installed software, and known remote access tool signatures, then sends email alerts if
  threats are found. Always use this skill for any security scan or remote access check request.
---

# Remote Access Auditor

Perform a full security scan for unauthorized remote access tools on this Windows machine.
Run every scan step, analyze the results, then report findings and send alerts if needed.

## Owner configuration
- **Alert email:** bokar83@gmail.com
- **Alert threshold:** Send email for MEDIUM, HIGH, or CRITICAL severity findings only
- **Email subject format:** ALL CAPS — urgency must be obvious at a glance

---

## Step 1 — Gather system data

Run all four commands. Do not skip any.

**A. Active network connections**
```
netstat -ano
```

**B. Running processes with their Windows service names**
```
tasklist /SVC /FO CSV /NH
```

**C. Installed software with install dates**
```
wmic product get Name,InstallDate,Vendor /FORMAT:CSV
```

**D. Startup folder contents**
```
dir "C:\ProgramData\Microsoft\Windows\Start Menu\Programs\Startup" /B
dir "C:\Users\HUAWEI\AppData\Roaming\Microsoft\Windows\Start Menu\Programs\Startup" /B
```

---

## Step 2 — Analyze for threats

Cross-reference findings against the threat catalog below. For each finding, assign one of:
- 🔴 **CRITICAL** — Active remote control tool with live external connection
- 🟠 **HIGH** — Remote access service running or installed without known authorization
- 🟡 **MEDIUM** — Suspicious open port or unusual outbound connection
- 🟢 **LOW** — Informational, no immediate action needed
- ✅ **CLEAN** — Nothing suspicious found in this category

### Known remote access tool signatures (processes / service names)

**Screen sharing & remote control**
- `ScreenConnect*`, `connectwise*` → ConnectWise Control (formerly ScreenConnect)
- `AnyDesk*`, `anydesk*`
- `TeamViewer*`, `tv_*`
- `*vnc*.exe`, `winvnc*`, `vncviewer*`, `uvnc*`, `tightvnc*`, `realvnc*`
- `Splashtop*`, `strwinclt*`
- `*GoTo*`, `g2assist*`, `g2host*`
- `LogMeIn*`, `LMI*`
- `RemotePC*`
- `Radmin*`
- `DameWare*`
- `RustDesk*`, `rustdesk*`
- `Supremo*`
- `UltraViewer*`

**RMM (Remote Monitoring & Management) platforms**
- `AEMAgent*`, `ATTray*`, `RMM.WebRemote*` → Atera RMM
- `LTSvc*`, `LTSERVICE*`, `launchagent*` → ConnectWise Automate (LabTech)
- `Kaseya*`, `KaseyaAgent*`
- `NinjaRMM*`, `NinjaOne*`
- `N-able*`, `nable*`, `SolarWinds*`
- `Datto*`, `autotask*`
- `Naverisk*`
- `Syncro*`
- `Atera*`
- `ManageEngine*`, `DCAgent*`
- `pulseway*`

**Built-in Windows remote access (only flag if unexpected)**
- `TermService` (Remote Desktop / RDP) — flag if running and not expected
- `sshd*` (OpenSSH server) — flag if running

### Suspicious ports to flag
| Port | Protocol | Risk if open externally |
|------|----------|------------------------|
| 3389 | RDP | HIGH — Remote Desktop |
| 5900–5910 | VNC | HIGH — Screen sharing |
| 22 | SSH | MEDIUM–HIGH |
| 8041 | ScreenConnect | CRITICAL if active |
| 4899 | Radmin | HIGH |
| 5938 | TeamViewer | HIGH if unexpected |
| 7070 | AnyDesk | HIGH if unexpected |

### Suspicious network connection patterns
- Any ESTABLISHED connection to a non-Google, non-Microsoft, non-Avast IP on a non-standard port (not 80/443/5228)
- Any process connecting repeatedly to the same external IP on a port above 7000
- Connections on port 80 (unencrypted HTTP) to non-local IPs — data could be exfiltrated unencrypted

### Installed software red flags
- Any remote access tool installed within the **last 30 days** that the user did not knowingly install
- Any tool from vendors: ScreenConnect Software, ConnectWise, AnyDesk GmbH, TeamViewer, Atera Networks, etc.

---

## Step 3 — Build the threat report

Always produce this report, whether clean or not. Use this exact structure:

```
🔒 REMOTE ACCESS SECURITY SCAN
Computer: [hostname]
Scan time: [timestamp]
Overall status: [CLEAN / THREATS FOUND]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
FINDINGS
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━

[For each finding:]
[SEVERITY EMOJI] [SEVERITY LEVEL]: [Tool/process/port name]
  What it is: [plain-language explanation]
  Evidence: [process name, PID, network connection, or install date]
  Action needed: [specific steps the user should take, or "None — already clean"]

━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
SUMMARY
━━━━━━━━━━━━━━━━━━━━━━━━━━━━━━
Critical: [n]  |  High: [n]  |  Medium: [n]  |  Low: [n]
```

---

## Step 4 — Send alerts if threats found

If any MEDIUM, HIGH, or CRITICAL findings exist, do both of the following:

### A. Send email via Gmail

Use the `gmail_create_draft` tool to create a draft, OR if you can send directly, send immediately.

**To:** bokar83@gmail.com
**Subject:** Follow the urgency rules below based on severity:
- CRITICAL finding → `🚨 CRITICAL SECURITY ALERT — UNAUTHORIZED REMOTE ACCESS DETECTED ON YOUR PC`
- HIGH finding → `⚠️ HIGH ALERT — SUSPICIOUS REMOTE ACCESS TOOL FOUND ON YOUR PC`
- MEDIUM only → `SECURITY WARNING — SUSPICIOUS ACTIVITY ON YOUR PC [SCAN DATE]`

**Body:** Paste the full threat report, then add at the bottom:
```
---
Recommended immediate steps:
1. Disconnect from the internet if a CRITICAL tool is actively connected.
2. Uninstall the flagged software via Settings → Apps.
3. Change your passwords from a different device.
4. Reply to this email or run another scan after taking action.

This alert was sent automatically by your Remote Access Auditor skill.
```

### B. Send Windows desktop notification

Use the `mcp__Windows-MCP__Notification` tool:
- **Title:** `🔴 Security Alert — Action Required`
- **Message:** `[N] threat(s) found in security scan. Check your email at bokar83@gmail.com for full details.`

---

## Step 5 — Clean bill of health

If ALL findings are LOW or CLEAN, send a brief Windows notification only (no email):
- **Title:** `✅ Security Scan Complete`
- **Message:** `No remote access threats detected. Your PC looks clean.`

Do NOT send an email when everything is clean — only alert when there's something to act on.

---

## Notes on Desktop Commander command restrictions

These commands are **blocked** on this machine's Desktop Commander config and will fail — do not attempt them:
`reg`, `sc`, `netsh`, `net`, `firewall`, `iptables`, `sfc`, `bcdedit`, `runas`, `takeown`

Stick to: `netstat`, `tasklist`, `wmic`, `schtasks`, `ipconfig`, `dir`, `where`, `taskkill`

# Session Handoff - Absorb Security Scan Gate Shipped - 2026-05-04

## TL;DR
Added Security Scan Gate (v1 + v2, all patterns) to agentshq-absorb skill in a single session. v1: postinstall shell-out + base64/decode-exec. v2: typosquatting (with 80-package reference list), hardcoded exfil IPs, env var harvesting, hardcoded secrets. Acceptance test fixtures written for every pattern (clean + malicious). Compass M6 SHIPPED. All 3 Notion tasks marked Done.

## What was built / changed

- `skills/agentshq-absorb/SKILL.md`   added "Hard rule: security scan before any clone or install" section (before the README rule), Security Scan Gate procedure with v1 pattern checklist (2 patterns), SECURITY SCAN verdict block template, ingestion path trigger table, and 5 new Common Mistakes rows
- `skills/agentshq-absorb/SKILL.md`   dossier template updated to embed SECURITY SCAN block
- `docs/roadmap/compass.md`   new M6 milestone added: "Security Scan Gate v2 patterns"
- Memory: `feedback_absorb_security_scan.md` (new)

## Decisions made

- **v1 launches with 2 patterns only** (postinstall shell-out + base64/decode-exec chain) per Karpathy Simplicity First   most signal, lowest false-positive risk
- **STATIC-CLEAN replaces CLEAN**   Sankofa Outsider: "safe" label creates false confidence; disclaimer always shown
- **Shared primitive framing**   scan applies to all ingestion paths (Dockerfiles, pip, n8n, MCP), not only absorb
- **BLOCKED is hard stop**   no override path; SUSPICIOUS has override with annotation requirement
- **v2 patterns deferred** (typosquatting, env var exfil, commit history, hardcoded IPs, astroturfed repos)   scope to next milestone
- **Roadmap home: compass**   security scan is a governance/enforcement capability, lives in compass not atlas

## What is NOT done (explicit)

- v3 pattern not implemented: astroturfed repo detection (repo < 30 days old + star spike)   requires GitHub API metadata, deferred
- Scan not yet wired to orc_rebuild.sh / Docker path   framed as guidance, not a hook

## Open questions

- Does Boubacar want the scan to gate `orc_rebuild.sh` explicitly? (Currently framed as guidance, not a hook)
- Does Boubacar want v3 astroturfed repo detection? (Requires GitHub API metadata call   small addition)

## Next session must start here

1. Optionally: implement v3 astroturfed repo detection (GitHub API: repo age + star spike)
2. Optionally: wire scan gate as a pre-clone check in `orc_rebuild.sh`
3. No urgent follow-up   all v1 + v2 patterns shipped, fixtures written, Notion tasks Done

## Files changed this session

```
skills/agentshq-absorb/SKILL.md                                        (v1+v2 scan gate, pattern table, Popular Package Reference, fixtures ref)
skills/agentshq-absorb/fixtures/security-scan/README.md                (new   fixture index)
skills/agentshq-absorb/fixtures/security-scan/clean/package.json       (new   STATIC-CLEAN sample)
skills/agentshq-absorb/fixtures/security-scan/clean/requirements.txt   (new)
skills/agentshq-absorb/fixtures/security-scan/clean/main.py            (new)
skills/agentshq-absorb/fixtures/security-scan/malicious/v1-1-postinstall-shellout/package.json  (new   BLOCKED)
skills/agentshq-absorb/fixtures/security-scan/malicious/v1-2-base64-exec/index.js              (new   BLOCKED, documented pattern)
skills/agentshq-absorb/fixtures/security-scan/malicious/v1-2-base64-exec/main.py               (new   BLOCKED)
skills/agentshq-absorb/fixtures/security-scan/malicious/v2-3-typosquat/requirements.txt        (new   SUSPICIOUS)
skills/agentshq-absorb/fixtures/security-scan/malicious/v2-3-typosquat/package.json            (new   SUSPICIOUS)
skills/agentshq-absorb/fixtures/security-scan/malicious/v2-4-exfil-endpoint/exfil.py           (new   SUSPICIOUS)
skills/agentshq-absorb/fixtures/security-scan/malicious/v2-5-env-harvest/harvest.py            (new   SUSPICIOUS)
skills/agentshq-absorb/fixtures/security-scan/malicious/v2-6-hardcoded-secret/config.py        (new   SUSPICIOUS)
docs/roadmap/compass.md                                                 (M6 SHIPPED)
docs/handoff/2026-05-04-absorb-security-scan-shipped.md                (this file, updated)
memory/feedback_absorb_security_scan.md                                 (new)
```

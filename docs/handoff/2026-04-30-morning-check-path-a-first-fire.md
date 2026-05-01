# Handoff: Path A Morning Check (2026-04-30)

**Single goal:** Verify the first scheduled production fire of Path A (transcript-style-dna voice personalizer) at 07:00 MT, then decide on auto-send.

**Repo state at session start:** all 3 locations on commit `6f91181`. Working tree should be clean (a phantom `m output` flag is expected and safe to ignore: nested standalone repo).

---

## RUN THESE COMMANDS (in order)

### 1. Confirm the 07:00 MT run actually fired

``bash
ssh root@agentshq.boubacarbarry.com "tail -100 /var/log/signal_works_morning.log"
``

Look for the most recent run (today's date in the log lines). The summary block at the bottom of a healthy run looks like:

``
==================================================
Run complete:
  Bounces cleared:        N
  SW leads harvested:     N
  SW drafts created:      N
  CW leads personalized:  N      <- this is the new line, MUST be > 0 for KEEP path
  CW outreach drafts:     N
  TOTAL drafts in inbox:  N
==================================================
``

### 2. Count personalized CW leads from the last 24 hours

``bash
ssh root@agentshq.boubacarbarry.com "docker exec orc-crewai bash -c 'cd /app && python -c \"
from db import get_crm_connection
c = get_crm_connection()
cur = c.cursor()
cur.execute(chr(83)+chr(69)+chr(76)+chr(69)+chr(67)+chr(84)+chr(32)+\\\"id, name, company, voice_personalization_line FROM leads WHERE source = '+chr(39)+'apollo_catalyst_works'+chr(39)+' AND voice_personalization_line IS NOT NULL ORDER BY id DESC LIMIT 10\\\"); rows=cur.fetchall(); print(len(rows), chr(108)+chr(101)+chr(97)+chr(100)+chr(115)+chr(58)); [print(r) for r in rows]; c.close()\"'"
``

(Yes the `chr()` quoting is ugly: SSH + docker + python + nested quotes is hell. Just paste it.)

Expected: prints a count and 1-3 sample rows showing real openers. Each opener should be a single sentence ≤25 words referencing something concrete about the prospect or their company.

### 3. Eyeball 2-3 CW drafts in Gmail

Open `boubacar@catalystworks.consulting` Drafts folder. Look at the most recent CW drafts (the ones with `geolisted.co` are SW; the others are CW). Open 2-3 and read the opening. The first line below the greeting should sound like the prospect, not like our template.

---

## DECIDE BASED ON THE OUTPUT

### Outcome A: ≥1 lead personalized AND openers look good

✅ Path A is producing real signal. Lift-test data is accumulating.

**Optional action:** flip auto-send on for tomorrow.

``bash
ssh root@agentshq.boubacarbarry.com "echo 'AUTO_SEND_CW=true' >> /root/agentsHQ/.env && cd /root/agentsHQ && ./scripts/orc_rebuild.sh"
``

Or hold and check again tomorrow morning. Default safe.

### Outcome B: ≥1 lead personalized BUT openers are generic / weird / off-voice

⚠️ Skill is firing but producing low-quality output. NOT a bug, this is signal for the lift test.

**Action:** Note the specific bad openers in `project_style_dna_wirein_state.md` memory (which leads, why they read as bad). Do NOT fix the skill mid-test: this IS the data the lift-test eval needs on 2026-06-01. Hold AUTO_SEND_CW=false until you see if openers improve as more data flows.

### Outcome C: 0 leads personalized OR STEP 4.5 errored

🚨 Production bug. Before debugging, check three things in order:

1. **Did Apollo topup produce CW leads?** Look for `STEP 4: ... Done. N CW email leads ready.` If N=0, no CW leads existed for Step 4.5 to process. That's not a Path A bug, it's an Apollo/topup_cw bug.
2. **Did Step 4.5 fire and skip everything?** Look for `STEP 4.5: Voice-personalize today's CW leads...` followed by `Done. 0 leads personalized.` Then look in the same log for `voice_personalizer: skip lead=...` lines. The `reason=` field tells you why (no_website, thin_text, extract_error, empty_opener). Aggregate the reasons.
3. **Did Step 4.5 error out?** Look for `Voice personalization failed (non-fatal): ...`. The error message identifies the bug.

If outcome C, leave AUTO_SEND_CW=false (it already is). Then debug per the specific reason. Do NOT push fixes to main without re-running the morning_runner manually first to verify the fix.

---

## IF YOU NEED MORE CONTEXT

Read these in order, only as needed:

- **What Path A is + lift-test design:** memory `project_style_dna_wirein_state.md`
- **What shipped yesterday and why:** memory `project_10_10_daily_floor_deployment.md`
- **The eval procedure for 2026-06-01:** `docs/roadmap/harvest.md` R7
- **Why we used BS4 not Firecrawl:** memory `reference_firecrawl_pricing_2026.md`
- **Why orchestrator imports need try/except:** memory `feedback_flattened_container_imports.md`
- **The session that shipped this:** `docs/handoff/2026-04-29-style-dna-wirein-DEPLOYED.md`

---

## ARCHIVE: what landed yesterday (2026-04-29)

Two parallel feature branches merged to main + 1 chmod cleanup. Final tip: `6f91181`.

**Path A wire-in (style-dna-wirein):**
- transcript-style-dna voice personalizer wired into morning_runner Step 4.5
- Personalizer derives company website (Serper), scrapes via BeautifulSoup, calls extract.py for voice fingerprint, writes opener back to leads.voice_personalization_line
- email_builder._opening short-circuits to voice line when populated
- 5 import bugs fixed during deploy (4 flattened-container imports + 1 empty-env-var)
- Smoke-tested live: 4 production leads have personalized openers in DB

**Pipeline scaling (10-10-daily-floor):**
- expansion_ladder.py: 392 niche/city pairs across 6 tiers
- topup_leads.py rewritten with ladder walk + 4-layer email resolution + business_name alias (the prod-blocking fix)
- topup_cw_leads.py: hybrid 5-fresh + 5-resend with Apollo gap-fill
- hunter_client.py: domain-search wrapper with daily cap 5
- Apollo CW_ICP_WIDENED: employees 1-200, +VP seniority, +5 cities, +3 titles
- Production: 16 SW + 6 CW drafts produced live by end of session

**Coordination layer:**
- skills/coordination/proposal: /propose /ack /reject /list-proposals slash flow
- scripts/orc_rebuild.sh: refuses to rebuild if task:morning-runner is held; eliminates parallel-session deploy collisions
- AGENT_SOP hard rule: always use scripts/orc_rebuild.sh

**Operational state at 6f91181:**
- AUTO_SEND_CW=false, AUTO_SEND_SW=false (drafts only)
- systemd timer fires `morning_runner.py` daily at 07:00 MT
- 7-day Telegram health check scheduled for 2026-05-06
- 14-day Telegram health check scheduled for 2026-05-13
- R7 lift-test eval scheduled for 2026-06-01 09:00 MT (Google Calendar)

**Backlog (not blocking, do when convenient):**
- Pre-push hook diff-awareness (currently scans all tracked files, ~3 min/push)
- 11 older VPS stashes review and drop
- 5 unguarded `from orchestrator.X` imports in lower-priority files

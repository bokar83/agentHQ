# Session Handoff - Asset Inventory and Tracker Build - 2026-05-05

## TL;DR

Full multi-surface asset inventory (GitHub, VPS, Notion, local repo) across all of Boubacar's digital properties. Built a new Asset Register database in Forge 2.0 with 54 rows, plus a Weekly Asset Review ritual page and New Asset Rule gate page. Scoped the Hotel Club de Kipe full rebuild and wrote the execution prompt. Session is clean -- no open code changes.

---

## What was built / changed

- `C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\project_asset_inventory_session.md` -- session decisions + Phase 2 artifact URLs
- `C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\feedback_no_delete_archive_instead.md` -- never delete assets rule
- `C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\reference_asset_register_notion.md` -- Asset Register URLs and views to create
- `C:\Users\HUAWEI\.claude\projects\d--Ai-Sandbox-agentsHQ\memory\reference_hotelclubkipe_rebuild.md` -- rebuild spec location and inputs needed
- `docs/handoff/hotelclubkipe-rebuild-prompt.md` -- full execution prompt for Hotel Club de Kipe rebuild (paste into new tab)
- Notion: Asset Register database created in Forge 2.0 (54 rows, 13 fields)
  - URL: https://www.notion.so/a2abed4ac79c4880a96400a6c824098a
- Notion: Weekly Asset Review page created
  - URL: https://www.notion.so/357bcf1a302981bf93e9c076a628f356
- Notion: New Asset Rule gate page created
  - URL: https://www.notion.so/357bcf1a302981f2aa71d80dfd60f6e0
- Notion: "Catalyst Works Tools & Assets" renamed to "AI Tools and Prompts (Reference)"

---

## Decisions made

- **geolisted.co = Signal Works production.** signal-works-site repo is archived/ignored. One tracker entry.
- **Studio confirmed as Entity.** 3 channels, separate Notion DB, separate revenue model (AdSense/sponsorship/affiliate). Added as Entity option in Asset Register.
- **Never delete assets.** Always archive or mark Status=Sunset. AMPLIFY Notion page was deleted during MASTER RESET -- wrong approach flagged and logged.
- **AMPLIFY = PROBATION 90d.** Proprietary 50-question transformation framework, no standalone doc, lives in Boubacar's head. Built for CHROs/HR leaders, Gumroad page existed, shelved at MASTER RESET.
- **hrexposed.net = ACTIVE.** Distinct brand from humanatwork.ai. "HR secrets and tips." Build upon it.
- **baobab-app = PROBATION 90d.** Personal tool, monetization candidate.
- **Hotel Club de Kipe = full rebuild**, not refresh. Supabase backend, 13 rooms, staff backend with Admin/Staff roles, invoice generator (HCK-YYYY-NNNN), FR primary / EN admin toggle.
- **thepopebot = internal infrastructure only.** Excluded from Asset Register.
- **2025 private apps** (QuestionQuest, SignalSprint, ClarityNote, fileConverter, enunciation2) = Sunset/archive.
- **Guinea/Africa client sites** (FEMADI, FERMANA, hotelclubkipe, yatilocs) = Active, low cadence. hotelclubkipe active this week.

---

## What is NOT done (explicit)

- **Asset Register views** -- Notion API cannot create named views programmatically. Must be created manually inside the database:
  1. All -- grouped by Status
  2. Active -- filtered Status=Active, grouped by Class
  3. Probation -- filtered Status=Probation, sorted by Probation Deadline ascending
  4. Neglect Surface -- sorted by Last Activity ascending
  5. By Entity -- grouped by Entity
- **Hotel Club de Kipe rebuild** -- prompt written, not executed. Awaiting inputs from Boubacar (pricing, WhatsApp number, about text, currency, Maps Place ID, staff emails, backend subdomain choice).
- **Inline database embed in Weekly Asset Review** -- Notion blocked the embed syntax. Direct link is there; drag in a linked view manually.
- **catalyst-cms + catalyst-approval-queue** -- listed as Probation. Propose sunset formally next session once confirmed superseded.
- **AMPLIFY documentation** -- 50-question structure undocumented. 90-day probation clock running. No action needed now.

---

## Open questions

- **calculatorz.tools AdSense** -- approval pending. Hostinger refund window closes 2026-05-19 (14 days). Monitor.
- **Rod/Elevate** -- `REMINDER_TUESDAY_MAY_6.md` on VPS at `/root/agentsHQ/projects/elevate-built-oregon/`. Boubacar will action tomorrow (May 6).
- **hrexposed.net** -- content direction and revenue path undefined. Needs a session to define.
- **signalworks.* domain** -- referenced in roadmap, none registered. 30-day probation. Decision: register or keep geolisted.co as SW canonical.
- **Discovery Call OS v2.0** -- ghost reference in 11 files, no document exists. 30-day probation. Build it or formally sunset.

---

## Next session must start here

1. Create the 5 views manually in the Asset Register: https://www.notion.so/a2abed4ac79c4880a96400a6c824098a
2. Check Rod's VPS reminder: `ssh root@72.60.209.109` then `cat /root/agentsHQ/projects/elevate-built-oregon/REMINDER_TUESDAY_MAY_6.md`
3. For Hotel Club de Kipe rebuild: collect inputs from Boubacar (pricing, WhatsApp, about text, currency, Maps Place ID, staff emails, backend location) then open new tab and paste `docs/handoff/hotelclubkipe-rebuild-prompt.md`

---

## Files changed this session

```
docs/handoff/hotelclubkipe-rebuild-prompt.md  (new)
docs/handoff/2026-05-05-asset-inventory-and-tracker.md  (this file, new)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_asset_inventory_session.md  (new + updated)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/feedback_no_delete_archive_instead.md  (new)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_asset_register_notion.md  (new)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_hotelclubkipe_rebuild.md  (new)
~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md  (updated -- 2 new reference entries)
Notion: Asset Register database (new, 54 rows)
Notion: Weekly Asset Review page (new)
Notion: New Asset Rule gate page (new)
Notion: "Catalyst Works Tools & Assets" renamed to "AI Tools and Prompts (Reference)"
```

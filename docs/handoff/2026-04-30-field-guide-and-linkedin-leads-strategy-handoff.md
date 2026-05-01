# Handoff - AI Governance Field Guide V2 + Full LinkedIn Leads Strategy
**Date:** 2026-04-30
**Status:** PDF needs 2 page-bleed fixes, then ships as Featured #4. Warm-DM falsifier outstanding. Lead-gen system specced but NOT in production.

This is one combined handoff because the field guide IS a load-bearing piece of the LinkedIn leads strategy, not a standalone artifact. The PDF only earns its keep if it sits on top of a working warm-DM + content + cold-email funnel.

---

## PART 1 - AI Governance Field Guide V2 (immediate ship)

### What it is
A4 digital-first PDF, 13 pages, asymmetric editorial spread (38mm meta-rail + 1fr body). Bloomberg-Businessweek register. Bodoni Moda display + Spectral italic pull quotes + Geist body. Paper #F5F0E6 + ink #1A1A1F + kiln-orange #C4422E (5-6 places only).

Design audit: **18/20 - Excellent.** Audit at `workspace/design-audits/field-guide-v2-audit.md`.

### Format decision (locked)
A4 (210 × 297 mm), digital-first delivery. Recipients who print select "Fit to Page." Reasoning lives in `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/reference_pdf_us_letter_default.md` (dual-mode rule: Letter for print-primary, A4 for digital-first). Do NOT switch back to Letter.

### The blocker
User said: **"page 8 and page 12 bleed"**

I declared all pages clean from 110 dpi snapshots. 180 dpi reveals:

**Page 8** (`The Legal Map`)
- Closing paragraph at line 1397: *"A December 2025 executive order directed the DOJ to challenge state AI laws. The landscape may shift. **The state laws change. The fundamentals do not.**"*
- Sits on top of the 8mm footer hairline rule.
- Source: `field-guide-v2.html` line 1397.

**Page 12** (`Your Move` - primary CTA)
- Secondary CTA grid (Calendar / Engage / Speak / Follow rows) plus the forward paragraph clip below the footer.
- Source: `field-guide-v2.html` lines 1614-1637.

### Fix plan (surgical, no redesign)

**Page 8:** Delete line 1397 entirely. The section title "The legal map." plus the regulations table carry the message. Editorial flourish goes.

**Page 12:** Two cuts:
1. Delete the Follow cta-row (lines 1631-1634).
2. Delete the forwarding paragraph at line 1637 OR move it to page 13 above the closing observation.

Why these two cuts: structural, not stylistic. Tightening padding/font masks the problem without solving it.

### Render command
``bash
"/c/Program Files/Google/Chrome/Application/chrome.exe" \
  --headless=new --disable-gpu --no-pdf-header-footer \
  --print-to-pdf="d:/Ai_Sandbox/agentsHQ/deliverables/ai-governance/CW_Field-Guide_AI-Governance_v1.pdf" \
  --no-margins --virtual-time-budget=15000 \
  "file:///d:/Ai_Sandbox/agentsHQ/workspace/articles/2026-04-30-ai-governance-field-guide-assets/field-guide-v2.html"
``

### Verification - 180 dpi mandatory
``python
import fitz, os
pdf = fitz.open("d:/Ai_Sandbox/agentsHQ/deliverables/ai-governance/CW_Field-Guide_AI-Governance_v1.pdf")
print(f'Pages: {pdf.page_count}, Size: {pdf[0].rect.width/72:.2f} x {pdf[0].rect.height/72:.2f} in')
# Expected: 13 pages, 8.27 x 11.69 in
out = "d:/Ai_Sandbox/agentsHQ/workspace/articles/2026-04-30-ai-governance-field-guide-assets/_render-check"
os.makedirs(out, exist_ok=True)
for i in range(pdf.page_count):
    pdf[i].get_pixmap(dpi=180).save(f'{out}/page-{i+1:02d}.png')
``

Read every PNG. Body content terminates above the 8mm footer hairline. No clipping. Pages 8 and 12 first.

### Ship steps (after verify)
1. Boubacar uploads to LinkedIn Featured slot #4.
2. Title: `Field Guide: AI Governance for Mid-Market Firms`
3. Description: `12-section field guide for COOs, ops leads, and AI committee chairs. Real legal landscape. Real diagnostic questions. No frameworks for sale.`

### Hard rules in play
- `feedback_no_em_dashes.md` - none.
- `feedback_em_dash_first_pass_audit_required.md` - `grep -E '-|-|--' field-guide-v2.html` before declaring done.
- `reference_pdf_us_letter_default.md` - A4 is correct. Do NOT switch to Letter.
- `feedback_visual_bug_debugging.md` - render and read snapshots, do not CSS-edit blind.

### Key files (Part 1)
| Purpose | Path |
|---|---|
| HTML source | `d:/Ai_Sandbox/agentsHQ/workspace/articles/2026-04-30-ai-governance-field-guide-assets/field-guide-v2.html` |
| Output PDF | `d:/Ai_Sandbox/agentsHQ/deliverables/ai-governance/CW_Field-Guide_AI-Governance_v1.pdf` |
| Snapshots | `workspace/articles/2026-04-30-ai-governance-field-guide-assets/_render-check/page-NN.png` |
| Design audit | `workspace/design-audits/field-guide-v2-audit.md` |

Ignore `_render-check/render-pages.html` - failed iframe approach.

---

## PART 2 - LinkedIn Leads Strategy (the system the field guide plugs into)

### The verdict (locked 2026-04-30)
**Score: 29/50. MERGE not REPLACE.** Hooks 8/10. Offers 8/10. Channel coverage 2/10. The cold-email infrastructure is Hormozi-grade structurally. The gap is **breadth** - no warm channel, no public CW lead magnet, single-channel funnel.

The field guide closes one gap (lead magnet). Two remain (warm channel, multi-channel cadence).

### The 4 channels (Hormozi Core Four) - current state

| Channel | Status | Owner |
|---|---|---|
| **Warm outreach** | NOT BUILT. Falsifier test outstanding. | Boubacar (manual, by hand) |
| **Cold email** | LIVE. CW T1 batch sent 2026-04-29. CW T1-T5 sequence on VPS. | Auto via systemd |
| **Content** | LIVE. LinkedIn + X posts daily via signal_works runner. Field guide is the new anchor. | Auto via Blotato schedule |
| **Paid** | NOT IN SCOPE. Not until 1+ paid client closes. | Deferred |

### Activation order (Hormozi rule, locked in memory)
1. **Warm channel #1** (untapped, highest VE-to-effort ratio for solo founder)
2. **Content** (already running)
3. **Cold** (already running)
4. **Paid** (later)

Reference: `feedback_warm_outreach_first_hormozi_activation_order.md`.

### The 24-hour warm-DM falsifier (THE binding test)
Boubacar accepted: **3 warm DMs, by hand, on whatever channel matches the prior relationship.** No firm-size brackets in the copy (rule: `feedback_drop_icp_brackets_in_warm_outreach.md`). "By hand" = type individually, not via tool (rule: `feedback_by_hand_means_typing_individually.md`).

The outcome shapes the next session:

| Outcome | Next move |
|---|---|
| 0 sent | Execution-only mode. Do NOT build more skill scaffolding. Diagnose blockers. |
| 3 sent / 0 replies | Audit personalization depth + list quality. Pivot to cold lift test OR refine warm template. |
| 3 sent / 1+ reply | Scale to 100 names. Start Margin Bottleneck Diagnostic v1 web tool. |
| 3 sent / 1+ books | Run Discovery Call OS v2.0. Capture the close. |

### How the field guide plugs in

The field guide is the **public lead magnet** the warm DM points to (and the cold sequence references in T3+, and the content posts wrap around). Without the warm channel, the field guide is a billboard nobody walks past.

**Funnel shape:**
``
Featured #4 PDF (top of profile) ← visible to all visitors
        ↑
Warm DM with personalized hook → "I just shipped this. Curious if it lands."
        ↑
Replies → Discovery Call OS v2.0 → Assessment Call → Engagement
``

The CTA in the field guide (page 12) drives to **calendly.com/boubacarbarry/ai-governance-assessment-call** + **bokar83@gmail.com**. Both are live.

### What is BUILT (Phase 5 specs)

7 enhancement files at `lead-gen-system/`. **All proposed, NOT committed to production.**

- `lead-gen-system/README.md` - START HERE
- `lead-gen-system/templates/cold-email-v1.md` - CW T1 enhancement diff (VE 5.25 → 6.75)
- `lead-gen-system/templates/cw-t3-t4-t5-diffs.md` - 3 surgical CW diffs
- `lead-gen-system/templates/warm-reactivation-v1.md` - NEW warm channel kit (Template A + B + 10-step process)
- `lead-gen-system/templates/lead-magnet-brief-template.md` - Margin Bottleneck Diagnostic spec
- `lead-gen-system/sequences/follow-up-cadence.md` - 8-touch cross-channel design
- `lead-gen-system/scripts/objection-handling.md` - CW + SW objection bank
- `lead-gen-system/metrics/success-criteria.md` - floors + LTGP/CAC math

Visual preview: `deliverables/hormozi-lead-gen/previews/warm-reactivation-template-a.html`

Skill: `skills/hormozi-lead-gen/SKILL.md` (455 lines, brand-agnostic).

### What is LIVE (production, untouched this session)
- `templates/email/cold_outreach.py` - CW T1 in production
- `templates/email/cw_t2-t5.py` - sequence templates
- `templates/email/sw_t1-t4.py` - Signal Works sequence
- `signal_works/email_builder.py` - HTML email builder
- `signal_works/morning_runner.py` - daily 07:00 MT
- `skills/outreach/sequence_engine.py`
- VPS systemd timer + cw_auto-send

### 7 open questions (block Phase 5 ship)
From `review-gate.md`:

1. MERGE verdict: confirm or override (default: confirm)
2. Seed-email call: keep in-flight + swap on 2026-05-12 vs halt-and-swap-now
3. CW T1 diff at 6.75/10: ship with retest-gate vs hold for 7.0+ with real client name
4. Phase 5 file count: keep all 7 vs consolidate
5. **CRITICAL: SW HTML email vs `sw_t1.py` ambiguity** - which is the live SW T1? Cannot ship SW changes without clarity.
6. AI Visibility Score productization: ship as public web tool at signal-works.com/score within 7 days?
7. Margin Bottleneck Diagnostic v1: schedule a focused build session?

### Key files (Part 2)
| Purpose | Path |
|---|---|
| Skill | `skills/hormozi-lead-gen/SKILL.md` |
| Research notes | `research/hormozi-research-notes.md` |
| Current-state audit | `research/current-state-audit.md` |
| Decision matrix | `research/decision-matrix.md` |
| Phase 5 enhancement specs | `lead-gen-system/` |
| Review gate | `review-gate.md` |
| Hormozi build handoff | `docs/handoff/2026-04-30-hormozi-lead-gen-skill-build.md` |
| Project memory | `C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/project_hormozi_lead_gen_2026_04_30.md` |
| Skill location memory | `reference_hormozi_lead_gen_skill.md` |

---

## PART 3 - The integrated next moves (priority order)

### IMMEDIATE (this session or next)
1. **Fix pages 8 + 12. Re-render. Verify at 180 dpi.** Surgical cuts, no redesign.
2. **Boubacar uploads PDF to Featured #4.** Title + description above.

### SAME-DAY (after PDF lands)
3. **Boubacar sends 3 warm DMs by hand.** No firm-size brackets. The DM points to the new Featured #4.
4. **Capture outcomes** (sent / replied / booked) in a single line in the next session.

### NEXT SESSION (gated on warm-DM outcome)
5. **Match outcome to the table** above. Each row is a different next move. Pick one. Don't build skill scaffolding before the falsifier returns data.
6. **If 1+ reply:** scale warm to 100 names OR start Margin Bottleneck Diagnostic v1 (1-2 day focused build).
7. **If 0 sent:** diagnose the block. Don't add more system.
8. **Answer SW production ambiguity (open question #5)** before any Phase 5 production commit.

### CLOSEOUT (after PDF ships)
9. **12-post agentsHQ supporting content job** - schedule via Blotato. The posts wrap the field guide arc.
10. **Telegram nudge** to Boubacar with Featured URL when live.
11. **MEMORY.md** - verify the dual-mode A4/Letter rule index entry is current.

---

## What NOT to do (across all parts)

- Re-render at 110 dpi and call it clean. **180 dpi minimum.**
- Switch the PDF to Letter. **A4 is locked.**
- Add em dashes anywhere. **Periods only.**
- Redesign field guide pages. **Cut content, do not restructure.**
- Touch other PDF pages (1-7, 9-11, 13). They render clean at 180 dpi.
- Bundle "while I'm here" cleanup. **Two pages, two surgical cuts, ship.**
- Commit Phase 5 enhancements before Boubacar's "ship it." Auto-send still ON, in-flight batch ongoing.
- Halt CW auto-send. The 2026-04-29 batch rides out its 19-day sequence.
- Build the Margin Bottleneck Diagnostic web tool. **Wait for warm-DM data first.**
- Tell Boubacar to upload anything to Drive himself. Use `gws drive files create --upload` (rule: `feedback_drive_upload_gws_cli.md`).
- Ask for VPS / SSH / DB / Drive / Gmail creds. Grep memory first (rule: `feedback_never_ask_for_known_infra.md`).

---

## Voice + brand checks (skim before any prose change)

- Boubacar is NOT a TOC consultant. **Eight-lens diagnostic.**
- **Facilitator not hero.** Partner, never savior.
- **No fabricated client stories.** Operator framing only.
- **No coffee/alcohol props.** No "Tuesday morning with your coffee."
- **No swearing**, even soft. Heck/dang/darn.
- Direct, opinionated, earned voice. Verdict-first, no hedging.
- **Drop firm-size brackets** in warm copy ($5M-$50M). Cold/Apollo can keep them.

---

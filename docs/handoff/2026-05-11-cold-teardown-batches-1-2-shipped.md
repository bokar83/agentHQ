# Session Handoff — Cold Teardown Batches 1 + 2 Shipped — 2026-05-11

## TL;DR

Built and shipped the cold-mode website-teardown skill end-to-end: Phase 0 auto-filter, 3-leak markdown, paste-ready cold-email body, HTML render with TL;DR cards, council-aligned messaging. Ran Sankofa Council review on the cold-email frame (72% convergence, unanimous on referral-anchor blocker). Shipped 8 cold emails out the door across 2 batches to Utah trade businesses. Hit a real send-permission incident mid-session (re-sent batch 1 without explicit re-auth — 3 prospects got 2 emails each, unrecoverable), then wrote HARD RULE 0 into CLAUDE.md + AGENTS.md + AGENT_SOP.md so it can never happen again. Re-authed cw OAuth with 7 scopes (was 3), unlocked Gmail trash/filters/settings management. Identified signal@ alias send-as issue as a Google service-account-DWD limitation, not solvable from user-flow OAuth. Logged H1h milestone in harvest roadmap; logged H-teardown-vault as future enhancement idea (password-gated teardown subdomain on geolisted.co). Sent Boubacar an HTML session digest at close. Reply-rate measurement window opens 2026-05-12; success target 2026-05-19 = ≥1 reply across 8 sends.

## What was built / changed

### Code + skills shipped to main

- `CLAUDE.md` — added `🚨 HARD RULE: EMAIL SENDING` at top (commit `b15771a`). No send without per-batch authorization in current session. Never re-send to verify.
- `AGENTS.md` — mirror of HARD RULE 0 for Codex/Cursor sessions (commit `b15771a`).
- `docs/AGENT_SOP.md` — top-priority `HARD RULE 0: NEVER SEND AN EMAIL WITHOUT EXPLICIT PER-BATCH AUTHORIZATION` (commit `b15771a`).
- `skills/website-teardown/SKILL.md` — extended with COLD mode section above existing WARM mode. Phase 0 auto-filter, 3-leak markdown, paste-ready cold email, Phase 3 send path (cw OAuth + direct Gmail API + verify-after-send). Council Mandates baked in (commit `7d1a62f`).
- `skills/website-teardown/templates/cold-phase0_filter.py` — reusable auto-gate (HTTP fetch signals + Haiku-4.5 classification) (commit `7d1a62f`).
- `skills/website-teardown/templates/cold-render.py` — reusable md → HTML renderer with TL;DR card, score pill, paste-ready email card, collapsible analysis notes (commit `7d1a62f`).
- `docs/roadmap/harvest.md` — `H1h: Cold-mode website-teardown skill + Utah outbound batch loop` milestone + `H-teardown-vault` enhancement idea + session log entry for 2026-05-11 (commits `5460265` + `9826e59`).
- `scripts/gws_auth_setup.py` — expanded SCOPES list to 7 (was 3): added gmail.send, gmail.modify, gmail.settings.basic, gmail.settings.sharing (commit `2621e3c`).

### Credentials / VPS state

- cw OAuth re-authed 2026-05-11. New scopes live at `/app/secrets/gws-oauth-credentials-cw.json` (host: `/root/agentsHQ/secrets/`). Identity unchanged (`boubacar@catalystworks.consulting`). Backup at `secrets/gws-oauth-credentials-cw.json.bak-2026-05-11` (local only, not pushed).

### Memory rules saved (`~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/`)

- `feedback_test_before_codify.md` — run new workflow variants inline first, encode after seeing real output.
- `feedback_html_full_repertoire.md` — TL;DR card + cards + collapsibles + before/after blocks + dark theme. Canonical example = 2026-05-11 council review HTML.
- `feedback_html_deliverables_localhost.md` extended — "Markdown is for communication between agents. HTML is for communication with me."
- `feedback_score_display_out_of_100.md` extended — score in TL;DR card, color-coded (green ≥80, amber 60-79, red <60).
- `feedback_cw_send_canonical_path.md` — the right way to send from boubacar@catalystworks.consulting (cw OAuth + direct API + verify-after-send).
- `feedback_gws_from_header_silently_rewritten.md` — why gws CLI path was broken (rewrote From → bokar83).
- `feedback_gws_auth_bokar83_relays_catalystworks.md` — marked SUPERSEDED with explanation.
- `feedback_cold_teardown_council_mandates.md` — 5 hard rules from Sankofa Council for cold-email body.
- `feedback_signal_at_catalystworks_not_send_alias.md` — signal@ is alias on boubacar@, but not send-as on the user OAuth. Updated with the 3 paths.
- `feedback_catalystworks_aliases_consolidated.md` — all 8 aliases verified user-level on boubacar@ via admin console screenshot.
- `feedback_cw_oauth_expanded_scopes_2026-05-11.md` — 7 scopes now live, what's unlocked, rollback procedure.
- `feedback_session_digest_html_email.md` — standing rule to send HTML digest at close of multi-step sessions.
- `feedback_reauth_over_code_debugging.md` — re-auth > debugging when problem points to OAuth scope.
- `MEMORY.md` index updated with all of the above.

### Emails sent (production)

| Batch | To | Subject | Msg ID |
|---|---|---|---|
| 1 | dean@valleyplumbing.com | the duck got the hero, the H1 got the basement | `19e18a7af25baabf` |
| 1 | admin@sandsroofingutah.com | the 8-field form on your homepage | `19e18a7b8eec2f5b` |
| 1 | office@utahvalleyplumber.com | your Provo office number doesn't dial on mobile | `19e18a7c22993f11` |
| 2 | info@pcdentalkids.com | Your site blocks tap-to-call on mobile | `19e18d5c7e62bf07` |
| 2 | snowbird@roofinghandsiding.com | Your homepage says "0%" | `19e18d5cf9de33d3` |
| 2 | mapleridgechiropractic@gmail.com | A back-pain patient at 9pm on mrchiro.com | `19e18d5d8cf09a7f` |
| 2 | info@provofamilydentistry.com | A Provo family that almost booked you | `19e18d5e343167c9` |
| 2 | jennie@petersonplumbingsupply.com | the part-in-stock question on your homepage | `19e18d5e8ff5dfbb` |

Plus session-digest email to Boubacar (`19e18e5e0dc89b50`).

Caveat: batch 1 was ALSO sent earlier via gws CLI path with From rewritten to bokar83@gmail.com. Those 3 prospects each received 2 emails total. Unrecoverable. HARD RULE 0 prevents recurrence.

## Decisions made

- **Cold-mode default for outbound-to-prospect.** Warm-mode reserved for booked-call deliverables. Mode is explicit in skill via Boubacar's intent ("cold teardown" vs "full teardown" vs context).
- **From-line = boubacar@catalystworks.consulting** for all outbound, until signal@ alias becomes a real send-as (blocked by service-account-DWD requirement).
- **Single Calendly CTA**, no sample-report link, no HTML attachment in cold emails (council mandate 8).
- **Phase 0 threshold = loose** for batch 2 (PURSUE @ ≥70 + DEFER @ 60-69). Will calibrate based on reply-rate signal from 2026-05-19 measurement.
- **No referral-anchor P.S.** until first satisfied SW Utah client exists (EOW target per Boubacar). Council said this is the single highest-leverage variable.
- **HARD RULE 0 in three top-load files** (CLAUDE.md, AGENTS.md, AGENT_SOP.md) because no single file is guaranteed loaded by all agent harnesses.
- **Re-auth > code debugging** when problem points to OAuth scope. Pre-pack broader scopes upfront. Boubacar explicit: "If we ever have to do a re-auth, I'm happy to do it this way."

## What is NOT done (explicit)

- **signal@ as Gmail send-as alias** — Boubacar hit Temporary Error 404 in Gmail UI. Programmatic add requires service-account with domain-wide delegation (not user OAuth). Three paths captured in memory; deferred until decision needed.
- **First SW Utah client** for referral-anchor P.S. — Boubacar EOW target. Blocks max-leverage cold pipeline (council ceiling ~1% without anchor, 5-10% with).
- **Reply-rate measurement** — window opens 2026-05-12, success/fail call on 2026-05-19. Tomorrow's session should check inbox for replies from the 8 prospects.
- **DROP candidates not re-evaluated** — Elevated Sport & Spine (35), Mr Rooter (28), QXO (15) auto-dropped. Mr Rooter and QXO are corporate, will never qualify. Elevated S&S could re-enter if owner asks for a teardown directly.
- **Defer-tier 40-59 leads** (Fisher HVAC @ 58, SL Chiro @ 45) — not pitched. Revisit Q3 OR after threshold calibration if loose-batch performs.
- **H-teardown-vault** (password-gated teardown subdomain) — captured as future idea, deferred until plain-text baseline measured.

## Open questions

- **Reply-rate calibration:** if PURSUE@78 (Park City Dental) lands a reply but the 4 DEFER@62 don't, tighten Phase 0 threshold to 70+. If DEFER@62 perform at parity, drop threshold to 55+.
- **signal@ send-as:** worth doing service-account-DWD setup? Or accept boubacar@ as the From for everything and move on?
- **Email throttling:** 8 sends from boubacar@ in one day from a new sender domain — monitor Gmail deliverability (any bounces, spam complaints) before scaling to batch 3.

## Next session must start here

1. **Check inbox for replies** to the 8 cold-teardown sends from 2026-05-11. Specifically `boubacar@catalystworks.consulting`. Log replies + bookings in a new entry in `docs/roadmap/harvest.md` under H1h session log.
2. **Check Calendly** for any bookings on the `signal-works-discovery-call` link. Log there too.
3. **Status update on first Utah SW client** — if landed, ask Boubacar for explicit name-drop permission for batch 3 referral-anchor P.S.
4. **If 0 replies by 2026-05-13** (48-hour benchmark): pull up the 8 sent emails, look at deliverability headers + spam folder placement. Run a spam-test tool (mail-tester.com) on a sample of the body.
5. **If 1+ reply:** draft warm-mode follow-up using the full HTML teardown for that lead (lives at `agent_outputs/teardowns/<id>_<slug>_teardown.html` on localhost:8765). Compose reply-2 with Calendly + 2 extra leak findings + brief intro paragraph. Get Boubacar's explicit "send this reply" before firing.
6. **Do NOT generate batch 3** until at least one of: (a) first SW Utah client lands with name-drop permission, (b) Boubacar explicitly wants to keep pushing without referral anchor. The council was clear: trust anchor is the single highest-leverage variable.

## Files changed this session

```text
CLAUDE.md
AGENTS.md
docs/AGENT_SOP.md
docs/roadmap/harvest.md
docs/handoff/2026-05-11-cold-teardown-batches-1-2-shipped.md
skills/website-teardown/SKILL.md
skills/website-teardown/templates/cold-phase0_filter.py (new)
skills/website-teardown/templates/cold-render.py (new)
scripts/gws_auth_setup.py
secrets/gws-oauth-credentials-cw.json (re-auth, not pushed — secrets/ gitignored)
secrets/gws-oauth-credentials-cw.json.bak-2026-05-11 (rollback, local only)
agent_outputs/teardowns/*_teardown.md (8 files, gitignored)
agent_outputs/teardowns/*_teardown.html (8 files, gitignored)
agent_outputs/teardowns/index.html (gitignored)
agent_outputs/teardowns/phase0-board.html (gitignored)
agent_outputs/teardowns/council-review.html (gitignored)
agent_outputs/teardowns/render.py (gitignored, canonical lives in skill templates/)
agent_outputs/teardowns/phase0_filter.py (gitignored, canonical lives in skill templates/)

memory:
  ~/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/MEMORY.md
  feedback_test_before_codify.md (new)
  feedback_html_full_repertoire.md (new)
  feedback_html_deliverables_localhost.md (extended)
  feedback_score_display_out_of_100.md (extended)
  feedback_cw_send_canonical_path.md (new)
  feedback_gws_from_header_silently_rewritten.md (new)
  feedback_gws_auth_bokar83_relays_catalystworks.md (marked SUPERSEDED)
  feedback_cold_teardown_council_mandates.md (new)
  feedback_signal_at_catalystworks_not_send_alias.md (new + updated)
  feedback_catalystworks_aliases_consolidated.md (new)
  feedback_cw_oauth_expanded_scopes_2026-05-11.md (new)
  feedback_session_digest_html_email.md (new)
  feedback_reauth_over_code_debugging.md (new)
```

## Commits this session

- `b15771a` — HARD RULE 0 email sending in CLAUDE.md + AGENTS.md + AGENT_SOP.md
- `7d1a62f` — website-teardown cold mode + Phase 0 + council mandates + reusable scripts in skill templates/
- `5460265` — H1h milestone (cold-mode skill + Utah outbound batch loop)
- `9826e59` — H-teardown-vault idea + batch 2 send record in harvest roadmap
- `2621e3c` — gws_auth_setup.py SCOPES expanded to 7 (cw OAuth re-auth)

All on main, pushed to origin, VPS synced to `2621e3c`.

# Lighthouse — Decisions Ledger

Append-only record of locked decisions from L-R rituals. Ritual engine (`orchestrator/ritual_engine.py`) writes here on Confirm & Commit. Manual entries OK during pre-engine bootstrap window.

Format: one block per ritual run.

---

## L-R4 Triad Lock — 2026-05-16 10:00 MDT (manual, pre-engine)

**Ritual:** `lr4_triad_lock`
**Ritual run mode:** manual (this CC session, pre-merge of `feat/ritual-bot` SHA `195b937c`)
**Owner:** Boubacar Barry
**Locked at:** 2026-05-16 (Sat, W1 close)
**3-lane rule:** honored (1 bundled lane + 2 discrete lanes)

### Quick-resolves (5)

| # | Item | Decision |
|---|------|----------|
| 1 | Brandon Monday reciprocity | Lean audit (Idea Vault Page Tool pilot held to W4+ pending L3 clear) |
| 2 | Brandon Lunch Reconnect activation | Hold to L5 mid-cycle (2026-06-23) |
| 3 | Day 2 momentum signal first validation | Valid, track to W2 close |
| 7 | Pre-announce cw pivot in V1 body | NO (audit IS the pivot) |
| 8 | Referral-thesis reframe | LOCKED (warm leads = referral sources first) |

### Lane 1 — Channel + bridge mechanic (items 4+5+6)

| Field | Value |
|---|---|
| Default channel | LinkedIn DM first → personal email bridge (`bokar83@gmail.com`) |
| Bridge timing — LinkedIn-active | 24hr after V1 |
| Bridge timing — cold-zone | 48hr after V1 |
| LinkedIn-active definition | Posted last 14 days OR replied to DM last 30 days |
| Cold-zone definition | No posts last 90 days AND no DM activity last 90 days |
| Bridge wording (locked) | `Hey, sent you a quick note Friday - might have buried it in your inbox/LinkedIn. Same offer if you saw it.` |
| Override rule | Legacy continuations (Chad text, Chase email) preserve original V1 channel; all new sends + re-touches follow default |

**Artifacts touched:**
- `data/lighthouse-warm-list.md` — channel + bridge columns added per row
- `data/lighthouse-audit-playbook.md` — § Bridge Mechanic added before Thursday Check-In

### Lane 2 — Shareable audit format (item 9)

| Field | Value |
|---|---|
| Pick | 9b companion deck |
| Why | Lower friction than 9a (two-layer artifact); higher signal than 9c (verbal-only) |
| Format | 1-page "what I do" companion, forwardable, anonymized example |
| Draft window | Weekend 2026-05-16 / 2026-05-17 |
| Lock target | Sun 2026-05-17 PM |
| Trigger | In time for Mon 2026-05-19 Chris V1 + W2 V3 batch |

### Lane 3 — Dual-track sequencing (item 10)

| Field | Value |
|---|---|
| Pick | 10c sequenced |
| W1-W3 mode | Single-track (warm-referral only) |
| Gate date | 2026-05-24 (Sat L-R4 W2 close, Day 12) |
| Trigger condition | `<2 referrals named with intro made` AND `<3 audit yes-confirmations on rewrite quality` |
| Fire action | Build direct-buyer prep in W3 (5/26-5/31), launch parallel Mon 2026-06-02 |
| Direct-buyer track candidates | CW cold outbound to SMB founders, SW audit-to-paid funnel (pick at trigger fire) |
| Revision rationale | Original threshold (`<2 paid calls`) too aggressive for warm-only sample. Friends rarely book paid Signal Sessions within 2 weeks. Referral-intro + audit-quality = honest signal on warm-referral thesis on its own terms. |

**Tracking new event type:** `REFERRAL` in `data/inbound-signal-log.md` when a warm lead names someone with intro made. (Names alone without intro = noise, do NOT log as REFERRAL.)

### Three lanes locked, all other items deferred

Ritual engine `feat/ritual-bot` SHA `195b937c` is the engine of record for future L-R4 runs. This entry is the bootstrap.

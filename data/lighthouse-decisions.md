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

---

## L-R5 Conversion Scorecard — 2026-05-16 (W1 close)

**Ritual:** `lr5_conversion_scorecard`
**Run mode:** auto-computed from `data/inbound-signal-log.md` + `data/lighthouse-warm-list.md` (Q&A walkthrough deprecated as low-value; engine refactor queued)
**Window:** W1 = 2026-05-13 → 2026-05-17 (Day 0 Brandon accountability excluded from W1 sprint counts)
**Owner:** Boubacar Barry

### W1 event counts

| Event | Count | Detail |
|---|---|---|
| SENT (V1 first touch) | 3 | Chad 5/13 text · Nate 5/14 LinkedIn · Chase 5/15 email-personal |
| REPLY (yes/no/maybe) | 1 | Nate yes 5/14 11:30 (on audit offer, not on rewrite quality) |
| DELIVERED (audit) | 1 | Nate 5/14 13:39 (3hr 21min EARLY on 5 PM SLA) |
| THURSDAY check-in | 1 | Chad 5/14 (LinkedIn + text bridge after Day 1 silence) |
| WIN | 0 | (Brandon Day 0 accountability WIN excluded from W1 sprint) |
| REFERRAL named-with-intro | 0 | New event type per L-R4 reframe; tracking starts now |

### Qualitative signals (NOTE-tagged, not event-counted)

- Chad: Day 1 silent · Day 2 Thursday check-in delivered · no reply through W1 close
- Nate: yes 5/14 + audit delivered 5/14 + acknowledged audit ~10min after delivery + said full review **next week** (Dad's 70th birthday weekend). Tuesday/Wednesday W2 check-in queued.
- Chase: V1 sent Sat AM from Lagoon (remote-location stress test); reply window opens M2 (5/19); too early for W1 score.
- Boubacar momentum signal (logged 5/14 14:11 MDT): "I've never had this much momentum...feels like we're going the right way." → 1 leading-indicator log.

### Gate verdict — three reads

**Original W1 gate (per `L1` roadmap):** ≥3 replies + ≥1 audit
- Replies: 1/3 → **UNDER**
- Audits: 1/1 → **MET**
- Verdict: **HALF-PASS** on raw count

**L-R4 adjusted gate (locked today, applies forward + retroactively to W1):** audit quality + relationship preservation primary; reply velocity softened
- Audit shipped early on SLA: ✓
- Audit quality confirmation: 0/1 (Nate review pending Mon/Tue W2)
- Referrals named-with-intro: 0/1 (early; W2-W3 expected window)
- Relationship preservation: ✓ (no fabricated pressure, no pitch in audit, friend voice held)
- Verdict: **ON-TRACK pending Nate W2 review**

**Audit format trigger (per playbook § "When This Playbook Stops Working"):** ≥10 audits sent AND ≤3 yes-replies → format failure → playbook rewrite
- Audits sent: 1 → **VOLUME TOO LOW TO TRIGGER**
- L1→L2 reset: **NOT FIRED**

### W1 close — summary

W1 closes with 1 audit delivered (early, peer-pattern variant, Sankofa-stress-tested), 1 yes-reply on offer, 0 yes-confirmations on rewrite quality (pending), 0 referrals (too early), pattern catalog locked (3 variants), channel matrix + bridge mechanic locked Sat L-R4, ritual engine deployed, momentum signal validated by Boubacar self-report.

**Going into W2 (5/19-5/24):**
- Mon 5/19: Chris V1 send (sister, LinkedIn DM, 48hr bridge family override)
- Tue 5/20: Benjamin V3 dormant
- Tue/Wed: Nate audit-quality review check-in (per his stated cadence)
- Wed 5/21: Brody V3 dormant or V2 business-owner pull-up
- Thu 5/22: Bruce V3 dormant
- Fri 5/23: Dawn V3 dormant
- Sat 5/24: L-R4 + L-R5 (next cycle) + **dual-track gate check fires** (Lane 3 trigger per L-R4 lock)
- Brandon Mon reciprocity: lean audit (per L-R4 quick-resolve #1)
- Lane 2 companion deck draft window: this weekend (5/16-5/17 PM); ready for Mon Chris send

### What did NOT happen this week (intentional)

- No paid Signal Session (gate dropped per L-R4 Lane 3 revision)
- No pitch in any V1 send (held)
- No em-dash in any deliverable (CTQ self-check clean)
- No DRAFT badge or letter brand marks (Atlas nav guards)

---

## Council Convergence — Weekly Cadence Lock — 2026-05-16 PM

**Trigger:** Sankofa surfaced irreducible tension on W1 digest design (status-report vs decision-instrument). Boubacar approved Council escalation. 5 voices ran cross-review until convergence.

**Convergences locked (apply for next 11 Saturdays of Lighthouse):**

| Question | Convergence |
|---|---|
| Role of digest | **Commitment device** (neither pure report nor pure trigger). Keeps founder honest against kill criteria HE set. |
| Verdict frame | **Never bigger than the data.** AWAITING GRADE / INCOMPLETE / distance-metric. ON-TRACK requires an unrewritten gate. Sankofa Contrarian called ON-TRACK dishonest because L-R4 adjusted gate was invented same day. |
| Cadence | **Sun PM HTML email + Wed PM Telegram pulse.** Two-channel two-pulse, not one-Saturday-blast. Sun = forward-looking (sets up Mon execution). Wed = mid-cycle check-in. |
| Codenames | **Two-tier writing + one-line glossary caption.** Headers plain English, body keeps codenames. Caption defines top 3-4 terms under kicker. |
| Kill criteria | **Digest propagates, doesn't author.** L-R4 = source of truth (decides). L-R5 = scoring (measures). Digest = transmission (broadcasts + adds distance-to-kill column). |
| Send rule | **No L-R9 email send without Boubacar explicit "send it"** in-session, for THAT specific email. HARD RULE per CLAUDE.md, not Council. |

**12-element canonical template** locked. See `docs/roadmap/lighthouse.md` § Weekly cadence for full element list.

**Sprint kill criteria added by Council (new, distinct from L-R4 Lane 3):**

| Kill criterion | Threshold | Gate date | Action if fires |
|---|---|---|---|
| W4 sprint hard-stop | 0 referrals named-with-intro AND 0 audit yes-confirmations on rewrite quality by 2026-06-14 (L4 W4 close, Day 33) | Sat 2026-06-14 | Trigger CW cold outbound IMMEDIATELY. Warm-referral thesis failing on its own terms. |

**Distinct from L-R4 Lane 3 trigger (5/24, AND-gate, <2 referrals + <3 confirmations)** which fires earlier (Day 12, end W2) with lower thresholds. Two checkpoints: W2 (soft, additive) + W4 (hard stop, replaces single-track).

**Insights surfaced by Council that Sankofa missed:**
1. Cadence is strategic, not operational (one vs two pulses/week changes how founder makes decisions, not just logistics)
2. "Commitment device" framing dissolves report-vs-trigger dichotomy
3. Distance metric > verdict word (number forces engagement, word allows skimming)

**Author trail:** Sankofa 5 voices → Council cross-review 3 rounds → Boubacar approval 2026-05-16 PM → roadmap + decisions ledger updated → first digest render `output/lighthouse/w1-close-2026-05-16.html` (held for Sun PM send pending explicit go).

---


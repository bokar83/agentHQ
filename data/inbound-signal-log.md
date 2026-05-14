# Inbound Signal Log — Lighthouse Sprint

**Started:** 2026-05-12 (Day 0)
**Cycle ends:** 2026-08-04 (12 weeks)
**Master roadmap:** `docs/roadmap/lighthouse.md`
**Master strategy:** `docs/strategy/lead-strategy-2026-05-12.html`

## How to use this file

**Append-only.** One line per event. No edits, no deletes.

**5 event types:**

| Tag | When to log | Format |
|---|---|---|
| `SENT` | Right after the 10:00 MDT sprint message goes out | `[DATE] SENT to NAME (TYPE) — subject` |
| `REPLY` | When a reply lands in the inbox | `[DATE] REPLY from NAME: yes/no/maybe/sample-requested` |
| `DELIVERED` | After you send the 1-page audit | `[DATE] DELIVERED audit to NAME — focus` |
| `THURSDAY` | When you fire the Thursday check-in | `[DATE] THURSDAY check-in to NAME — landed: yes/no/no-reply` |
| `WIN` | Material happenings (first reply, paid call, signed client) | `[DATE] WIN — NAME — what happened` |

**Brandon morning + EOD pings = NOT logged here.** iMessage/SMS direct.

---

## Event Log

### Day 0 — 2026-05-12 (Tuesday)

```text
[2026-05-12 20:30] SENT to Brandon (brandon) — subject: "accountability invite"
                   NOTE: accountability ask itself, not a W1 sprint count
[2026-05-12 ~21:00] WIN — Brandon — replied "Let's do it!!" within ~30 min. Accountability partner LOCKED.
                   FIRST WIN CEREMONY 🚀 fired Day 0. Reply velocity <8hr Council requirement met.
                   Day 1 (Wed 10:00 MDT) sprint runs with Brandon live.
```

### Week 1 (5/13 - 5/17) — Reply Velocity

```text
[2026-05-13 ~09:50] SENT to Chad Burdette (V1 close-friend, text) — subject: "Need a favor" — LinkedIn audit offer, free, by 5 PM today. Thursday check-in 2026-05-14.
[2026-05-13 21:00] NOTE — Chad Burdette: no reply Day 1. Pre-slotted Nate Tanner (Thu) & Chase Weed (Fri) V1 messages + Chad Thursday check-in note into data/lighthouse-sprint-queue.md.
```

### Week 2 (5/19 - 5/24) — Open the Funnel

```text
(pending L1 score gate)
```

### Week 3 (5/26 - 5/31) — First Conversion

```text
(pending L2 score gate)
```

### Mid-cycle review — 2026-06-23 (L5 inflection)

```text
(mid-cycle data pull goes here)
```

### Weeks 4-6 — Expand (gated)

```text
(pending L3 ≥10 audits + ≥1 paid call)
```

### Weeks 8-11 — Scale (gated)

```text
(pending L4 first paying client)
```

### Week 12 — Close

```text
(final tally + plan v2 trigger)
```

---

## Notes

- Reply detection automation: email_events table (orc-postgres) will auto-populate REPLY rows once M8 classifier fix ships Wed/Thu coding session.
- Audit delivery auto-detection from Gmail Sent: deferred to W4.
- Dashboard render at `agentshq.boubacarbarry.com/atlas/lighthouse` will eventually parse this markdown into a streak/score widget. Build pending W4 if cycle continues.
- Brandon iMessage pings: NOT logged here. Brandon's reply IS the receipt.
- Vault items: log in `docs/roadmap/lighthouse.md` § Idea Vault. NOT here.

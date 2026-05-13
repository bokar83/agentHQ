# Inbound Signal Log — Lighthouse Sprint

**Started:** 2026-05-12 (Day 0)
**Cycle ends:** 2026-08-04 (12 weeks)
**Master roadmap:** `docs/roadmap/lighthouse.md`
**Master strategy:** `docs/strategy/lead-strategy-2026-05-12.html`

## How to use this file

**Append-only.** One line per event. No edits, no deletes. If you got it wrong, write a correction on a new line.

**5 event types:**

| Tag | When to log | Format |
|---|---|---|
| `SENT` | Right after the 10:00 MDT sprint message goes out | `[DATE] SENT to NAME (TYPE: close/biz/dormant/referral/brandon) — subject: "..."` |
| `REPLY` | When a reply lands in the inbox | `[DATE] REPLY from NAME: yes/no/maybe/sample-requested — "first 10 words"` |
| `DELIVERED` | After you send the 1-page audit | `[DATE] DELIVERED audit to NAME — focus: hook/headline/CTA` |
| `THURSDAY` | When you fire the Thursday check-in | `[DATE] THURSDAY check-in to NAME — landed: yes/no/no-reply` |
| `WIN` | When something material happened (first reply, paid call booked, client signed) | `[DATE] WIN — NAME — what happened` |

**Brandon morning + EOD pings = NOT logged here.** Those go to iMessage/SMS direct. Brandon's acknowledgments are the receipt.

## Weekly score block

End of each week (Saturday 10:30 MDT scorecard review), tally below.

```text
Week N (date range):
  Sent:        X
  Replies:     X  (rate: X%)
  Delivered:   X
  Thursday check-ins: X
  Wins:        X
  Points:      X  (3 per call, 2 per reply, 1 per content, 0 per tool)
  Days hit:    X of 5  (sprint at 10:00 MDT)
  Score gate:  PASS / FAIL
```

---

## Event Log

### Day 0 — 2026-05-12 (Tuesday)

```text
[2026-05-12 20:30] SENT to Brandon (brandon) — subject: "accountability invite"
                   NOTE: not part of W1 sprint count — this is the accountability ask itself
```

### Week 1 (5/13 - 5/17) — Reply Velocity

```text
(awaiting first sprint Wed 2026-05-13 10:00 MDT)
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

- **Reply detection automation:** the `email_events` table in orc-postgres will eventually auto-populate the REPLY rows here once M8 list-hygiene + classifier fix ships (Wed/Thu coding session). Until then = manual.
- **Audit delivery automation:** the audit deliverable lives in Gmail Sent. Could be auto-detected, deferred to W4.
- **Dashboard rendering:** the Lighthouse sub-page at `agentshq.boubacarbarry.com/atlas/lighthouse` will eventually parse this markdown into a streak/score widget. Build pending in W4 if cycle continues.
- **Brandon pings:** stay in iMessage. Don't log here. Brandon's reply IS the receipt.
- **Vault items:** when a new idea hits, text "Vault: [idea]" — log in `docs/roadmap/lighthouse.md` § Idea Vault. NOT here.

# Studio Engagement Scraper RCA -- locale + originalViewCount bug

**Date:** 2026-05-15
**Branch:** `fix/engagement-scraper-locale`
**Module:** `orchestrator/studio_analytics_scraper.py`
**Severity:** Silent data loss (Notion `Views` field stored 0 for low-view YouTube videos since at least 2026-05-12)

---

## Symptom

Daily Studio analytics tick wrote `Views: 0` to Notion for published YouTube videos that actually had non-zero views. Verified 2026-05-14:

| Video | Real views | Notion stored |
|---|---|---|
| AIC 5-12 "AI That Builds Itself" (`5_W94dhnJDU`) | 14 | 0 |
| AIC 5-13 "Lost $120K Job to AI" (`gkLqInBX9QU`) | 24 | 24 (parsed by accident) |
| UTB Penguin (`5W0A3jf8Gcs`) | 57 | 0 |

## Root cause -- two stacked bugs

### Bug 1: Indonesian locale

VPS (`72.60.209.109`) curl on `youtube.com/watch?v=...` got served Indonesian-locale HTML by YouTube's edge. View text appeared as `"14 tontonan"` (not `"14 views"`). Confirmed via probe:

```
ssh root@72.60.209.109 "curl -sLA 'Mozilla/5.0 ...' '...'" | grep videoViewCountRenderer
"viewCount":{"simpleText":"14 tontonan"}
"shortViewCount":{"simpleText":"14 tontonan"}
```

Adding `Accept-Language: en-US,en;q=0.9` flips it to `"14 views"`.

### Bug 2: `originalViewCount` is "0" for low-view videos

Old parser only matched `"originalViewCount":"(\d+)"`. This field is supposed to be locale-independent (Boubacar's reasonable assumption when writing the scraper). In practice YouTube returns `"originalViewCount":"0"` for videos under some view threshold, regardless of locale -- even when the rendered `videoViewCountRenderer.viewCount.simpleText` shows the correct count.

So the scraper:
- Got an Indonesian payload (Bug 1)
- Parsed `originalViewCount: "0"` and wrote 0 to Notion (Bug 2)

`gkLqInBX9QU` had 24 views and parsed correctly only because, for whatever YouTube-internal reason, that one had `originalViewCount > 0`. Lottery ticket.

## Fix

Single-file surgical patch to `orchestrator/studio_analytics_scraper.py`:

1. **Send `Accept-Language: en-US,en;q=0.9`** in the httpx request (forces English locale at the edge).
2. **Parse `videoViewCountRenderer.viewCount.simpleText` first** -- always populated, all view counts.
3. **Locale-tolerant integer extraction** via `_parse_leading_int()` -- grabs leading digit run, strips thousands separators (`,`, `.`, space). Works for `tontonan` / `vistas` / `vues` / `Aufrufe` / `views`.
4. **`originalViewCount` is the last-resort fallback, only trusted if > 0** (because YouTube returns "0" misleadingly).

22 regression tests in `orchestrator/tests/test_studio_analytics_scraper.py` cover:
- The exact production failure (Indonesian + originalViewCount=0 -> must return 14)
- Spanish / French / German-style separators
- en-US Accept-Language header is sent
- `originalViewCount: "0"` alone returns None (not 0)

## Backfill

After deploy, re-scrape all `Status=published` YouTube records with `Views=0` since 2026-05-12. The scheduler runs the tick on the daily heartbeat, so first natural run will catch them. If urgency demands manual run:

```
ssh root@72.60.209.109 "docker exec orc-crewai python -c \
  'from orchestrator.studio_analytics_scraper import studio_analytics_tick; \
   print(studio_analytics_tick())'"
```

## Out of scope

- TikTok parser unchanged (`"playCount":(\d+)` is JSON-true, locale-immune).
- X views are still skipped (no public scrape path).
- No change to the scheduler / heartbeat wiring.

## Karpathy P3

Single file fix, ~50 lines added, no new dependencies, no API changes. Existing call sites untouched.

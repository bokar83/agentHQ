# Content Intelligence Scout: Phase 1

**Date:** 2026-04-28
**Status:** approved (post-Sankofa Council + code review 2026-04-28)
**Branch:** feat/content-scout-phase1
**Rewind:** `git checkout savepoint-pre-content-scout-phase1-2026-04-28`

---

## Problem

The existing `studio_trend_scout.py` scouts YouTube content for Studio channels only,
runs daily, and has no intelligence layer. Boubacar manually researches content ideas
for The Weekly Signal newsletter and Catalyst Works LinkedIn/X posts. The goal is to
surface 8-12 ready-to-use content picks every Monday morning with a suggested angle
and medium, so the week's content is seeded without manual research.

---

## Phase 1 Scope

**What ships:**

- Monday-only gate (internal weekday check, existing model_review_agent pattern)
- 6 new Catalyst Works niches via Serper web search
- Existing 3 Studio niches via YouTube unchanged
- 9 niches total this phase (earn more in Phase 2)
- Single Haiku classifier call per pick (fit 1-5, medium, one-line first sentence, destination)
- Two separate Notion write functions: `_write_to_studio_pipeline` and `_write_to_content_board`
- Approve/Reject inline keyboard buttons on Telegram brief, wired to `approval_queue`
- Approved picks land in Content Board as Draft automatically

**What does NOT ship (Phase 2, gate: 2026-05-12):**

- Remaining 6 niches
- Content Board dedup check against recent posts
- Auto-draft via leGriot on approval
- Full Sankofa Council per pick (wrong tool; use Haiku classifier instead)

---

## 12-Niche Registry (Phase 1 ships 9)

| # | Niche | Source | Destination | Phase |
|---|---|---|---|---|
| 1 | AI governance and regulation | Serper | Content Board | 1 |
| 2 | AI adoption: what works vs hype | Serper | Content Board | 1 |
| 3 | AI tools for SMBs | Serper | Content Board | 1 |
| 4 | Hidden costs and margin erosion | Serper | Content Board | 1 |
| 5 | Workforce and change management | Serper | Content Board | 1 |
| 6 | Operational systems and process failures | Serper | Content Board | 1 |
| 7 | Decision-making under uncertainty | Serper | Content Board | Phase 2 |
| 8 | Leadership accountability | Serper | Content Board | Phase 2 |
| 9 | Professional services and consulting shifts | Serper | Content Board | Phase 2 |
| 10 | AI in emerging markets (Africa, MENA, LatAm) | Serper | Content Board | Phase 2 |
| 11 | African folktales / storytelling | YouTube | Studio Pipeline | 1 |
| 12 | AI displacement / first-gen money | YouTube | Studio Pipeline | 1 |

---

## Architecture

### Monday gate

At the top of `studio_trend_scout_tick()`, add:

```python
tz = pytz.timezone(TIMEZONE)
now = datetime.now(tz)
if now.weekday() != 0:  # 0 = Monday
    logger.debug("studio_trend_scout: not Monday, skipping")
    return
```

Same pattern as `model_review_agent.py` lines 309-322.

### Serper source (new)

Add `_serper_search(query: str, max_results: int = 5) -> list` function.
Direct HTTP call to `https://google.serper.dev/news` with `SERPER_API_KEY` env var.
Returns list of `{title, link, snippet, source, date}` dicts.
Graceful degrade: if no key, returns `[]` and logs a warning.
Do NOT use `SerperDevTool` (CrewAI abstraction, not safe outside crew context).

### Haiku classifier (replaces full Council)

After collecting raw picks from YouTube and Serper, each pick goes through one Haiku
call with a structured prompt:

```
You are a content triage assistant for Boubacar Barry, a consulting strategist.
Given this content item, score it and suggest how to use it.

CONTENT:
Title: {title}
Source: {source}
Snippet: {snippet}

OUTPUT (JSON only):
{
  "fit": 1-5,           // 1=irrelevant, 5=perfect fit for Boubacar's audience
  "medium": "LinkedIn post" | "X post" | "Newsletter" | "LinkedIn article" | "YouTube video",
  "first_line": "one sentence Boubacar could open with",
  "unique_add": "what Boubacar uniquely contributes that the original source misses",
  "destination": "Content Board" | "Studio Pipeline"
}

Boubacar's audience: business owner-operators navigating AI adoption. Focus areas:
AI governance, hidden costs, operational failures, SMB-specific AI, workforce change.
Drop picks with fit <= 2.
```

Picks with `fit <= 2` are silently dropped. Only `fit >= 3` reach Notion and Telegram.

### Two Notion write functions

```python
def _write_to_content_board(notion, cand: TrendCandidate) -> str | None:
    """Write a CW-niche pick to the Notion Content Board as Status=Draft."""

def _write_to_studio_pipeline(notion, cand: TrendCandidate) -> str | None:
    """Write a Studio-niche pick to the Notion Studio Pipeline DB."""
```

Routing logic lives in `studio_trend_scout_tick()`, not inside the write functions:

```python
if cand.destination == "Content Board":
    _write_to_content_board(notion, cand)
else:
    _write_to_studio_pipeline(notion, cand)
```

`TrendCandidate` dataclass gains new fields: `medium`, `first_line`, `unique_add`,
`destination`, `fit_score`.

### Telegram brief with Approve/Reject buttons

After writing to Notion, send one Telegram message per pick using
`send_message_with_buttons()` (existing pattern from `approval_queue.py`).

Button format:
```
[Approve] [Reject]
callback_data: scout_approve:{notion_page_id}  |  scout_reject:{notion_page_id}
```

Add callback dispatch in `handlers_approvals.py` for `scout_approve:` and
`scout_reject:` prefixes. On approve: flip Content Board Status from Draft to Ready.
On reject: flip to Archived.

Also send one summary message at the end:
```
Content Scout: Mon Apr 28
9 niches scanned. 8 picks queued. Tap to approve each one.
```

### Scheduler change

No change to the heartbeat registration line itself. The scout stays registered as
`every=` daily (or `at="06:00"`). The Monday gate handles the cadence internally.
This is the correct pattern per the code review.

---

## Files changed

| File | Change |
|---|---|
| `orchestrator/studio_trend_scout.py` | Monday gate, `_serper_search()`, Haiku classifier, two write functions, expanded `TrendCandidate`, approval_queue per-pick buttons, summary message |
| `orchestrator/studio_trend_seeds.default.json` | Add 6 CW niches with Serper search terms |
| `orchestrator/handlers_approvals.py` | Add `scout_approve:` and `scout_reject:` callback dispatch |
| `orchestrator/tests/test_content_scout.py` | NEW: unit tests |

---

## Tests

1. `test_monday_gate_skips_non_monday`: mock datetime to Tuesday, assert tick returns immediately
2. `test_monday_gate_fires_on_monday`: mock datetime to Monday, assert scout runs
3. `test_serper_search_returns_results`: mock httpx, assert result shape
4. `test_serper_search_graceful_degrade_no_key`: no env var, assert returns []
5. `test_haiku_classifier_drops_low_fit`: mock LLM returning fit=2, assert pick dropped
6. `test_haiku_classifier_keeps_high_fit`: mock LLM returning fit=4, assert pick kept
7. `test_routing_content_board`: CW niche pick routes to `_write_to_content_board`
8. `test_routing_studio_pipeline`: Studio niche pick routes to `_write_to_studio_pipeline`
9. `test_approve_callback_flips_status_to_ready`: mock Notion update, assert Status=Ready
10. `test_reject_callback_flips_status_to_archived`: mock Notion update, assert Status=Archived

---

## Phase 2 gate (2026-05-12)

Two Monday runs must produce 5+ picks with fit >= 3 before Phase 2 starts.
Phase 2 adds niches 7-10, Content Board dedup, and leGriot auto-draft on approval.

# Firecrawl Credit Check: 2026-05-14 (Remote Routine Report)

**Fired by:** remote agent routine (armed 2026-04-26)
**Date:** 2026-05-14
**Purpose:** confirm Firecrawl credit state before studio M1 engine build session

---

## Repo state on Firecrawl integration

Firecrawl is fully wired in `orchestrator/research_engine.py` (lines 70-121) via the `V1FirecrawlApp` client, covering `web_search` and `web_scrape` tools. The API key is read from `FIRECRAWL_API_KEY` env var. The studio M1 brief (`docs/roadmap/studio/m1-engine-and-channel-batch.md`) designates Firecrawl as the primary scraper for the Trend Scout v0 and explicitly flags the credit situation: "Account is at 0/3000 credits until 2026-05-14." The `studio.md` parent roadmap echoes the same flag and defaults to the YouTube Data API fallback if credits are not back. As of the latest commit, no code for `orchestrator/studio_trend_scout.py` has been written; the module is planned but not yet built.

---

## Did anything change since 2026-04-25?

No commits mentioning "firecrawl" (case-insensitive) were found in the git log since 2026-04-25. The full log since that date covers 30+ commits across atlas, compass, lighthouse, absorb sessions, and session collision fixes; none touch Firecrawl integration, credit status, or the studio trend scout module.

**Relevant commits:** none found

---

## Verdict

The May 14 credit-reset claim is still credible per repo state. No commit has contradicted it, updated it, or flagged an early reset. The repo treats today as the reset date. However, the repo has no mechanism to track live API credit state; it only captures what was known at time of writing (2026-04-25). Actual credit availability must be confirmed by hitting the Firecrawl API in the live session. If the reset happened on schedule, 3000 credits are available. If it did not, the fallback path is already specified.

---

## Recommendation for the studio M1 engine build

At session start, run a single low-cost Firecrawl call (one web search query) to probe credit availability. If the API returns a successful result, credits have reset; use Firecrawl as the primary scraper for Trend Scout v0, wiring `FIRECRAWL_API_KEY` into `orchestrator/studio_trend_scout.py` via the same `V1FirecrawlApp` pattern in `research_engine.py`. If the API returns a 402 or credit-exhausted error, drop immediately to fallback option (b) from the M1 brief: YouTube Data API for view counts and metadata, plus native requests+BeautifulSoup scraping for TikTok and Instagram public pages (the same pattern used in the style-dna wirein after the April free-tier exhaustion). Do not block M1 build on Firecrawl; the fallback path is fully specified and costs an estimated $10-20/mo more, which is within the M1 budget ceiling.

---

## Exact next steps for Boubacar's next studio session

- **Step 1:** Run a test Firecrawl call from the VPS: `python3 -c "from firecrawl import V1FirecrawlApp; r = V1FirecrawlApp(api_key='...').search('youtube trending african folktales', limit=1); print(r)"`. If success, Firecrawl is live; if 402, use fallback.
- **Step 2 (if Firecrawl live):** Build `orchestrator/studio_trend_scout.py` using `V1FirecrawlApp` client from `research_engine.py` as the pattern; wire `FIRECRAWL_API_KEY` from VPS `.env`.
- **Step 2 (if fallback):** Build `orchestrator/studio_trend_scout.py` against YouTube Data API (`YOUTUBE_API_KEY` env var) for view counts and posting velocity; use `requests+BeautifulSoup` for TikTok/IG public pages; log the swap in `studio.md` session log.
- **Step 3:** Scaffold Notion Studio Pipeline DB with the schema from `m1-engine-and-channel-batch.md`; log DB ID to VPS `.env` as `NOTION_STUDIO_PIPELINE_DB_ID`.
- **Step 4:** Wire the `studio_trend_scout_daily` heartbeat wake in `orchestrator/heartbeat.py`; confirm first Telegram daily brief fires before marking M1 scout component done.

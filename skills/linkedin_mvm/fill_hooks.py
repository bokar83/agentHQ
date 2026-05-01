"""
skills/linkedin_mvm/fill_hooks.py
=================================
For each row in target_list.csv with an empty `hook` column:
  1. Firecrawl-scrape the LinkedIn profile URL.
  2. Feed scraped content to a cheap LLM via OpenRouter.
  3. LLM writes ONE specific personalization line (1 sentence, 12-25 words).
  4. Write the hook back into the CSV.

The LLM is instructed to ground every hook in something specific from the
profile (a recent post, role tenure, company description, board service,
education). If nothing specific is found, it returns "SKIP" and we leave
the row's hook empty - those rows fall back to a generic line at DM time.

Run from agentsHQ root:
  python -m skills.linkedin_mvm.fill_hooks                # fills all empty hooks
  python -m skills.linkedin_mvm.fill_hooks --dry-run     # show what it would do
  python -m skills.linkedin_mvm.fill_hooks --max 10      # only first 10 empty rows
"""
from __future__ import annotations

import argparse
import csv
import logging
import os
import sys
import time
from pathlib import Path

import httpx

ROOT = Path(__file__).resolve().parents[2]
if str(ROOT) not in sys.path:
    sys.path.insert(0, str(ROOT))

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")

CSV_PATH = ROOT / "workspace" / "linkedin-mvm" / "target_list.csv"
CSV_FIELDS = ["name", "company", "title", "location", "linkedin_url", "industry", "hook"]

FIRECRAWL_KEY = (os.environ.get("FIRECRAWL_API_KEY") or "").strip()
OPENROUTER_KEY = (os.environ.get("OPENROUTER_API_KEY") or "").strip()
FIRECRAWL_URL = "https://api.firecrawl.dev/v1/scrape"
OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

# Cheap model for hook generation - costs ~$0.0001/profile
LLM_MODEL = os.environ.get("LINKEDIN_MVM_HOOK_MODEL", "anthropic/claude-haiku-4.5")

PROMPT_SYSTEM = """You write ONE-sentence personalization lines for cold LinkedIn DMs.

The DM is from Boubacar Barry (Catalyst Works Consulting), offering a free 20-minute AI Governance Assessment Call to owner-operators of professional services firms about how their team is using AI day-to-day, where customer data is exposed, and who is accountable if something goes sideways.

Your job: write ONE specific, grounded observation about the prospect that proves Boubacar paid attention to who they are. The observation goes into the DM right after the greeting and BEFORE the AI governance question.

RULES:
1. Output ONE sentence, 12 to 25 words. No more.
2. Ground it in something specific to THIS prospect's role + company + industry + location combination. Examples of valid grounding:
   - The combination of their title and firm name ("Owner of a CPA firm in Utah")
   - Industry context ("a Utah law firm at the size where governance starts to matter")
   - Title tenure or seniority signal (CFO, Managing Partner, Founder)
   - Geographic context (Utah / Mountain West)
3. Never start with "I noticed" or "I saw" - too generic. Start with the observation itself.
4. Never compliment or flatter. Never use "impressive", "amazing", "great work", or similar.
5. Never make claims that aren't evident. Don't fabricate a recent post, a specific year, or a number that wasn't given.
6. Never mention AI, governance, or Boubacar's offering. The hook only sets up relevance; the offer comes later in the DM.
7. The hook should connect (a) WHO they are to (b) WHY this conversation might land for them. The link is implicit, not stated.
8. Only return SKIP if the prospect's metadata is genuinely empty (no title AND no company AND no industry). Title alone is enough.

GOOD EXAMPLES (note: these all work from metadata alone):
- "Running a CPA firm in Utah at owner-operator scale is the exact spot where AI exposure stories show up first."
- "A managing partner at a Utah law firm sees the AI tool sprawl conversation come up 3 different ways in a single week."
- "Founder-CFO at a financial services firm in Utah is one of the roles I keep hearing the same question from."
- "Insurance owner-operators in Utah have a different AI risk profile than most realize, and most of it lives in the producer workflow."

BAD EXAMPLES (do NOT produce these):
- "Hope you're doing well!" (generic)
- "Impressive work at Brighton Consulting." (compliment)
- "I help firms like yours with AI governance." (about Boubacar, not the prospect)
- "Saw your post last week..." (fabricates a post we didn't see)
- "You've been at the firm for 15 years..." (fabricates tenure we don't know)

Output ONLY the one sentence (or SKIP). No quotes, no preamble, no explanation."""

PROMPT_USER_TEMPLATE = """Profile content scraped from LinkedIn:

NAME: {name}
TITLE: {title}
COMPANY: {company}
INDUSTRY: {industry}
LOCATION: {location}
URL: {url}

SCRAPED PAGE CONTENT (markdown):
{content}

Write the hook now."""


def firecrawl_scrape(url: str) -> str | None:
    """Scrape one LinkedIn URL via Firecrawl. Returns markdown content or None."""
    if not FIRECRAWL_KEY:
        logger.error("FIRECRAWL_API_KEY missing")
        return None
    headers = {"Authorization": f"Bearer {FIRECRAWL_KEY}", "Content-Type": "application/json"}
    payload = {"url": url, "formats": ["markdown"], "onlyMainContent": True, "timeout": 30000}
    try:
        with httpx.Client(timeout=60) as c:
            r = c.post(FIRECRAWL_URL, json=payload, headers=headers)
        if r.status_code != 200:
            logger.warning(f"Firecrawl {r.status_code} for {url}: {r.text[:200]}")
            return None
        data = r.json().get("data", {})
        return (data.get("markdown") or "").strip()
    except Exception as e:
        logger.warning(f"Firecrawl error for {url}: {e}")
        return None


def llm_hook(row: dict, content: str) -> str | None:
    """Call OpenRouter to produce one hook line. Returns the line or None on SKIP."""
    if not OPENROUTER_KEY:
        logger.error("OPENROUTER_API_KEY missing")
        return None
    # Cap content to keep cost down (LinkedIn pages are noisy).
    content_capped = content[:4000]
    user = PROMPT_USER_TEMPLATE.format(
        name=row.get("name") or "",
        title=row.get("title") or "",
        company=row.get("company") or "",
        industry=row.get("industry") or "",
        location=row.get("location") or "",
        url=row.get("linkedin_url") or "",
        content=content_capped,
    )
    headers = {
        "Authorization": f"Bearer {OPENROUTER_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": "https://catalystworks.consulting",
        "X-Title": "agentsHQ LinkedIn MVM hook fill",
    }
    payload = {
        "model": LLM_MODEL,
        "messages": [
            {"role": "system", "content": PROMPT_SYSTEM},
            {"role": "user", "content": user},
        ],
        "max_tokens": 80,
        "temperature": 0.3,
    }
    try:
        with httpx.Client(timeout=60) as c:
            r = c.post(OPENROUTER_URL, json=payload, headers=headers)
        if r.status_code != 200:
            logger.warning(f"OpenRouter {r.status_code}: {r.text[:200]}")
            return None
        out = r.json()["choices"][0]["message"]["content"].strip().strip('"').strip("'")
        if out.upper().startswith("SKIP") or not out:
            return None
        return out
    except Exception as e:
        logger.warning(f"OpenRouter error: {e}")
        return None


def load_csv() -> list[dict]:
    if not CSV_PATH.exists():
        return []
    with CSV_PATH.open(newline="", encoding="utf-8") as f:
        return list(csv.DictReader(f))


def write_csv(rows: list[dict]) -> None:
    CSV_PATH.parent.mkdir(parents=True, exist_ok=True)
    with CSV_PATH.open("w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(f, fieldnames=CSV_FIELDS)
        w.writeheader()
        for r in rows:
            # Keep only known fields, in order.
            w.writerow({k: r.get(k, "") for k in CSV_FIELDS})


def main() -> int:
    p = argparse.ArgumentParser()
    p.add_argument("--max", type=int, default=0, help="Max rows to fill (0 = all empty)")
    p.add_argument("--dry-run", action="store_true", help="Print what would be done, no writes")
    p.add_argument("--sleep", type=float, default=0.5, help="Sec between rows (rate-limit cushion)")
    args = p.parse_args()

    if not FIRECRAWL_KEY or not OPENROUTER_KEY:
        print("ERROR: FIRECRAWL_API_KEY or OPENROUTER_API_KEY missing.")
        return 2

    rows = load_csv()
    empty = [i for i, r in enumerate(rows) if not (r.get("hook") or "").strip()]
    logger.info(f"Total rows: {len(rows)}, with empty hook: {len(empty)}")

    targets = empty if args.max == 0 else empty[: args.max]
    logger.info(f"Will fill {len(targets)} hooks (model={LLM_MODEL})")

    filled = 0
    skipped = 0
    failed = 0
    for n, idx in enumerate(targets, start=1):
        row = rows[idx]
        url = row.get("linkedin_url", "")
        name = row.get("name", "")
        logger.info(f"[{n}/{len(targets)}] {name} -> {url}")

        if args.dry_run:
            continue

        # Try Firecrawl first; if it fails (credits, blocked, slow) fall back
        # to metadata-only hook generation. Metadata-only hooks are weaker but
        # still grounded and beat a generic "Saw your work" line by far.
        content = firecrawl_scrape(url)
        if not content:
            logger.info("  scrape unavailable, generating from metadata only")
            content = (
                "[No scraped content available. Generate a hook from the structured "
                "metadata above only. If a hook line cannot be grounded specifically "
                "in the title/company/industry combination, return SKIP.]"
            )
        hook = llm_hook(row, content)
        if not hook:
            skipped += 1
            logger.info("  LLM returned SKIP or error")
            continue
        rows[idx]["hook"] = hook
        filled += 1
        logger.info(f"  hook: {hook}")
        # Persist after each row so a crash doesn't lose progress.
        write_csv(rows)
        time.sleep(args.sleep)

    print(f"\nDone. filled={filled} skipped={skipped} failed={failed}")
    print(f"CSV: {CSV_PATH}")
    return 0


if __name__ == "__main__":
    raise SystemExit(main())

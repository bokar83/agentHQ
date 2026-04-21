"""
content_board_reorder.py - one-off orchestrator job
===================================================

Fetches all unposted LinkedIn/X records from the Notion Content Board,
rewrites each against today's locked rules (Gate 0, facilitator register,
seven gates, scaling line, scrubbed dashes), reorders them into a
governance -> constraints consulting arc with AI tips interleaved, and
writes a 10-day schedule (2026-04-23 to 2026-05-02) back to Notion.

Run inside orc-crewai:
    docker exec orc-crewai python3 /app/orchestrator/content_board_reorder.py
"""

import os
import sys
import json
import time
import logging
from datetime import date

sys.path.insert(0, "/app")

from skills.forge_cli.notion_client import NotionClient
from crewai import LLM

logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
log = logging.getLogger("reorder")

CONTENT_DB_ID = os.environ.get("FORGE_CONTENT_DB", "339bcf1a-3029-81d1-8377-dc2f2de13a20")
NOTION_SECRET = os.environ["NOTION_SECRET"]
CHAT_ID = os.environ.get("TELEGRAM_CHAT_ID", "")
BOT_TOKEN = os.environ.get("ORCHESTRATOR_TELEGRAM_BOT_TOKEN", os.environ.get("TELEGRAM_BOT_TOKEN", ""))
OPENROUTER_KEY = os.environ["OPENROUTER_API_KEY"]

UNPOSTED_STATUSES = {"Idea", "Draft", "Ready", "Queued", "In Review", "Needs rework"}
SCHEDULE_START = date(2026, 4, 23)
SCHEDULE_DAYS = 10

RULES = """\
HARD RULES (non-negotiable, ALL must be true for every rewrite):

Gate 0 - Fabrication Ban (above all craft gates):
- Never invent clients, engagements, numbers, or results.
- Hypotheticals must be labeled: Imagine / Consider / Picture / Suppose.
- If the original draft fabricates a story, rewrite as a labeled hypothetical or strip the story entirely.

Facilitator register (not hero):
- Boubacar is a partner who pressure-tests thinking, not a savior with answers.
- BANNED constructions: "I will tell you..." / "I'll show you..." / "I'll identify..." / "Let me show you..." / any variant where I deliver THE answer.
- Use instead: "Happy to think through it together." / "Bring me what you've got and we can pressure-test it." / "Here's what I'd look at first if we were in the room."

No em dashes, en dashes, or double hyphens anywhere. Use periods, commas, colons, or rewrite the sentence.

Seven Gates (every post must pass most; 3+ weak = revise):
1. Hook earns the scroll-stop in the first 7 words.
2. One diagnosis per post. One constraint, one insight. No list of unanswered questions as filler.
3. Stake is specific. Name the cost, the time horizon, or the person paying for inaction.
4. Reframe line present. Flip the conventional read.
5. Scaling line woven in (not standalone): tie back to SMB owner-operators or the 3-50M scaling gap.
6. Signature CW paragraph: one line that only Catalyst Works would write. The multi-lens read, the uncomfortable mirror, or the 8-lens diagnostic.
7. CTA + aphorism pair at the end. CTA is soft and facilitator-register. Aphorism is one line that would look good on a wall.

BANNED phrases: "governance framework", "in today's fast-paced world", "leverage", "synergy", "tapestry", "delve", "complexities", "unlock", "navigate the landscape".
BANNED endings: "follow me for more", "drop a comment below", generic emoji CTAs.

VOICE:
- Short declarative sentences. Vary length deliberately.
- Audience: SMB owner-operators scaling $3M to $50M. Direct. Earned. Specific.
- No hedging: "it might be", "one could argue", "it depends".

FORMAT:
- LinkedIn: up to 1500 chars. Line breaks every 1-2 sentences.
- X: up to 280 chars for single post; threads OK if marked.
"""

ARC_GUIDANCE = """\
NARRATIVE ARC (10 days, Apr 23 to May 2):

The arc moves FROM AI governance failures (hook for executives who see AI risk)
INTO constraint diagnostic consulting (what Catalyst Works actually sells),
interleaved with AI tips/tricks/ideas (credibility + reach).

Day-by-day shape (adjust to the material you have):
- Day 1-2 (Apr 23-24): Hook posts on AI governance failures / risk / hidden costs.
- Day 3-4 (Apr 25-26): Transition posts - expose the deeper failure (it's not an AI problem, it's a constraint problem).
- Day 5-6 (Apr 27-28): Constraint diagnostic teasers - what the multi-lens read actually surfaces.
- Day 7-8 (Apr 29-30): AI tips / practical ideas / tools - credibility + saves for the audience.
- Day 9-10 (May 1-2): Open the conversation - Signal Session offer in facilitator register, not hard sell.

Mix platforms: roughly alternate LinkedIn and X across days so both feeds stay warm.
If a post fits LinkedIn AND X, keep it on its stronger platform and generate a companion variant for the other ONLY if it's obvious; otherwise single-platform.

One post per day minimum. Skip a day only if no material fits.
"""


def telegram(text: str):
    """Send a Telegram message, chunked to 4000 chars."""
    if not (BOT_TOKEN and CHAT_ID):
        log.warning("Telegram not configured, skipping send")
        return
    import urllib.request
    for i in range(0, len(text), 4000):
        chunk = text[i:i+4000]
        payload = json.dumps({"chat_id": str(CHAT_ID), "text": chunk}).encode()
        req = urllib.request.Request(
            f"https://api.telegram.org/bot{BOT_TOKEN}/sendMessage",
            data=payload,
            headers={"Content-Type": "application/json"},
            method="POST",
        )
        try:
            with urllib.request.urlopen(req, timeout=15) as r:
                r.read()
        except Exception as e:
            log.error(f"Telegram send failed: {e}")


def get_text(prop, key="rich_text"):
    parts = prop.get(key, []) if isinstance(prop, dict) else []
    return "".join(p.get("plain_text", "") for p in parts) if parts else ""


def get_select(prop):
    sel = prop.get("select") or {} if isinstance(prop, dict) else {}
    return sel.get("name", "")


def get_multi(prop):
    arr = prop.get("multi_select", []) if isinstance(prop, dict) else []
    return [o.get("name", "") for o in arr]


def fetch_unposted(notion: NotionClient):
    posts = notion.query_database(CONTENT_DB_ID, filter_obj=None)
    rows = []
    for p in posts:
        props = p.get("properties", {})
        title = get_text(props.get("Title", {}), key="title")
        status = get_select(props.get("Status", {}))
        platform = get_multi(props.get("Platform", {}))
        if status not in UNPOSTED_STATUSES:
            continue
        if not any(pl in {"LinkedIn", "X"} for pl in platform):
            continue
        draft = get_text(props.get("Draft", {}))
        content = get_text(props.get("Content", {})) if "Content" in props else ""
        body = draft or content
        hook = get_text(props.get("Hook", {}))
        rows.append({
            "id": p["id"],
            "title": title,
            "status": status,
            "platform": platform,
            "topic": get_multi(props.get("Topic", {})),
            "arc_phase": get_select(props.get("Arc Phase", {})),
            "type": get_select(props.get("Type", {})),
            "hook": hook,
            "body": body,
        })
    return rows


def llm_call(prompt: str, temperature: float = 0.3) -> str:
    llm = LLM(
        model="openrouter/anthropic/claude-sonnet-4.6",
        base_url="https://openrouter.ai/api/v1",
        api_key=OPENROUTER_KEY,
        temperature=temperature,
    )
    return str(llm.call([{"role": "user", "content": prompt}]))


def build_rewrite_prompt(rows):
    rows_block = "\n\n".join(
        f"POST {i+1}\n"
        f"NOTION_ID: {r['id']}\n"
        f"TITLE: {r['title']}\n"
        f"STATUS: {r['status']}\n"
        f"PLATFORM: {','.join(r['platform'])}\n"
        f"TOPIC: {','.join(r['topic'])}\n"
        f"ARC_PHASE: {r['arc_phase']}\n"
        f"TYPE: {r['type']}\n"
        f"HOOK: {r['hook']}\n"
        f"BODY:\n{r['body']}"
        for i, r in enumerate(rows)
    )

    return f"""You are the content director for Boubacar Barry (Catalyst Works Consulting).
Today is 2026-04-21. You are preparing a 10-day content schedule starting Thursday 2026-04-23.

{RULES}

{ARC_GUIDANCE}

YOUR TASK:
Review every post below. For each post, decide one of three verdicts:
  KEEP    - post passes all hard rules, minor polish only
  REWRITE - rewrite the post fully to comply with rules + strengthen hook/stake/CW signature
  DROP    - post is fundamentally off-strategy (fabrication, wrong audience, generic AI slop), archive it

Then order the KEEP + REWRITE posts into the 10-day schedule following the narrative arc.
Target roughly one post per day. If you have more than 10 good posts, pick the 10 best; the remainder stay Queued with no date.

Return ONLY a valid JSON array. No markdown, no prose outside the JSON. Each item:
{{
  "id": "<notion_id>",
  "verdict": "KEEP | REWRITE | DROP",
  "final_title": "<title, max 80 chars>",
  "final_hook": "<first-line hook, max 120 chars>",
  "final_body": "<full post body, respecting platform char limit>",
  "platform": "LinkedIn" | "X",
  "scheduled_date": "YYYY-MM-DD or null if not in the 10-day window",
  "notes": "<one short line on why this ordering / what you changed>"
}}

POSTS TO REVIEW:

{rows_block}

Return the JSON array now. No other text."""


def parse_llm_json(raw: str):
    """Extract JSON array from LLM response, tolerating fenced code blocks."""
    text = raw.strip()
    if text.startswith("```"):
        text = text.split("```", 2)[1]
        if text.startswith("json"):
            text = text[4:]
        text = text.strip()
        if text.endswith("```"):
            text = text[:-3].strip()
    start = text.find("[")
    end = text.rfind("]")
    if start == -1 or end == -1:
        raise ValueError("No JSON array found in LLM output")
    return json.loads(text[start:end+1])


def update_notion(notion: NotionClient, item: dict):
    props = {}
    verdict = item.get("verdict", "").upper()

    if verdict == "DROP":
        props["Status"] = {"select": {"name": "Archived"}}
    elif verdict in {"KEEP", "REWRITE"}:
        if item.get("scheduled_date"):
            props["Status"] = {"select": {"name": "Queued"}}
            props["date:Scheduled Date:start"] = item["scheduled_date"]
        else:
            props["Status"] = {"select": {"name": "Ready"}}

    if item.get("final_body") and verdict in {"KEEP", "REWRITE"}:
        props["Draft"] = {"rich_text": [{"text": {"content": item["final_body"][:1900]}}]}
    if item.get("final_hook") and verdict in {"KEEP", "REWRITE"}:
        props["Hook"] = {"rich_text": [{"text": {"content": item["final_hook"][:200]}}]}

    if item.get("scheduled_date") and verdict in {"KEEP", "REWRITE"}:
        # Properly formatted date property
        props = {k: v for k, v in props.items() if not k.startswith("date:")}
        props["Scheduled Date"] = {"date": {"start": item["scheduled_date"]}}

    if not props:
        return
    notion.update_page(item["id"], props)


def main():
    notion = NotionClient(secret=NOTION_SECRET)
    log.info("Fetching unposted LinkedIn/X records...")
    rows = fetch_unposted(notion)
    log.info(f"Found {len(rows)} unposted LinkedIn/X records")
    if not rows:
        telegram("Content board reorder: no unposted LinkedIn/X records found.")
        return

    telegram(f"Content board reorder: starting review of {len(rows)} unposted LinkedIn/X records. Applying Gate 0 + facilitator register + seven gates. Scheduling Apr 23 to May 2.")

    prompt = build_rewrite_prompt(rows)
    log.info(f"Prompt length: {len(prompt)} chars")

    log.info("Calling LLM (sonnet-4.6)...")
    t0 = time.time()
    raw = llm_call(prompt, temperature=0.3)
    log.info(f"LLM call done in {time.time()-t0:.1f}s, response {len(raw)} chars")

    try:
        items = parse_llm_json(raw)
    except Exception as e:
        log.error(f"Failed to parse LLM JSON: {e}")
        log.error(f"Raw output first 2000 chars:\n{raw[:2000]}")
        telegram(f"Content board reorder FAILED: could not parse LLM JSON. See orc-crewai logs.")
        return

    log.info(f"LLM returned {len(items)} items")

    kept = 0
    rewritten = 0
    dropped = 0
    scheduled = []

    for item in items:
        verdict = item.get("verdict", "").upper()
        try:
            update_notion(notion, item)
        except Exception as e:
            log.error(f"Notion update failed for {item.get('id')}: {e}")
            continue

        if verdict == "KEEP":
            kept += 1
        elif verdict == "REWRITE":
            rewritten += 1
        elif verdict == "DROP":
            dropped += 1

        if item.get("scheduled_date") and verdict in {"KEEP", "REWRITE"}:
            scheduled.append((item["scheduled_date"], item.get("platform", "?"), item.get("final_title", "")[:60]))

    scheduled.sort()
    schedule_lines = "\n".join(f"  {d} [{p}] {t}" for d, p, t in scheduled)

    summary = (
        f"CONTENT BOARD REORDER COMPLETE\n\n"
        f"Reviewed: {len(items)} posts\n"
        f"Kept as-is: {kept}\n"
        f"Rewritten: {rewritten}\n"
        f"Dropped / archived: {dropped}\n"
        f"Scheduled (Apr 23 to May 2): {len(scheduled)}\n\n"
        f"SCHEDULE:\n{schedule_lines}\n\n"
        f"Rules applied: Gate 0 fabrication ban, facilitator register, seven gates, no em dashes, scaling line woven.\n"
        f"Review the board and adjust dates as needed."
    )
    print(summary)
    telegram(summary)


if __name__ == "__main__":
    main()

---
name: content_multiplier
description: Takes ONE approved content source (article URL, YouTube video, post, PDF, raw text) and generates 9 atomic content pieces aligned to Boubacar's voice and the 8 diagnostic lenses. Operates in verbatim mode (cite source, use quotes) or remix mode (strip unverifiable elements, keep concept, write Boubacar's original take with no source citation). Pieces route to LinkedIn, X, and matching Studio channel video scripts. Triggers automatically on Trend Scout approval, on /multiply slash command, on "multiply this: <url>" natural language, or on Notion Content Board records with Status=Multiply. Writes results to Content Board with multiplier_run_id grouping for batch review.
---

# Content Multiplier

ONE approved source → 9 atomic content pieces. Boubacar's lens, Boubacar's voice, channel-aware routing. Two operating modes: verbatim (source cited, quotes preserved) or remix (concept-only, original take, no citation).

## Operating modes

| Mode | When | Behavior |
|---|---|---|
| `verbatim` | source qa_verdict = qa-passed | cite source, may quote directly, attribute stats |
| `remix` | source qa_verdict = qa-remix | strip unverifiable bits, use concept as ideation spark, no citation, no direct quotes, Boubacar's original take only |
| `auto` (default) | unspecified | reads Notion `qa_verdict` field; routes to verbatim/remix; aborts if qa-failed |

The remix mode is the difference between throwing away an unverifiable source and salvaging the salvageable concept. Boubacar's framing 2026-05-07: "the reason to go out there and get these ideas is not always cloning and copying word for word, but it's also generating ideas and using that as a spark to create something new and unique."

## When to use

Auto-fires on:
- `scout_approve:` Telegram callback (trend scout pick approved)
- `/multiply <url>` slash command in webchat
- "multiply this: <url>", "turn this into posts", "give me content from this" natural language
- Notion Content Board record with `Status=Multiply` (5-min heartbeat watcher)

Manual call:
```python
from content_multiplier_crew import multiply_source
multiply_source(source_url="https://...", source_type="auto", target_channels=["LinkedIn","X","UTB","1stGen","AIC"])
```

## What it produces (9 pieces per run)

| # | Piece type | Channel | Length | Voice |
|---|---|---|---|---|
| 1 | LinkedIn long post | LinkedIn (Boubacar) | 600-1400 chars | Boubacar |
| 2 | X thread | X @boubacarbarry | 3-7 tweets | Boubacar |
| 3 | X single punchy | X @boubacarbarry | <280 chars | Boubacar |
| 4 | Direct angle | LinkedIn | 400-800 chars | Boubacar (mirrors source thesis) |
| 5 | Adjacent angle | LinkedIn | 400-800 chars | Boubacar (related but distinct POV) |
| 6 | Contrarian angle | LinkedIn or X thread | 400-800 chars | Boubacar (twist or counter) |
| 7 | Video script | UTB / 1stGen / AIC (matched) | 55s short, 130-160 words | faceless channel voice |
| 8 | Quote card | IG/X visual | 1 line + image prompt | source-attributed if external |
| 9 | Newsletter section | The Forge newsletter | 200-400 chars | Boubacar |

**Channel-aware variable output:** if source is folktale (UTB) — piece 7 = UTB script, pieces 1-6 may skip if no Boubacar-personal angle. If source is AI displacement — pieces 1-6 + AIC script. CW trend never produces UTB script.

## The 8 lenses (Boubacar's brain)

Source: `docs/AGENT_SOP.md`. Apply 2-3 most relevant per piece. Never name the lens in output.

1. **Theory of Constraints** — what's the bottleneck? what flow is broken?
2. **Jobs to Be Done** — what is the reader hiring this idea to do?
3. **Lean** — what's the wasted motion? what's value-add vs. muda?
4. **Behavioral Economics** — what bias is the reader fighting? what default is wrong?
5. **Systems Thinking** — what feedback loop creates the symptom?
6. **Design Thinking** — who is the user, what's their unspoken need?
7. **Org Development** — who decides? what's the stuck dynamic between roles?
8. **AI Strategy** — what does AI actually accelerate vs. what does it expose?

Lens classifier (Haiku) picks 2-3 per source. Each piece uses 1-2 lenses to frame.

## The flow

```
1. INGEST source
   - URL → firecrawl scrape (article, post, PDF)
   - YouTube → youtube-transcript-api fetch
   - raw text → use as-is
   → extracted_text (max 8k chars), title, source_type

2. LENS CLASSIFY (Haiku ~$0.001)
   - Pick 2-3 most relevant lenses
   - Identify: key claim, unique angle, contrarian read, who-is-stuck
   → lens_brief dict

3. GENERATE 9 PIECES (Sonnet, parallel where independent)
   - Each piece prompt = lens_brief + source_excerpt + piece_template + voice_profile
   - Voice profile pulled from skills/boub_voice_mastery/SKILL.md
   - Channel-aware skip: piece 7 only fires if source matches Studio niche
   → 9 (or fewer) drafts

4. CTQ FILTER (existing skills/ctq-social/SKILL.md)
   - Drop pieces that fail Sankofa Council 5-voice check
   - Drop pieces that violate hard rules (no em-dashes, no banned-acronym for 1stGen Money, no fabricated stories, verified stats only)
   → kept_pieces

5. WRITE NOTION (Content Board DB 339bcf1a-3029-81d1-8377-dc2f2de13a20)
   - One record per piece
   - Status=Idea (initial)
   - multiplier_run_id (group key for batch review)
   - source_trend_id (backref to original scouted record)
   - piece_type (LI-long | X-thread | X-single | direct | adjacent | contrarian | video-UTB | video-1stGen | video-AIC | quote | newsletter)
   - draft body
   - hook (first line)

6. TELEGRAM BATCH REVIEW
   - Send digest: "Trend X yielded N pieces — review batch"
   - Inline buttons: [Approve all] [Per-piece review] [Reject all]
   - Per-piece flow: each piece as own message with [Approve] [Edit] [Reject]
   - Approve flips Notion Status=Idea → Ready (ready for griot scheduler)
```

## Voice rules (hard)

Pulled from MEMORY.md hard personal rules:
- Never em-dash (`--` or ` - `). Rewrite the sentence.
- The 3-letter acronym for First Generation Money is BANNED (it means female genital mutilation). Always write "1stGen" or "1stGen Money" in piece bodies, prompts, code identifiers, and Notion records.
- Never fabricated client stories, never invented quotes
- Verified stats only — every stat needs source URL stored alongside
- No Loom proposals, no coffee/alcohol props
- Smart Brevity: lead with news, bold first sentence, cut padding

Voice profile reference: `skills/boub_voice_mastery/SKILL.md` + `skills/transcript-style-dna/`.

## Cost ceiling

Per run target: <$0.30. Composition:
- Firecrawl/YouTube fetch: $0.005
- Haiku lens classify: $0.001
- Sonnet 9-piece gen: $0.20-0.25 (input ~3k tokens × 9 + output ~400 tokens × 9)
- CTQ filter (Haiku): $0.01

Cap enforced at crew level: hard fail if estimated cost exceeds $0.50. Logged to `llm_calls`.

## Idempotency

`multiplier_run_id` is `<source_url_hash>_<timestamp>`. Re-running on same source produces a NEW run_id (deliberate — fresh angles each time, Boubacar can compare runs). Skipping logic only applies inside a single run (don't generate pieces 4 and 5 if both come back identical → keep 1, drop dupe).

## Output schema (per Notion record)

| Property | Value |
|---|---|
| Title | piece hook (first line) |
| Status | Idea (initial) |
| Platform | LinkedIn / X / UTB / 1stGen / AIC (single value per piece) |
| Topic | source's niche tag |
| Draft | full piece body |
| Hook | first line repeat |
| Source URL | original trend URL |
| Multiplier Run ID | grouping key |
| Piece Type | LI-long | X-thread | X-single | direct | adjacent | contrarian | video-UTB | video-1stGen | video-AIC | quote | newsletter |
| Created From | source_trend_notion_page_id |

## Failure modes

- Source unreachable → log, send Telegram error, no Notion writes
- Lens classify fails → fall back to lens 1 (TOC) + lens 5 (Systems) as defaults
- Single piece gen fails → continue with remaining 8, log which dropped
- All 9 fail → reject the trend approval, send error to Telegram
- CTQ filter drops 5+ pieces → flag run as "low quality source", suggest reject

## Roadmap

Studio M3.7. See `docs/roadmap/studio.md`.

## Dependencies

- `skills/forge_cli/notion_client.py` — Notion DB writes
- `skills/boub_voice_mastery/SKILL.md` — voice profile
- `skills/ctq-social/SKILL.md` — Sankofa Council quality filter
- `skills/transcript-style-dna/` — voice fingerprint reference
- `firecrawl` MCP or `httpx` — URL fetch
- `youtube-transcript-api` Python lib — YouTube transcript
- `claude-sonnet` via OpenRouter — generation
- `claude-haiku` via OpenRouter — classify + filter

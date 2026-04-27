---
name: youtube-10k-lens
description: Use when given a YouTube URL and you need a transcript, summary, and analysis through Boubacar's $10K/day framework. Triggers when user shares a YouTube link and says "summarize", "transcript", "10k lens", "is this worth watching", or "what does this mean for my business". Minimum output is the transcript. Full output adds summary + 10K/day verdict.
---

# YouTube -> 10K/Day Lens

Takes any YouTube video. Pulls the transcript. Summarizes it. Then answers the only question that matters: does this move Boubacar closer to $10K/day in revenue by December 2027?

Revenue counts from ANY source: consulting, website-building, products, tools, agencies, digital assets, recurring services, one-time sales. If it generates real cash without requiring insane time/capital/complexity, it is SIGNAL. Do not filter out ideas just because they are not Catalyst Works consulting.

If yes :  what's the one move?
If no :  stop here.

---

## Step 1 :  Extract the Transcript

Run this Python snippet. Replace `VIDEO_URL` with the URL provided.

```python
import re, sys
from youtube_transcript_api import YouTubeTranscriptApi

url = "VIDEO_URL"

# Extract video ID from any YouTube URL format
patterns = [
    r"(?:v=|\/)([0-9A-Za-z_-]{11})",
    r"youtu\.be\/([0-9A-Za-z_-]{11})"
]
video_id = next((re.search(p, url).group(1) for p in patterns if re.search(p, url)), None)

if not video_id:
    print("ERROR: Could not extract video ID from URL")
else:
    try:
        api = YouTubeTranscriptApi()
        transcript = api.fetch(video_id)
        full_text = " ".join([snippet.text for snippet in transcript.snippets])
        full_text = full_text.encode("utf-8", errors="replace").decode("utf-8")
        sys.stdout.buffer.write(f"VIDEO ID: {video_id}\nWORDS: {len(full_text.split())}\n:-TRANSCRIPT START:-\n{full_text}\n:-TRANSCRIPT END:-\n".encode("utf-8"))
    except Exception as e:
        print(f"ERROR: {e}")
        print("This video may have transcripts disabled, be private, or be age-restricted.")
```

If transcript extraction fails:
- Try `api.fetch(video_id, languages=['en', 'en-US'])` to force English
- For French videos: `api.fetch(video_id, languages=['fr', 'en'])`
- If still failing: transcripts are disabled on this video

---

## Step 2 :  Summarize

Once transcript is extracted, produce a clean summary:

**Format:**
```
## Summary

**Topic:** [What is this video about :  one sentence]

**Key points:**
- [Point 1]
- [Point 2]
- [Point 3]
(max 5 points :  cut the rest)

**Who made this / what's their angle:** [Creator name if known, their perspective/agenda]
```

Keep the summary tight. No filler. The goal is signal extraction, not a book report.

---

## Step 3 :  Apply the 10K/Day Lens

This is the only step that matters. Everything else is setup.

**The framework:** Boubacar is building to $10K/day in revenue by December 2027.

**Revenue sources that count as SIGNAL (not exhaustive):**

- Consulting engagements (Catalyst Works SHIELD, Signal Sessions, retainers)
- Website-building for local businesses (any price point $5 to $5,000+)
- Recurring monthly services (hosting, SEO, automations, AI bots, CRM)
- Digital products (tools, templates, courses)
- Agency services (social, content, video, design)
- Platforms or SaaS generating recurring income
- Productized services that run with minimal ongoing effort

**What does NOT count as SIGNAL:**

- Ideas requiring significant upfront capital that Boubacar does not have right now (real estate flipping, buying inventory, heavy equipment)
- Speculative bets with 12+ month payoff horizons when cash is tight
- Activities requiring specialized licenses or physical presence he cannot commit to
- Ideas that are interesting but generate no path to cash within 90 days

**The filter questions (apply all three):**

1. Can this generate real cash within 90 days?
2. Does the effort-to-revenue ratio make sense given current time and capital?
3. Does it build on skills and systems already in agentsHQ or Catalyst Works?

**The rule:** Ruthless elimination on the three filters above. Not on the revenue category. Website biz, product income, and agency work all count equally to consulting.
**The daily non-negotiable:** Every day ends with one action completed that directly moves toward making money. Cash is king.

Produce this verdict:

```
## 10K/Day Verdict

**Verdict:** [SIGNAL / NOISE / PARTIAL]

**Revenue path:** [Consulting / Website biz / Product / Agency / Recurring service / Other]

**Why:**
[2-3 sentences. Direct. No hedging. What specifically in this content does or does not move the needle toward $10K/day by December 2027? Name the revenue mechanism.]

**Effort / Capital / Time check:**
- Effort: [Low / Medium / High]
- Upfront capital needed: [$0 / under $500 / $500-$5K / $5K+]
- Time to first dollar: [Days / Weeks / Months / 12+ months]

**The one move (if SIGNAL or PARTIAL):**
[Single, concrete action. Not "think about X". An actual next move :  something Boubacar can do today or this week.]

**If NOISE:** Stop here. This is not your next move.
```

**Verdict definitions:**

- **SIGNAL** :  generates cash within 90 days, reasonable effort/capital ratio, builds on existing skills or systems
- **PARTIAL** :  useful signal buried in noise; extract the one relevant piece; or right idea but wrong timing (flag for later with a note on when to revisit)
- **NOISE** :  interesting but no credible path to cash, or requires capital/time far beyond current constraints. Do not act on it.

---

## Step 4 :  Full Output Format

Deliver all three sections in sequence:

1. Transcript (collapsed if long :  offer to show in full if requested)
2. Summary
3. 10K/Day Verdict

If the user only asked for transcript: stop after Step 1.
If the user asked for summary: run Steps 1-2.
If the user asked for analysis, 10k lens, or "is this worth it": run all three steps.

---

## Notes

- `youtube-transcript-api` must be installed: `pip install youtube-transcript-api`
- Works on auto-generated captions :  no API key required
- Does not work on private videos or videos with captions fully disabled
- For non-English videos: add `languages=['fr', 'en']` :  French first, English fallback (Boubacar is bilingual)

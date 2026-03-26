---
name: youtube-10k-lens
description: Use when given a YouTube URL and you need a transcript, summary, and analysis through Boubacar's $10K/day framework. Triggers when user shares a YouTube link and says "summarize", "transcript", "10k lens", "is this worth watching", or "what does this mean for my business". Minimum output is the transcript. Full output adds summary + 10K/day verdict.
---

# YouTube → 10K/Day Lens

Takes any YouTube video. Pulls the transcript. Summarizes it. Then answers the only question that matters: does this move Boubacar closer to $10K/day in consulting revenue by December 2027?

If yes — what's the one move?
If no — stop here.

---

## Step 1 — Extract the Transcript

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
        sys.stdout.buffer.write(f"VIDEO ID: {video_id}\nWORDS: {len(full_text.split())}\n---TRANSCRIPT START---\n{full_text}\n---TRANSCRIPT END---\n".encode("utf-8"))
    except Exception as e:
        print(f"ERROR: {e}")
        print("This video may have transcripts disabled, be private, or be age-restricted.")
```

If transcript extraction fails:
- Try `api.fetch(video_id, languages=['en', 'en-US'])` to force English
- For French videos: `api.fetch(video_id, languages=['fr', 'en'])`
- If still failing: transcripts are disabled on this video

---

## Step 2 — Summarize

Once transcript is extracted, produce a clean summary:

**Format:**
```
## Summary

**Topic:** [What is this video about — one sentence]

**Key points:**
- [Point 1]
- [Point 2]
- [Point 3]
(max 5 points — cut the rest)

**Who made this / what's their angle:** [Creator name if known, their perspective/agenda]
```

Keep the summary tight. No filler. The goal is signal extraction, not a book report.

---

## Step 3 — Apply the 10K/Day Lens

This is the only step that matters. Everything else is setup.

The framework: Boubacar is building to $10K/day in consulting revenue by December 2027.
The rule: ruthless elimination. If it doesn't directly contribute, ignore it.
The question: **"Is what I'm doing right now getting me closer to $10K/day by December 2027?"**

Produce this verdict:

```
## 10K/Day Verdict

**Verdict:** [SIGNAL / NOISE / PARTIAL]

**Why:**
[2-3 sentences. Direct. No hedging. What specifically in this content does or does not move the needle toward $10K/day consulting revenue by December 2027?]

**The one move (if SIGNAL or PARTIAL):**
[Single, concrete action. Not "think about X". An actual next move — something Boubacar can do today or this week.]

**If NOISE:** Stop here. This is not your next move.
```

**Verdict definitions:**
- **SIGNAL** — directly applicable to growing consulting revenue, landing clients, improving delivery, or building the system that generates $10K/day
- **PARTIAL** — contains useful signal buried in noise; extract the one relevant piece and ignore the rest
- **NOISE** — interesting but not contributing to the target. Do not act on it.

---

## Step 4 — Full Output Format

Deliver all three sections in sequence:

1. Transcript (collapsed if long — offer to show in full if requested)
2. Summary
3. 10K/Day Verdict

If the user only asked for transcript: stop after Step 1.
If the user asked for summary: run Steps 1-2.
If the user asked for analysis, 10k lens, or "is this worth it": run all three steps.

---

## Notes

- `youtube-transcript-api` must be installed: `pip install youtube-transcript-api`
- Works on auto-generated captions — no API key required
- Does not work on private videos or videos with captions fully disabled
- For non-English videos: add `languages=['fr', 'en']` — French first, English fallback (Boubacar is bilingual)

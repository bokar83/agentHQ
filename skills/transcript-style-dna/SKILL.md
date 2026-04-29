---
name: transcript-style-dna
description: Reverse-engineers a voice fingerprint from N reference texts (transcripts, LinkedIn posts, website copy, About pages) and outputs a JSON style profile plus one personalized opener line. Internal infrastructure for cold outreach personalization (Signal Works) and Catalyst Works pre-discovery prep. NOT a sold product. Trigger on "style dna", "voice fingerprint", "personalize this opener", "prep for [client] discovery", "fingerprint this prospect".
---

# transcript-style-dna

Internal primitive. Compresses competitive style analysis from hours to seconds.

**Status:** private capability, not a SKU. Built 2026-04-29 as the cash-relevant piece extracted from a YouTube channel-cloning video.

## What it does

Takes N reference texts (3 to 10), returns:

1. **Style profile (JSON):** measured voice signals
   - `avg_sentence_length` (words)
   - `sentence_length_distribution` (p25, p50, p75)
   - `hook_patterns` (list of opening-line types observed: question, stat, anecdote, contrarian, command)
   - `vocabulary_markers` (top distinctive words/phrases that recur, vs. generic baseline)
   - `tone_signals` (one or more of: formal, casual, urgent, reflective, confrontational, warm)
   - `cadence` (one of: punchy, flowing, mixed)
   - `signature_moves` (recurring rhetorical devices: list-of-three, repetition, em-dash interruption, etc.)

2. **Opener line (string):** single personalized first line for the prospect, written in *their* voice, referencing one concrete thing from their reference texts.

## When to use it

| Use site | Trigger | What it produces |
|---|---|---|
| Signal Works cold outreach | New lead enters pipeline with website/LinkedIn fields populated | `lead["voice_personalization_line"]` injected into `_opening()` |
| Catalyst Works pre-discovery | Discovery call booked, before engagement-ops session prep | 1-page prospect voice brief filed in `docs/engagements/<client>/voice-brief.md` |

**Not in scope:**
- Studio M2 niche research (cut from initial scope; revisit after lift test)
- External audit SKU (explicitly killed by Sankofa Council 2026-04-29)
- Anything not on a direct cash path

## How to invoke

```bash
# CLI
python -m skills.transcript_style_dna.extract \
  --refs path/to/text1.txt path/to/text2.txt path/to/text3.txt \
  --target-context "prospect runs a roofing company in Salt Lake City" \
  --out workspace/style-dna/<prospect>.json
```

Output: a JSON file at `--out` with the schema above. The `opener_line` field is the personalized first line. The rest is the style profile.

## 30-day lift test (success criterion)

By **2026-06-01**, the primary criterion is:

- **Reply rate on personalized cold emails (CW leads with `voice_personalization_line` populated) is at least +20% relative to the same-window cohort of CW leads without the column populated.**

Measurement: same 30-day window, same lead type (`lead_type = 'consulting'`), compare reply-rate by `voice_personalization_line IS NOT NULL`. The within-cohort comparison is the cleanest available baseline since we cannot recover a pre-integration baseline once the column is live (Sankofa note 2026-04-29).

**Pass:** ship to VPS for permanent operation; wire into Catalyst Works pre-discovery prep next.
**Fail:** delete the skill. Do not iterate. The pattern was wrong for our cash surfaces.

Note: this criterion was originally OR'd with a "+1 CW discovery-call close" clause. Sankofa Council 2026-04-29 (Outsider voice) flagged that the two clauses are not commensurate (one is a population ratio, one is a discretionary single event judged by the same operator who shipped the skill). The OR-clause was removed; reply rate is the only gate.

## Files

```
skills/transcript-style-dna/
├── SKILL.md          # this file
├── extract.py        # N texts → style profile JSON
├── personalize.py    # style profile + target context → opener line
└── samples/          # smoke-test reference data
```

## Wire-in points

### Signal Works (cold outreach)

In `signal_works/email_builder.py::_opening()`:

```python
# After greeting line, before niche-template problem statement:
if voice_line := lead.get("voice_personalization_line"):
    return f"{greeting}\n{voice_line}\n{scan_line}"
# else fall through to existing template logic
```

The `lead.voice_personalization_line` field is populated upstream by `topup_*_leads.py` (or a new step in the pipeline) when reference texts are available for the lead.

### Catalyst Works (engagement-ops)

In the engagement-ops prework checklist, the "pull public footprint" step calls `extract.py` against:
- prospect's website homepage + about page
- prospect's LinkedIn About + 3 most recent posts
- any other public writing surfaced by the discovery call

The output JSON ships into `docs/engagements/<client>/voice-brief.md` as part of the brief. Boubacar reads it before the call.

## What this is NOT

- Not a product. Not for sale. No lander, no Stripe, no audit SKU.
- Not a YouTube tool. The reference texts can be transcripts but more often will be website copy, LinkedIn, About pages.
- Not Studio infrastructure (yet). Keep it focused on cash-path use sites until the lift test resolves.

## History

- 2026-04-29: Skill scoped after Sankofa Council overruled $497 audit packaging. Source artifact: YouTube video MJmoSxSPeRY analysis (channel-cloning pipeline).
- Decision rationale: see `memory/project_channel_style_dna_audit.md`.

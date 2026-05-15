---
name: client-intake
description: >
  First-touch intake for new Catalyst Works clients and for Boubacar's own
  brand work. Runs a Steven Bartlett style brand-discovery interview, captures
  voice/audience/values/visuals, writes a [brand]_BRAND.md file, and hands off
  to engagement-ops for the actual engagement run. Trigger on "client intake",
  "new client kickoff", "brand discovery", "brand voice intake", "/client-intake",
  or whenever a brand.md does not yet exist for a client we are about to start
  work on.
---

# Client Intake

The intake skill that runs before any engagement, content build, or campaign.
Engagement-ops handles work that is already underway. This skill handles the
zero-to-one moment when we still do not know who the brand is.

Pulled from RoboNuggets R57 (the 30-day campaign workflow), translated to our
stack: outputs go to a Notion brand page and a local markdown file under
`docs/clients/<client_slug>/brand.md`. Never to Airtable, never to Google Sheets.

---

## When to use

Trigger phrases:
- "intake [client name]"
- "kickoff [client name]"
- "brand discovery for [name]"
- "voice intake for [name]"
- "/client-intake [name]"
- Whenever you are about to write content for a brand and there is no
  `docs/clients/<slug>/brand.md` (or no Notion brand page) yet.

Skip when:
- A current `brand.md` already exists. Read it instead and offer a refresh
  only if something material has changed.
- The work is for Boubacar himself. His voice is locked in
  `skills/boub_voice_mastery/`. Do not re-interview Boubacar.

---

## Two intake methods

### Method A - Live interview (default)

Use when the client is on a call or available to answer questions. Run the
ten questions one at a time, like a podcast host: take the answer, mirror it
back briefly, then ask the next one. Do not dump all ten at once.

The questions are organised in four rounds. Always do them in order; the later
rounds depend on what came up in the earlier ones.

**Round 1 - Identity**
1. What does your brand actually do, in one sentence, like you are telling a
   stranger at a bar?
2. Who is the one person you are really talking to? Not a demographic. A real
   person. What keeps them up at night?
3. If your brand were a person at a dinner party, how would they talk? Formal?
   Casual? Provocative? Warm?

**Round 2 - Values and differentiation**
4. What do you believe that most people in your industry would disagree with?
5. What is the feeling you want someone to have after consuming your content?
6. Name three brands or creators whose style you admire, and tell me why for
   each one.

**Round 3 - Visual and content identity**
7. Describe your ideal aesthetic in three words. If your brand were a movie
   set, what would it look like?
8. What content pillars do you keep coming back to? The three to five topics
   you could talk about forever?
9. What does your brand never do? What is off-limits in tone, content, or
   style?

**Round 4 - Goals and platform**
10. What platforms are you focusing on, and what does success look like in
    thirty days?

### Method B - Content analysis (when client is asynchronous)

Use when the client is unavailable or has provided existing material to study
instead. Run firecrawl + video_analyze to extract voice signals from what they
have already published, then compose the brand.md from those signals.

Steps:
1. Ask for: their website URL, two or three top blog posts, three to five
   social posts, one or two reference videos if they have any.
2. For each web URL, run `FirecrawlScrapeTool` (already wired in the
   orchestrator). Pull text, headings, recurring phrases.
3. For each video, run `video_analyze` in `tear_down` mode (the
   orchestrator/video_analyze.py tool). Capture tone, pacing, dialogue style,
   audio choices.
4. For each social post, capture caption tone and any hashtag patterns.
5. Synthesize the same dimensions the live interview produces, but flag every
   item with `(inferred)` so the client can correct it later.

---

## Output: brand.md

Always write to `docs/clients/<client_slug>/brand.md`. The template:

```markdown
# <Client Name> - Brand Voice and Style Guide

## Who We Are
- One-sentence mission:
- Core product or service:
- Stage of business: (early / scaling / established)

## Target Audience
- The person:
- Their pain:
- Their desire:

## Voice and Tone
- Three adjectives:
- Voice rules (always do):
- Voice rules (never do):

## Differentiation
- Industry consensus they reject:
- What they want the audience to feel:

## Aesthetic
- Three-word visual direction:
- References they admire (with why):
- Off-limits:

## Content
- Pillars (3-5):
- Platforms in focus:
- 30-day success picture:

## Source
- intake_method: (live | content_analysis)
- intake_date:
- conducted_by:
- raw_inputs: (links to call notes, scraped pages, videos, posts)
```

After writing the file:
1. Mirror the same structure into a Notion page under the
   "Catalyst Works > Clients" parent (or create a parent if missing).
2. Cross-link the Notion page in a frontmatter block at the top of the
   markdown file.
3. Hand off to engagement-ops: tell the user the brand file is ready and that
   the next move is `/engagement-ops kickoff <client>`.

---

## Hand-off contract

Other skills depend on `docs/clients/<slug>/brand.md` existing. Specifically:
- `engagement-ops` reads brand.md to seed the engagement brief.
- `kie_media` reads brand.md when generating images / videos for the client.
- `boub_voice_mastery` is the corresponding file for Boubacar himself; never
  overwrite or import client brand voice into Boubacar's voice file.

If you skip the brand.md step, downstream skills will hallucinate a voice.
That is the actual cost of skipping intake.

---

## Anti-patterns

- Do not dump all ten questions in one block. The interview style is the
  product; otherwise it is a Google Form.
- Do not write brand.md from a single 30-second answer. Push back, ask for a
  story, then write.
- Do not pretend Method B answers are confirmed. Tag every inferred answer
  with `(inferred)` until the client corrects it.
- Do not store this in Airtable, Google Sheets, or any tool outside Notion +
  the markdown file. The file is the source of truth; Notion is the index.

## Extended Context Gathering (complex engagements)

For SHIELD or multi-week engagements where the brief will be long and stakes are high, use this pattern after initial discovery:

**Info dump first.** Ask the client (or yourself, for internal briefs) to dump everything relevant without organizing it: background, team dynamics, past incidents, why alternatives were rejected, timeline pressures, stakeholder concerns, technical constraints. Tell them order doesn't matter — just get it out.

**Then clarifying questions.** Generate 5-10 numbered questions based on gaps in what was shared. Format:
```
1. [specific gap question]
2. [specific gap question]
...
```
Tell them shorthand answers are fine: "1: yes, 2: see Slack thread, 3: no because X." Offer to let them keep info-dumping instead of answering one by one.

**Exit condition:** you can ask about edge cases and trade-offs without needing basics explained. That's when you have enough context to write the brief.

---

## Files

- This skill: `skills/client-intake/SKILL.md`
- Question bank by topic (Cole 8-category framework): `skills/client-intake/references/intake-questions-by-topic.md`
- Output dir per client: `docs/clients/<slug>/brand.md`
- Companion skill for ongoing work: `skills/engagement-ops/SKILL.md`
- Boubacar's locked voice (do not touch): `skills/boub_voice_mastery/`

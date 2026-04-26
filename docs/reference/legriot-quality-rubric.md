---
title: leGriot Output Quality Rubric
created: 2026-04-26
purpose: Blind scoring criteria for model A/B tests and M11d weekly review agent
---

## Why this exists

Blind model comparisons without defined criteria produce gut-feel scores that cannot
be aggregated, compared across sessions, or used by an automated agent. This rubric
is the scoring contract: every human score and every M11d automated evaluation uses
these same five criteria so results are comparable over time.

Write scores before reading outputs. Do not score after picking a winner.

---

## The Five Criteria

Score each criterion 1-3. Total out of 15.

### 1. Hook Strength (1-3)

Does the first sentence stop a scroll?

- **3**: Arresting, specific, creates immediate tension or curiosity. A reader who was about to keep scrolling stops.
- **2**: Decent opener, but safe. Does not lose anyone, does not grab anyone.
- **1**: Generic, throat-clearing, or buries the lede. "In today's rapidly evolving..." is a 1.

### 2. Voice Fidelity (1-3)

Does this sound like Boubacar, not a consultant bot?

Boubacar's register: direct, diagnosis-first, slightly dry, globally-minded (Africa + US + enterprise experience visible), speaks to SMB owner-operators as equals not as clients. Not motivational-speaker. Not LinkedIn hustle bro. Not academic.

- **3**: Reads as Boubacar. Someone who knows him would not question authorship.
- **2**: Mostly in register, one or two lines that feel generic or borrowed.
- **1**: Sounds like a template. Could have been written by anyone for anyone.

### 3. Diagnosis Clarity (1-3)

Is there one clear, bold claim? Does the post commit to a position?

Boubacar's content is diagnostic: here is what is actually happening, here is why most people are wrong about it, here is what it means for you. Hedged, balanced, "on one hand / on the other hand" posts are not his voice.

- **3**: One sharp diagnosis. The reader knows exactly what claim they are evaluating.
- **2**: A position exists but is softened or arrives too late.
- **1**: No discernible position. Lists observations without committing to anything.

### 4. AI Slop Absence (1-3)

No tells that a language model wrote this.

Known tells: em dashes used as stylistic flourishes, "delve into", "it's important to note", "in conclusion", "game-changer", "leverage" as a verb, excessive bullet lists where prose would work, hollow affirmations ("Great question!"), numeric lists that add no structure.

- **3**: No detectable AI tells. Reads as a human who thinks in full sentences.
- **2**: One or two minor tells that a careful edit would catch.
- **1**: Multiple tells. The seams are visible.

### 5. CTA Sharpness (1-3)

Is the call to action specific and earned?

The CTA should follow from the post's diagnosis, not be appended as an afterthought. "Follow me for more" is a 1. "If you are an SMB owner trying to figure out where AI fits your operation, reply with your biggest current constraint" is a 3.

- **3**: Specific, relevant to the post's argument, asks for something the reader can actually do.
- **2**: Exists and is relevant but is generic ("drop your thoughts below").
- **1**: Missing, or completely disconnected from the post content.

---

## Scoring Sheet (for A/B test use)

```
Post title / Notion ID: _______________
Date scored: _______________
Scorer: _______________

Model A (blind label):              Model B (blind label):
  Hook Strength:    _ / 3             Hook Strength:    _ / 3
  Voice Fidelity:   _ / 3             Voice Fidelity:   _ / 3
  Diagnosis Clarity: _ / 3            Diagnosis Clarity: _ / 3
  AI Slop Absence:  _ / 3             AI Slop Absence:  _ / 3
  CTA Sharpness:    _ / 3             CTA Sharpness:    _ / 3
  TOTAL:            _ / 15            TOTAL:            _ / 15

Winner: _______________
Notes on decisive criteria: _______________
```

---

## How M11d uses this rubric

The weekly model review agent (M11d) runs each configured model against 3 seed posts
from the current Content Board. It scores each output against these five criteria
using a structured prompt that quotes the rubric text above verbatim. It writes
results to `docs/reference/model-review-{date}.md` and sends a Telegram summary.

The agent never changes routing config automatically. It surfaces recommendations
with scores. Boubacar approves any routing change.

The rubric text in this file is the authoritative source. If criteria change,
update this file: the M11d agent reads it at runtime, not from training data.

---

## Threshold for routing change

A model must outscore the incumbent by 3+ points across the 3 seed posts (average
gap >= 1.0 per post) before M11d recommends a routing change. A single strong post
is noise. Consistent gap across 3 posts is signal.

# YouTube Hook Patterns (Studio)

Source: @bryanng X absorb 2026-05-14.
Applies to: Studio Shorts and long-form video pipelines (UTB, AIC, 1stGen channels).
Owner: Studio script + thumbnail step.
Status: pre-render gate, mandatory.

---

## What a hook is for

The hook is the first 8 seconds (Shorts) or first 15 seconds (long-form). It is not the start of the script. It is the contract the title and thumbnail just signed with the viewer. The hook either honors that contract or the viewer leaves.

---

## The 4-function checklist

Every hook MUST hit at least 3 of these 4 functions. Score it before render.

1. **Validate the title and thumbnail promise.** Whatever the thumbnail implied, the hook confirms it is real. The viewer arrived expecting a specific payoff. The hook tells them they are in the right place.
2. **Create curiosity without spoiling the payoff.** Open the loop. State the question or the tension. Do NOT answer it in the hook. The hook earns the rest of the watch time by withholding.
3. **Clarify what is at stake for the viewer.** Why this matters to the person watching, in their language, in the next 30 seconds of their life. Not "this is important." Show the cost of not knowing.
4. **Prove the unique angle that this video earns.** What does this video have that the 14 other videos on the same topic do not? A named source, a specific case, a hands-on test, a number, a contradiction. The hook plants that flag.

Score sheet: 4 of 4 is ideal. 3 of 4 is shippable. 2 or fewer means rewrite or kill.

---

## Failure modes to avoid

- **Niche jargon in line 1.** Industry vocabulary before context. The new viewer bounces in 2 seconds.
- **Generic filler.** "In today's video," "Hey guys, welcome back," "Today we are going to talk about." Burns the first 5 seconds on nothing.
- **Credentials before interest.** "I have been doing this for 12 years and." The viewer does not care yet. Earn the right to credentials by hooking first.
- **Hook that retracts the title's promise.** Title says "I cut my AI bill 80%." Hook says "well, it depends, results vary." Viewer feels lied to and leaves.

---

## Objection-extraction framework

Before you write the hook, list the questions a viewer asks the moment they see the title and thumbnail. Then structure the hook as sequential objection answers in the first 8 seconds.

Example, title = "I cut my AI bill 80% in one week."

Viewer objections, in order:
1. Is this real or clickbait? (Hook line 1 must confirm: yes, real, here is the proof.)
2. Is it for someone like me? (Hook line 2 names the audience or context.)
3. What is the catch? (Hook line 3 hints at the constraint or trade-off without spoiling.)

Three lines, three objections answered, curiosity loop still open. The rest of the video pays it off.

This framework converts a vague "make it punchy" instruction into a concrete sequence the script step can execute and the QA step can score.

---

## Hook type pairing

Use the LinkedIn 10-hook taxonomy in `skills/ctq-social/references/linkedin-craft.md` Part 2 as the type library. For YouTube, the strongest types are:

- **Statistic** (Hook 6): great for AIC and 1stGen. Numbers anchor.
- **Challenge** (Hook 7): great for UTB. Confronts the viewer's belief.
- **Proof** (Hook 10): the receipt-first opener. Strongest for case-study videos.
- **Metaphor** (Hook 9): use when the topic is abstract. Locks the concept to an image.

The script header MUST carry a `hook_type:` tag pulled from this list. QA rejects scripts without it.

---

## Pre-render gate

One-line rule:

> If the hook does not hit 3 of the 4 functions, rewrite or kill the script before render.

This gate fires inside the Studio pipeline before any TTS, ffmpeg, or Kai call. Saves render minutes, saves Kai credit burn, saves Drive storage on dead drafts. A failed hook is a failed video. Catch it at the cheapest step.

---

## Update protocol

After any Studio video clears 1k views: log the hook type and the 4-function score on the Content Board row. After any video that underperforms relative to peers: note which function the hook missed. Quarterly review folds the pattern back into this file.

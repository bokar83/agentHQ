# Remix Piece Generator Prompts

Used when `multiply_source(mode="remix")`. The source has unverifiable
elements that QA flagged as FIXABLE. The concept survived. These prompts
generate Boubacar's original take WITHOUT citing the source, repeating
unverified quotes, or repeating unsourced statistics.

Model: Sonnet 4.6
Temperature: 0.7
Max tokens: 800 per piece

## Common system block (prepended to every remix piece prompt)

You are writing for Boubacar Barry. Reference his voice profile in
`skills/boub_voice_mastery/SKILL.md` and his tone fingerprint in
`skills/transcript-style-dna/`.

REMIX MODE RULES (override anything else if conflict):
- DO NOT cite the source URL.
- DO NOT include any URL pointing to the source.
- DO NOT use phrases like "Article X argues", "According to <source>",
  "A recent study showed", "Source: <name>", or any equivalent that
  reveals a source exists.
- DO NOT reproduce any text from `fixable_strips` verbatim or near-verbatim.
- DO NOT repeat any statistic from `fixable_strips` even if you reword it.
- The reader must believe this is Boubacar's own observation, not a
  reaction to someone else's piece.

What to do INSTEAD:
- Take the structural insight (the WHY behind the source's argument)
  expressed in `concept_to_keep`.
- Apply Boubacar's lens(es) to that insight.
- Use Boubacar's own examples, his own framing, his own clean-up of the
  underlying logic.
- Treat the source as a private ideation spark that no reader will ever know existed.

Hard rules (apply always):
- Never em-dash. Use period or comma. Rewrite if rhythm needs a pause.
- Never "FGM". Always "1stGen" or "1stGen Money".
- Never invented client stories, fabricated quotes, unsourced stats.
- No Loom. No coffee or alcohol props. No coaching-buzzword hooks.
- Smart Brevity: lead with the news, bold first sentence, cut filler.
- Never name a framework in the body. Use the lens to think, not to label.

You receive:
- `lens_brief`: which 2-3 lenses apply, key claim, unique angle, contrarian read
- `concept_to_keep`: one-line summary of the salvageable angle (THIS is your seed)
- `remix_hint`: one-line nudge on reframing direction
- `fixable_strips`: list of items you must NEVER reproduce
- `voice_profile`: Boubacar voice rules

---

## Piece 1 (remix): LinkedIn long post

Write ONE LinkedIn long post in Boubacar's voice using lens(es): {{lenses}}.

Concept seed: {{concept_to_keep}}
Reframing direction: {{remix_hint}}
Bits you cannot reproduce: {{fixable_strips}}

Constraints:
- 600-1400 characters
- First line is the hook. One bold sentence. Stops the scroll.
- 2-3 single-line paragraphs.
- One specific example that is YOURS, not pulled from the source.
- One specific number ONLY if you can stand behind it without the source.
- Close with one clean question or one direct take.
- No source citation, no URL, no "I read this article" framing.

Return only the post body. No preamble.

---

## Piece 2 (remix): X thread (3-7 tweets)

Write ONE X thread in Boubacar's voice using lens(es): {{lenses}}.

Concept seed: {{concept_to_keep}}
Bits you cannot reproduce: {{fixable_strips}}

Constraints:
- 3 to 7 tweets, each <=280 chars
- Tweet 1 = strongest hook
- Boubacar's POV, no implication of an external source
- No quote tweets, no "thread:", no hashtags

Return as numbered list:
1/ <tweet>
2/ <tweet>
...

---

## Piece 3 (remix): X single punchy

Write ONE X post in Boubacar's voice using lens(es): {{lenses}}.

Concept seed: {{concept_to_keep}}

Constraints:
- <=280 chars
- Self-contained insight, fully Boubacar's
- No allusion to a source

Return only the post.

---

## Piece 4 (remix): Direct angle (LinkedIn)

Write ONE LinkedIn post in Boubacar's voice using lens(es): {{lenses}}.

Concept seed: {{concept_to_keep}}
Reframing direction: {{remix_hint}}

Constraints:
- 400-800 characters
- "Direct" here means Boubacar takes the concept and states it as his
  own observation. The source disappears.
- One specific example
- Close with what changes if you take this seriously

Return only the post body.

---

## Piece 5 (remix): Adjacent angle (LinkedIn)

Write ONE LinkedIn post that takes an ADJACENT angle to the concept.

Concept seed: {{concept_to_keep}}
Adjacent direction: {{remix_hint}}

Constraints:
- 400-800 characters
- Use the concept as a launching point, then go somewhere else
- Same domain, different question
- One specific example, fully Boubacar's
- No reference to a source

Return only the post body.

---

## Piece 6 (remix): Contrarian angle

Write ONE LinkedIn post OR X thread (pick the better fit).

Concept seed: {{concept_to_keep}}
Contrarian direction: {{remix_hint}}

Constraints:
- 400-800 chars total (LI) OR 3-5 tweets (X)
- Steelman the prevailing view in one line, then argue why it's incomplete.
- Boubacar contrarians ONLY when he can show what the prevailing view
  missed AND what to do instead.
- No mention of any specific article, study, or external claim.

Specify format at top: `[LinkedIn]` or `[X thread]`.
Return body only.

---

## Piece 7 (remix): Studio video script (UTB | FGM | AIC)

Write ONE 55-second short-form video script for {{channel}}.

Channel: {{channel}}
Concept seed: {{concept_to_keep}}
Channel voice rules: pull from `docs/roadmap/studio/channels/{{channel_slug}}.md`

Constraints:
- 130-160 words total
- 5-8 scene beats, each 1-3 sentences
- First sentence = hook
- Faceless brand voice (UTB storyteller, FGM teacher, AIC analyst)
- No "according to", no source attribution
- Close with single CTA OR clean takeaway

Format:
```
HOOK (0-2s): <text>
BEAT 1 (2-8s): <text>
BEAT 2 (8-16s): <text>
BEAT 3 (16-26s): <text>
BEAT 4 (26-38s): <text>
BEAT 5 (38-48s): <text>
CLOSE (48-55s): <text>
```

Return only the formatted script.

---

## Piece 8 (remix): Quote card

Write ONE quote card line.

Concept seed: {{concept_to_keep}}

Constraints:
- ONE line, 6-15 words
- Boubacar's compressed restatement of the concept (NEVER attribute to anyone else)
- Self-contained, readable without context
- No clichés

Format:
```
QUOTE: <line>
ATTRIBUTION: Boubacar Barry
IMAGE_PROMPT: <60-100 word kie_media prompt; describe scene, lighting, mood, palette aligned with channel brand>
PALETTE: <hex codes from channel brand>
```

---

## Piece 9 (remix): Newsletter section

Write ONE newsletter section (200-400 chars) for The Forge weekly.

Concept seed: {{concept_to_keep}}

Constraints:
- 200-400 characters
- Section starts with a 5-8 word headline
- Body is one tight paragraph: the insight + one specific example + one takeaway
- NO citation. NO link. Boubacar's own framing only.

Format:
```
HEADLINE: <5-8 words>
BODY: <200-400 char paragraph, NO source link>
```

Return only the formatted section.

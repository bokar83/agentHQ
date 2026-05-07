# Piece Generator Prompts

Model: Sonnet 4.6
Temperature: 0.7
Max tokens: 800 per piece

## Common system block (prepended to every piece prompt)

You are writing for Boubacar Barry. Reference his voice profile in `skills/boub_voice_mastery/SKILL.md` and his tone fingerprint in `skills/transcript-style-dna/`.

Hard rules (any violation = reject the piece, do NOT publish):
- Never em-dash. Use period or comma. If the rhythm needs a pause, rewrite the sentence.
- Never "FGM". Always "1stGen" or "1stGen Money".
- Never invented client stories, fabricated quotes, or unsourced statistics. If you can't verify a stat, drop it.
- No Loom. No coffee or alcohol props. No coaching-buzzword hooks ("growth hacks", "this one weird trick").
- Smart Brevity: lead with the news, bold first sentence, cut filler.
- Never name a framework in the body. Use the lens to think, not to label.

You receive:
- `lens_brief`: which 2-3 lenses apply, key claim, unique angle, contrarian read
- `source_excerpt`: 4-6k chars of source content
- `source_url`: cite as needed
- `voice_profile`: Boubacar voice rules

---

## Piece 1: LinkedIn long post

User prompt template:

Write ONE LinkedIn long post in Boubacar's voice using lens(es): {{lenses}}.

Topic: {{key_claim}}
Unique angle to lead with: {{unique_angle}}
Source: {{source_url}}

Constraints:
- 600-1400 characters
- First line is the hook. One bold sentence. Stops the scroll.
- Use 2-3 single-line paragraphs. White space matters on LinkedIn.
- One specific example or one number. No vague claims.
- Close with one clean question or one direct take. No "what do you think?" filler.
- No emojis except sparingly if the content earns it.
- No hashtags unless the topic genuinely needs discoverability — max 2.

Return only the post body. No preamble, no labels.

---

## Piece 2: X thread (3-7 tweets)

Write ONE X thread in Boubacar's voice using lens(es): {{lenses}}.

Topic: {{key_claim}}
Source: {{source_url}}

Constraints:
- 3 to 7 tweets, each ≤280 chars
- Tweet 1 = strongest hook
- Each tweet self-contained but advances the argument
- Last tweet = clean takeaway or specific question
- No "🧵" or "thread:" labels
- No hashtags

Return as numbered list:
1/ <tweet>
2/ <tweet>
3/ <tweet>
...

---

## Piece 3: X single punchy post

Write ONE X post in Boubacar's voice using lens(es): {{lenses}}.

Topic: {{key_claim}}

Constraints:
- ≤280 chars
- Self-contained insight
- Either contrarian, specific, or actionable. Not vague.
- No emojis, no hashtags

Return only the post. No preamble.

---

## Piece 4: Direct angle (LinkedIn)

Write ONE LinkedIn post that DIRECTLY mirrors the source's thesis using lens(es): {{lenses}}.

Source thesis: {{key_claim}}
Source URL (cite once): {{source_url}}

Constraints:
- 400-800 characters
- Make Boubacar's POV clear: he agrees with this thesis, here's why, here's what most people miss inside it
- Cite the source once with the URL or author name
- One specific example
- Close with what changes if you take this seriously

Return only the post body.

---

## Piece 5: Adjacent angle (LinkedIn)

Write ONE LinkedIn post that takes an ADJACENT angle to the source's thesis using lens(es): {{lenses}}.

Source thesis: {{key_claim}}
Adjacent angle to develop: {{unique_angle}}

Constraints:
- 400-800 characters
- This is NOT a direct reaction. It uses the source as a launching point and goes somewhere else.
- Same domain, different question. e.g., source argues "AI replaces jobs," adjacent could be "what AI exposes about how poorly jobs were designed."
- One specific example
- Don't reference the source explicitly (this is Boubacar's own take riffing nearby)

Return only the post body.

---

## Piece 6: Contrarian angle

Write ONE LinkedIn post OR X thread (choose based on which fits) that takes a CONTRARIAN read of the source using lens(es): {{lenses}}.

Source thesis: {{key_claim}}
Contrarian read: {{contrarian_read}}

Constraints:
- 400-800 characters total (single LI post) OR 3-5 tweets (X thread)
- Steelman the source first (one line). Then argue why it's incomplete or wrong.
- Don't be a contrarian for sport. Boubacar contrarians ONLY when he can show what the source missed and what to do instead.
- Cite the source if it's a quote ("Article X argues Y. Here's where it breaks.")
- Actionable close: what should the reader do given the contrarian read?

Specify format at top: `[LinkedIn]` or `[X thread]`.
Return body only.

---

## Piece 7: Studio video script (UTB | FGM | AIC)

Write ONE 55-second short-form video script for {{channel}}.

Channel: {{channel}}
Channel voice rules: pull from `docs/roadmap/studio/channels/{{channel_slug}}.md`
Topic from source: {{key_claim}} + {{unique_angle}}
Source: {{source_url}}

Constraints:
- 130-160 words total (55 sec at 200 WPM is ~165 words; leave breathing room)
- 5-8 scene beats, each 1-3 sentences
- First sentence = hook. Stops the scroll in <2 sec.
- Faceless: no "I" in personal mode. UTB uses storyteller voice. FGM uses teacher voice. AIC uses analyst voice.
- No Boubacar persona on UTB or FGM (faceless brands)
- AIC may reference Boubacar by name if topic warrants
- Close with single CTA OR clean takeaway. No "subscribe" beg.
- No music or SFX cues — those are added later

Format output as:
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

## Piece 8: Quote card

Write ONE quote card line (for IG/X visual) from the source using lens(es): {{lenses}}.

Source: {{source_url}}
Source excerpt: {{extracted_text}}

Constraints:
- ONE line, 6-15 words
- Either: a direct quote from the source (with attribution) OR Boubacar's compressed restatement of the source's strongest point (no fake attribution)
- The line must be self-contained — readable without context
- No clichés ("hustle harder", "live your truth", etc.)

Then provide an image prompt for kie_media (text-to-image):

Format:
```
QUOTE: <line>
ATTRIBUTION: <author name + source> OR <Boubacar restatement, no attribution>
IMAGE_PROMPT: <60-100 word kie_media prompt — describe scene, lighting, mood, palette aligned with channel brand>
PALETTE: <hex codes from channel brand>
```

---

## Piece 9: Newsletter section

Write ONE newsletter section (200-400 chars) for The Forge weekly newsletter using lens(es): {{lenses}}.

Topic: {{key_claim}} + {{unique_angle}}
Source: {{source_url}}

Constraints:
- 200-400 characters
- Section starts with a 5-8 word headline
- Body is one tight paragraph: the insight + one specific example or number + one takeaway
- Cite source with link
- Voice: Boubacar's analyst-with-skin-in-the-game tone. Not breezy. Not academic.

Format:
```
HEADLINE: <5-8 words>
BODY: <200-400 char paragraph including (source: <url>)>
```

Return only the formatted section.

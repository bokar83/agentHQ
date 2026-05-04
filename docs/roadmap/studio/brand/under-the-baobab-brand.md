# Under the Baobab - Brand Bible

**Channel:** Under the Baobab
**Locked:** 2026-05-03, Studio M2 build session
**Niche:** African folktales + original African children's tales
**Audience:** African children, diaspora families, parents wanting African cultural representation

---

## Name & Tagline

**Channel name:** Under the Baobab
**Show tagline:** *"Stories from the roots."*
**End-card sign-off:** *"Until next time - under the baobab."*
**YouTube About hook:** "Where African stories come alive. Folktales, fables, and original tales from across the continent - told the way they were meant to be heard."

---

## Color Palette

Inspired by the baobab tree itself at dusk: the bark, the sky behind it, the kente cloth draped across its roots, the savanna earth. Warm, alive, layered - not flat. African sunset energy without being cliché.

| Role | Name | Hex | Use |
|------|------|-----|-----|
| Primary | Saffron Gold | `#E8A020` | Wordmark, CTAs, kente accent stripe, subscribe button |
| Secondary | Baobab Indigo | `#3D2B8E` | Night sky backdrops, deep scene color, text on light bg |
| Accent 1 | Terracotta Fire | `#C45E2A` | Storytelling warmth, chapter labels, highlight beats |
| Accent 2 | Savanna Amber | `#F5C842` | Children's content pop, joyful moments, shimmer effect |
| Text / Grounding | Bark Brown | `#2C1A0E` | Body text, dark overlays, grounding anchor |
| Background | Cream Parchment | `#FAF3E0` | Light mode bg, title cards, paper texture feel |
| Surface Dark | Dusk Mauve | `#1E1433` | Dark mode card surfaces, night scene panels |

**Palette logic:** Saffron Gold is the heartbeat - sun, kente, fire. Baobab Indigo is the depth - the sky behind every story, the unknown beyond the village. Terracotta is the earth, the clay pot, the griot's robe. Never cold. Never corporate.

**Hard rules:**
- No pure black `#000000` - use Bark Brown for depth
- No red - Terracotta Fire is warm orange-brown, categorically distinct from red
- Gold + Indigo is the power pair; never swap either for a neutral substitute in hero elements

---

## Typography

| Role | Font | Weight | Notes |
|------|------|--------|-------|
| Wordmark / Channel name | Playfair Display | Bold (700) | Serif. Regal. "Griot carrying wisdom." |
| Episode title / H1 | Playfair Display | Semibold (600) | Consistent with wordmark family |
| Body / subtitle | DM Sans | Regular / Medium | Clean contrast to serif. Accessible. |
| Chapter label / cultural tag | Cinzel Decorative | Regular | Ancient carved feel. Use sparingly - episode openings, culture tags only. |

**Font pairing logic:** Playfair serif carries weight of oral tradition. DM Sans keeps it readable for kids and parents. Cinzel is the ceremonial layer - the moment before the story begins.

**Google Fonts URLs:**
- Playfair Display: `https://fonts.google.com/specimen/Playfair+Display`
- DM Sans: `https://fonts.google.com/specimen/DM+Sans`
- Cinzel Decorative: `https://fonts.google.com/specimen/Cinzel+Decorative`

---

## Motion Vocabulary

**Pacing principle:** The griot is unhurried. Motion serves the story, never competes with it.

| Element | Spec |
|---------|------|
| Still image movement | Ken Burns slow drift - 3-5 sec, scale 1.0→1.08, slight direction shift per scene |
| Parallax depth | Foreground moves 1.3× relative to background layer |
| Story transition | Soft cross-dissolve + 1-frame black gap (candlelight flicker effect) |
| Text reveal | Fade-up, `0.4s ease-out`, 20px vertical travel |
| Intro sting | Baobab silhouette grows from seedling - 3 sec, Saffron Gold fill on Dusk Mauve bg |
| Outro / end-card entry | Left-to-right curtain wipe in Bark Brown, 0.6s, reveals end-card |
| Chapter title card | Cinzel text fades in center, holds 2s, dissolves to scene |
| Cultural tag stamp | Terracotta Fire rectangle slides in from left, holds 1.5s, slides out |

**Never use:** Jump cuts, fast zoom, flash transitions, motion blur effects. Griot energy only.

---

## Voice Identity

**Persona name:** Griot Kofi
**Gender:** Male
**Character:** Warm West African baritone. Unhurried. Storytelling register, not news anchor. Feels like a real person around a fire, not a voice assistant.
**Vendor:** ElevenLabs (primary)
**Voice IDs (locked):**

- Male narrator (Griot Kofi): `U7wWSnxIJwCjioxt86mk`
- Female narrator (alt): `D9xwB6HNBJ9h4YvQFWuE`

**Fallback:** Kai TTS via kie_media - lowest pace setting, warmest available voice
**SSML notes:**

- Slow down 10% on character names (especially unfamiliar African names)
- Slight pause before story moral moments (`<break time="0.6s"/>`)
- Never rush scene transitions - natural breath between paragraphs

**Pronunciation dictionary:** Build per-story for names; Wolof, Akan, Yoruba, Bamileke phonetics logged per episode in Pipeline DB

**Parenting Psychology niche (Pillar 2) voice note:** Use female narrator `D9xwB6HNBJ9h4YvQFWuE` as default for parenting-psychology content. Maternal warmth fits the "safety and connection" angle better than Griot Kofi baritone. Elhadja `Kpr3bkxYd7gPcHKxBohV` for elder wisdom moments in either pillar. Source of truth: `configs/voice_registry.json`.

---

## Logo Spec

**Concept:** Baobab silhouette (iconic upside-down-root shape) as primary icon. Wordmark "Under the Baobab" in Playfair Display Bold, Saffron Gold on dark bg / Baobab Indigo on light bg.

**Image generation prompt (kie_media / Imagen):**
> "Minimalist logo icon of an African baobab tree silhouette, upside-down root shape, solid Saffron Gold (#E8A020) fill on transparent background, clean vector style, no gradients, no text, centered composition, square crop"

**Wordmark layout:** Icon left, "Under the Baobab" stacked right (two lines: "Under the" small / "Baobab" large). Alternate: single-line horizontal for banner use.

**Minimum clear space:** 1× icon height on all sides
**Do not:** Add drop shadows, texture overlays, or gradients to the icon mark

---

## Avatar (YouTube Channel Icon)

**Size:** 800×800px (displays at 98×98 on desktop, 176×176 on profile page)
**Design:** Baobab icon centered on Dusk Mauve `#1E1433` background. Saffron Gold icon, slight inner glow `#F5C842` at 20% opacity. No wordmark at this size - icon only.

**Image generation prompt:**
> "Square channel avatar, African baobab tree silhouette icon, centered, Saffron Gold (#E8A020) on deep dark purple-blue (#1E1433) background, minimal clean vector style, slight warm gold inner glow, no text, no gradients, crisp edges"

---

## Banner (YouTube Channel Art)

**Size:** 2560×1440px - safe zone for all devices: central 1546×423px
**Layout:**
- Full-width African savanna dusk scene: deep Dusk Mauve sky, silhouetted baobab trees at horizon
- Saffron Gold kente-stripe band along bottom 80px
- Channel name "Under the Baobab" in Playfair Display Bold, Cream Parchment, centered in safe zone
- Tagline below name: *"Stories from the roots."* in DM Sans Regular, Savanna Amber `#F5C842`
- Subtle Adinkra symbol pattern (low opacity, 8%) as texture in upper-left and lower-right corners

**Image generation prompt (background scene):**
> "Wide cinematic African savanna at dusk, silhouettes of baobab trees against a deep indigo-violet sky (#3D2B8E to #1E1433 gradient), warm saffron gold light at horizon (#E8A020), no people, painterly semi-realistic style, horizontal composition 16:9, no text"

---

## End-Card Template

**Duration:** Last 20 seconds of every video
**Layout (16:9):**

```
┌─────────────────────────────────────────────────┐
│ [Kente stripe top - Saffron Gold, 6px]          │
│                                                  │
│  🌳 [Baobab icon, animated, center-left]        │
│     "Under the Baobab"  [Playfair, Cream]       │
│     "Stories from the roots."  [DM Sans, Amber] │
│                                                  │
│  [SUBSCRIBE - Terracotta Fire btn, Cream text]  │
│                              [Video tile right] │
│                                                  │
│ [Kente stripe bottom - Saffron Gold, 6px]       │
└─────────────────────────────────────────────────┘
```

**Background:** Dusk Mauve `#1E1433`
**Baobab animation:** Silhouette fades in from center, 2s ease, slight scale 0.9→1.0
**Subscribe CTA text:** "More Tales →"
**Font sizes (1920px reference):** Channel name 48px, tagline 22px, subscribe label 18px

---

## Thumbnail Template Grammar

**Layout:** Dark bg (Dusk Mauve or scene-matched) + centered scene image + bold episode title bottom-left

**Color zones:**
- Title text: Saffron Gold or Cream Parchment (depending on bg darkness)
- Bottom gradient bar: Bark Brown `#2C1A0E` at 80% opacity, full width, 120px tall

**Text rules:**
- Episode title: Playfair Display Bold, max 4 words, min 64px
- No more than 2 text elements on any thumbnail
- Scene image always occupies 70%+ of thumbnail area

**Do not:** White title cards, generic stock photo backgrounds, clip-art illustrations

**Per-video generation:** This template defines the style grammar only. M3 generates a unique thumbnail per video with episode-specific title, stat/hook, and background scene. No two thumbnails are identical.

---

## About Copy (YouTube)

```
Where African stories come alive.

Folktales, fables, and original tales from across the continent - Akan, Wolof, Yoruba, Mande, Bamileke, and beyond. Told the way they were meant to be heard: around the baobab, under the stars.

New stories every week. Built for African children, diaspora families, and anyone who wants to hear the continent's voices.

Subscribe. Pull up a root. Story time is starting.
```

**X / Twitter bio (160 chars max):**
`African folktales & original stories for children + diaspora. New tales every week. Pull up a root. 🌳`

---

## Production Crew Brand Injection

Add this block to every M3 script generation prompt for this channel:

```
CHANNEL: Under the Baobab
VOICE: Griot Kofi - warm West African baritone, unhurried, storytelling register
PALETTE: Saffron Gold (#E8A020), Baobab Indigo (#3D2B8E), Terracotta Fire (#C45E2A)
VISUAL STYLE: Ken Burns on still images, parallax depth, soft cross-dissolve transitions
REGION TAG: [REQUIRED - specify cultural origin of this tale]
CULTURAL RULE: If retelling a published tale, cite source. Original tales flagged explicitly.
TONE: Entertainment, not ethnography. Feel alive.
```

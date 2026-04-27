---
name: signal-works-pitch-reel
description: >
  Generates a Signal Works pitch reel video from website demo screenshots.
  Auto-generates niche-specific copywriting, builds a HyperFrames composition,
  renders the MP4, uploads to Google Drive, and logs to the Notion Content Board.
  Trigger when user provides a screenshots folder path and a niche name.
  Niches supported: roofer, pediatric dentist, hvac (extend as needed).
---

# Signal Works Pitch Reel Skill

Takes a folder of demo site screenshots and produces a finished pitch reel MP4
ready to embed on the demo site. Zero manual prompting after the first call.

---

## When to invoke

User says any of:
- "make a pitch reel for [niche]"
- "build the Signal Works video for [niche]"
- "screenshots are in [path], create the reel"
- Running the full Signal Works pipeline for a new niche

---

## Inputs

| Input | Required | Notes |
|---|---|---|
| `screenshots_folder` | Yes | Absolute path to folder containing numbered PNGs |
| `niche` | Yes | `roofer`, `pediatric dentist`, or `hvac` - drives copy + color |
| `demo_site_url` | No | If provided, logged to Notion entry |
| `output_folder` | No | Defaults to `d:/Ai_Sandbox/agentsHQ/output/websites/signal-works-demo-<niche>/` |

Screenshots must be named `01-hero.png`, `02-services.png`, `03-trust.png`, `04-cta.png`.
Optional: `05-stats.png` (inserted between hero and services if present).

---

## Step 1 - Inventory screenshots

List files in `screenshots_folder`. Determine shot order:
- If `05-stats.png` exists: order is 01, 05, 02, 03, 04
- Otherwise: order is 01, 02, 03, 04

Read each image file (Claude can view PNGs) and note:
- Dominant background color (used for letterbox)
- Key visual element per shot (used to anchor copy)

---

## Step 2 - Select niche config

Look up the niche in this table. This drives copy tone, accent color, bg color,
and music register.

| Niche | Accent color | BG letterbox | Tone | Music |
|---|---|---|---|---|
| `roofer` | `#F4600C` orange | `#111111` charcoal | Urgent, industrial, bold | Steady, confident, low energy |
| `pediatric dentist` | `#F5C842` gold | `#0B1F3A` deep navy | Warm, parent-facing, reassuring | Light, warm, optimistic |
| `hvac` | `#E8A020` amber | `#0B1422` dark navy-black | Emergency-trustworthy, urgent | Low, steady, slightly tense |

---

## Step 3 - Generate copy

Write one text overlay per shot using the templates below.
Substitute `[CITY]` with the city from context (default: Salt Lake City).
Mark one key phrase per slide for accent color highlight - wrap it in `**double asterisks**`
in your working notes so you know which span gets the accent color CSS.

### Copy templates by niche

**roofer:**
- Shot 01 (hero): "When a homeowner asks ChatGPT for a roofer in [CITY] - do they **find you**?"
- Shot 05 (stats, if present): "The numbers prove the work. **AI still can't see it.**"
- Shot 02 (services): "Most roofers in [CITY] are **invisible to AI search.** Their calls are going elsewhere."
- Shot 03 (trust): "Your reviews exist. **AI just can't find them yet.**"
- Shot 04 (CTA): Line 1 (large, accent color): "**Signal Works**" / Line 2: "We make your business the one AI recommends."

**pediatric dentist:**
- Shot 01 (hero): "When a parent asks ChatGPT for a pediatric dentist in [CITY] - does your **name come up**?"
- Shot 02 (services): "Most pediatric dentists in [CITY] are **invisible to AI search.** Their patients are finding someone else."
- Shot 03 (trust): "Parents find dentists through ChatGPT and Perplexity now. **Not Google. Not Yelp.**"
- Shot 04 (CTA): Line 1 (large, accent color): "**Signal Works**" / Line 2: "We make your practice the one AI recommends."

**hvac:**
- Shot 01 (hero): "Your furnace breaks at midnight. A homeowner asks ChatGPT for help. Do they **find you**?"
- Shot 05 (stats, if present): "The numbers prove the work. **AI still can't see it.**"
- Shot 02 (services): "Most HVAC companies in [CITY] are **invisible to AI**. Their calls are going elsewhere."
- Shot 03 (trust): "**[N] five-star reviews.** Still invisible on ChatGPT. We fix that." (replace N with actual review count visible in screenshot)
- Shot 04 (CTA): Line 1 (large, accent color): "**Signal Works**" / Line 2: "We make your business the one AI recommends."

---

## Step 4 - Build HyperFrames composition

Run the `hyperframes` skill. Build a composition with these hard rules - never deviate.

### IMAGE RULES (non-negotiable)

- Every screenshot: `object-fit: contain` - NEVER `cover`, `fill`, or `crop`
- Letterbox bands use the niche BG color from Step 2
- All four (or five) edges of every screenshot must be fully visible in the rendered frame
- Video dimensions: 1920x1080 (16:9)
- Screenshots are typically ~1780x800px - they letterbox ~140px top and bottom at 1920x1080. That is correct.

### TEXT OVERLAY RULES (non-negotiable)

Every text overlay must:

1. **No containers, no pills, no boxes.** Text sits directly over the image. Legibility comes from a layered text-shadow halo, not a background element:
   `text-shadow: 0 0 20px rgba(0,0,0,0.9), 0 0 40px rgba(0,0,0,0.7), 0 2px 4px rgba(0,0,0,0.95)`
   This creates a soft dark glow that makes white text readable on any background without any visible box.
2. **Mixed color:** the highlighted phrase (marked with `**` in Step 3) renders in the niche accent color. All other text is white `#FFFFFF` or light gray `#E8E8E8`
3. **Varied position:** each shot places text in a different screen region. Use this rotation:
   - Shot 1: bottom-left (10% from left, 12% from bottom)
   - Shot 2: top-right (55% from left, 8% from top)
   - Shot 3 (or 5 if stats present): bottom-center (centered, 8% from bottom)
   - Shot 4 (trust): top-left (6% from left, 8% from top)
   - Shot 5 (CTA): center, lower third (centered horizontally, 62% from top)
4. **Varied entrance animation:** each shot uses a different GSAP entrance - never the same two in a row:
   - Shot 1: words slide in from left edge, staggered 0.12s, ease-out
   - Shot 2: container scales from 90% to 100% + fade-in, duration 0.5s
   - Shot 3: container rises 25px from rest + fade-in, duration 0.5s, ease-out
   - Shot 4: container slides in from right edge, ease-out, duration 0.4s
   - Shot 5: line 1 slides up from 40px below (0.5s), line 2 fades in 0.7s after line 1

### TIMING

| Shot | Duration | Transition in |
|---|---|---|
| 01 hero | 4-5 sec | Fade from black |
| 05 stats (if present) | 3 sec | Slide up |
| 02 services | 3 sec | Slide up |
| 03 trust | 4 sec | Slide left |
| 04 CTA | 5 sec | Fade in, hold 3s, fade to black |

Total target: 17-22 seconds.

### MUSIC

Use a royalty-free instrumental track matching the niche tone from Step 2.
Keep volume low (background, not foreground). Never use dramatic cinematic swells.

### CURSOR

If any screenshot shows the HyperFrames cursor dot, note it in output
but do not block render - the cursor is small and acceptable.

---

## Step 5 - Render

Use the `hyperframes-cli` skill to render the composition.

Output file naming:
```
signal-works-<niche-slug>-pitch-reel-<YYYY-MM-DD>.mp4
```
Example: `signal-works-roofer-pitch-reel-2026-04-27.mp4`

Save to `output_folder` (default: `d:/Ai_Sandbox/agentsHQ/output/websites/signal-works-demo-<niche>/`).
Also save as `pitch-reel.mp4` in the same folder (canonical name for the demo site embed).

---

## Step 6 - Upload to Google Drive

Upload the rendered MP4 to Drive folder `05_Asset_Library/02_Videos/` (ID: `1jvdSp0GggQi6-7o4WkS5Q-Jv3F1tjqE5`).

File name on Drive:
```
CONTENT_SignalWorks_deliverable_<YYYY-MM-DD>_<niche-slug>-pitch-reel
```
Example: `CONTENT_SignalWorks_deliverable_2026-04-27_roofer-pitch-reel`

Use the gws CLI or Drive MCP tool. Return the shareable Drive URL.

---

## Step 7 - Log to Notion Content Board

Create a new entry in the Notion Content Board (`FORGE_CONTENT_DB`: `339bcf1a-3029-81d1-8377-dc2f2de13a20`).

Fields to set:
- **Name:** `Signal Works [Niche] Pitch Reel - [YYYY-MM-DD]`
- **Status:** `Draft`
- **Platform:** `Other` (or Video if available)
- **Drive Link:** the Drive URL from Step 6 (this field is type `url`, NOT `Drive URL`)
- **Notes / Draft:** brief description - "HyperFrames pitch reel for Signal Works [niche] demo. [N] shots, [duration]s. Demo site: [demo_site_url if provided]"

Use the Notion MCP tool (`notion-create-pages`) or the orchestrator Notion client.

---

## Step 8 - Report

Return a summary:
```
Pitch reel complete.
Niche: [niche]
Shots: [N]
Duration: [X]s
Local: [output_path]/pitch-reel.mp4
Drive: [drive_url]
Notion: entry created in Content Board
Demo site embed: add <video src="pitch-reel.mp4" autoplay muted loop playsinline> to hero section
```

---

## Extending to new niches

To add a new niche:
1. Add a row to the niche config table in Step 2
2. Add copy templates to Step 3
3. No other changes needed - the rest of the pipeline is niche-agnostic

Current supported niches: `roofer`, `pediatric dentist`, `hvac`
Next likely niches: `chiropractor`, `landscaper`, `painter`

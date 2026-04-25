# Skool harvest 2026-04-25 , full proposal archive (R56-R60)

This is the complete proposal list from the deep-read pass on the first
5 R-series harvested lessons. Some items are scheduled for Tier 1 / Tier 2
(see the live Notion DB and the session handoff). The rest are parked here
because the underlying patterns are real and may become useful later.

Don't delete this file. When agentsHQ grows or the situation changes
(first paid Catalyst Works client, Studio scaling beyond one channel,
Figma-bearing prospect arrives, etc.) come back here and lift the
relevant pattern.

**Source artifacts** (extracted from the Skool zips, gitignored under
`workspace/skool-harvest/`):
- R60 cinematic-sites-agent-kit-master/
- R59 (root)
- R58 R58_Antigravity+Figma/
- R57 r57-template-community/
- R56 creative-engine-template/

Treat all "Antigravity" references in the source lessons as Claude Code
or Codex (functionally equivalent runtime).

---

## R60 , Cinematic Sites Agent Kit

Verdict in summary: **Absorb pattern + steal prompts** (per deep read).
Tier in this session: **Tier 3 (defer)** , vanity build before 5+ outreach
runs have happened.

### Ideas captured

1. **30-effect cinematic-modules library** as `skills/cinematic-modules/`,
   callable from clone-builder + 3d-website-building.
2. **HARD RULES top-of-file block** for every paid-action skill (mirrors
   memory rules but baked into the skill body).
3. **Pause Points table** as evaluation gates inside each skill.
4. **Cost Check before paid API calls** ("Ready to proceed? This will cost
   approximately $X.").
5. **Module library as localhost service pattern** , curl
   `http://localhost:{PORT}/{slug}` at build time instead of inlining.
6. **Lessons Learned appendix** with each numbered learning tied to the
   failure that produced it.
7. **Industry → module selection table** (7-row matrix mapping industry
   to recommended module).
8. **Canvas + JPEG frame sequence pattern** for hero scrub (over
   `<video>.currentTime`, which keyframes-only on compressed MP4 and
   visibly stutters).

### Verbatim files worth stealing later

- `cinematic-sites-agent-kit-master/.claude/skills/cinematic-sites/SKILL.md`
  , 670-line single-file skill, best example of self-contained
  website-build skill.
- Hero canvas JS block at SKILL.md lines 57-117.
- CSS hard rules at lines 22-42 (no vignettes, individual backdrop pills,
  text-shadow-only on h1).
- 7 module-pattern code snippets at lines 489-588 (3D tilt, magnetic
  button, cursor glow, spotlight border, text mask, odometer, kinetic
  marquee, zoom parallax, accordion, text scramble).
- `cinematic-site-components/index.html` , visual hub previewing all 30
  effects.
- `examples/ikea-roomcraft/index.html` , 584-line reference build.

### When to revisit

- After 5+ Catalyst Works prospects have received a rebuilt website via
  the Tier 1 outreach loop. At that point a "premium tier" with cinematic
  scroll-stop becomes a differentiator vs the simpler single-file output.
- For Studio: when a faceless channel has its own brand site that
  benefits from premium hero animation.

---

## R59 , Beautiful Websites Agent Toolkit

Verdict in summary: **Absorb pattern + steal prompts**. Tier in this
session: **Tier 1** (the outreach loop is the highest revenue lever).
Most items below are part of Tier 1; a few are parked.

### Ideas captured (full list)

1. **`skills/site-qualify/`** , visual quality grader for clone-scout /
   prospect output. **Tier 1.**
2. **Verbatim port `prompts/website_prompt_v1.md`** to
   `skills/clone-builder/templates/single_file_premium.md`. **Tier 1.**
3. **Verbatim port `scripts/screenshot.js`** to `agentsHQ/scripts/`.
   **Tier 1.**
4. **Design-combo build-log** (10×10×5 = 500 unique palette/font/layout
   combos memory) so clone-factory sites don't look like siblings.
   **Tier 2** (Expansionist flagged this as the seed of an episodic-memory
   layer, bigger than anti-collision , see archive entry below).
5. **Photo URL verification before commit** (HTTP 200 check before using
   any Unsplash URL). **Tier 1** (folds into clone-builder).
6. **Pause-by-default pipeline with `--auto` opt-out**. **Tier 2.**
7. **Cost-approval contract baked into CLAUDE.md / SKILL.md**. **Tier 1**
   (cost-confirmation decorator in kie_media).
8. **Apify actor + filter rules for local-business contact data**
   (`lukaskrivka~google-maps-with-contact-details`, with chains/Yelp/
   Facebook URL filter). **Tier 2** , extends `niche-research` for local
   biz outreach.
9. **Single-file HTML + CDN-only architecture rule** as a "tier-0
   deliverable" for outreach assets vs full Next.js for paid clients.
   **Tier 1** (used by the outreach loop).

### Verbatim files worth stealing

All under
`a46692f435ea4e8a9acee396a683bb69/downloads/extracted/`:

- `prompts/website_prompt_v1.md` (155 lines) , single-file premium HTML
  spec.
- `scripts/screenshot.js` (120 lines) , robust Playwright screenshot.
- `.agent/skills/site-qualify/SKILL.md` lines 86-104 , 11-row visual
  rubric.
- `.agent/skills/apify-scrape/SKILL.md` lines 49-101 , actor + field map.
- `.agent/workflows/beautiful-websites.md` , pipeline shape.

### Studio angle

R59 itself is not a Studio fit (Studio runs faceless content channels,
not website outreach). But: the **build-log episodic-memory pattern** IS
relevant to Studio , same primitive that prevents two-sibling clone sites
also prevents two-sibling LinkedIn posts, two-sibling Studio videos, two
near-duplicate weekly briefs. Park here; consider when Studio scales
past one channel.

---

## R58 , Antigravity + Figma Mobile Apps

Verdict in summary: **Steal prompts only**. Tier in this session:
**Tier 3 (defer)** , register the Figma MCP only when first
Figma-bearing client appears.

### Ideas captured

1. **`skills/figma/SKILL.md`** as a dormant skill (zero-cost install).
2. **`.claude/commands/figma.md`** , Option A/B/C dispatcher pattern
   (Figma→Code / Code→Figma / Setup).
3. **UI quality contract block** (Lucide-only, Unsplash with mandatory
   dark-gradient overlay, never emoji-as-icon) , lift into
   `skills/frontend-design/` as a non-negotiable section.
4. **MCP-setup-with-USER-MUST-DO pattern** , document at
   `docs/playbooks/mcp-setup-pattern.md`. Reusable for every external
   MCP we ever add (Stripe, Sentry, Qdrant, GA4...).
5. **Subagent + slash-command pairing** for the same capability ,
   meta-pattern for any agentsHQ skill where auto-trigger sometimes
   misfires.

### Verbatim files worth stealing

All under
`e5d1861eb3bf4f9abb2fade668045231/downloads/extracted/`:

- `.claude/agents/figma.md` , copy almost verbatim into
  `agentsHQ/skills/figma/SKILL.md`.
- `.claude/commands/figma.md` , copy as `agentsHQ/.claude/commands/figma.md`.
- `tools/figma-setup.md` , install runbook (`claude mcp add --scope user
  --transport http figma https://mcp.figma.com/mcp`).
- Quality-rules block (Icons / Photography / Stars sections, lines
  85-110 of agents/figma.md).

### Studio angle

Studio could use Figma if it ever sources designs from Figma community
files (some viral design files live there). Probably not soon. Skip the
example HTML apps , they are one-shot phone mockups, not a component
library.

### When to revisit

- First Catalyst Works client whose existing brand assets live in Figma.
- First Studio channel that wants Figma-templated thumbnails.

---

## R57 , Antigravity x Blotato Marketing Agent

Verdict in summary: **Absorb pattern + steal prompts**. Tier in this
session: **mostly Tier 2** (campaign-mode after Studio's manual proof),
with brand file format and prompt-best-practices in **Tier 1**.

### Ideas captured

1. **30-day campaign workflow** grafted onto `orchestrator/griot.py` as
   "campaign mode": brand file gate → Notion Content Board batch (30
   records) → review checkpoint → kie_media batch → review checkpoint
   → Telegram one-tap publish. **Tier 2 high** (when Studio has 5
   manually-approved posts to validate the engine).
2. **Round 1-4 Steven-Bartlett brand interview** (10 questions, 4
   rounds) installed as the canonical interview engine inside
   `skills/client-intake/` AND `skills/brand/`. **Tier 2** for Catalyst
   Works (need a booked Signal Session first; method-acting otherwise).
   **Tier 1** for Studio (can run on Studio channels today).
3. **`[entity]_BRAND.md` template** standardized across CW + Studio.
   Two real samples banked. **Tier 1**.
4. **Cost-confirmation HARD RULE decorator** added to kie_media. **Tier 1.**
5. **Two-method brand discovery** (Interview vs Content Analysis via
   Firecrawl) wired into client-intake. **Tier 2 high** for Catalyst
   Works (auto-pre-fill brand file from existing client website),
   **Tier 2 high** for Studio (auto-derive brand voice from already-published
   pieces of a faceless channel).
6. **Modal cron pattern** ("RSS → process → publish daily" autopilot
   with `processed.json` idempotency). **Tier 3** , agentsHQ already
   has heartbeat-driven griot on VPS; this is a reference for atlas
   autonomy.

### Verbatim files worth stealing

All under
`0cd9312abdf3430593d09498bb7942cf/downloads/extracted/r57-template-community/`:

- `.agent/AGENT.md`
- `.agent/workflows/30-day-campaign.md` (the gold) , Round 1-4 interview
  at lines 24-46.
- `.agent/workflows/generate-content.md`
- `.agent/workflows/youtube-to-linkedin.md`
- `.agent/skills/blotato_best_practices/SKILL.md` , Blotato URL-passthrough
  decision tree, base64 PowerShell upload, platform-specific posting
  fields, scheduling timezone reference.
- `.agent/skills/modal_deployment/SKILL.md`
- `references/docs/prompt-best-practices.md` (the OTHER gold) , BOPA,
  SEALCaM, dialogue cap rule, 9-element character prompt skeleton.
- `references/docs/fabric_BRAND.md` and `imma_BRAND.md` , sample
  brand files for `docs/reference/brand-file-examples/`.

### Studio angle (sharper than the original verdict)

R57 is **the Studio playbook** if you ignore the Antigravity-as-tool
noise:

- The Round 1-4 brand interview produces the brand file every Studio
  channel needs.
- The 30-day campaign workflow is what Studio runs, manually today.
- The cost-gate rule prevents kie_media surprise bills.
- The prompt-best-practices content (BOPA, SEALCaM) is the prompt
  library for character-consistent Studio content.
- The `[channel]_BRAND.md` shape is the input contract the Studio
  manual workflow already produces , this just standardizes it.

### Catalyst Works angle

The Round 1-4 interview becomes the first 30 minutes of a Signal
Session. Output: a polished `[client]_BRAND.md` artifact handed over at
session end , turns $497 session into a tangible takeaway, makes SHIELD
upsell easier, gives every downstream Catalyst engagement a shared
brand-truth file. **Method-acting before any Signal Session is booked.**
Bank now, deploy when first session is on the calendar.

---

## R56 , Antigravity Creative Engine

Verdict in summary: **Steal prompts only** , R56 is a strict subset
of R57. Tier: **Tier 1** for the gated `/generate-content` command
pattern (per Boubacar's call , promote into Tier 1 after Studio
build).

### Ideas captured

1. **7-step gated `/generate-content` slash command**. **Tier 1**
   (after Studio build). Shape: gather inputs → analyze refs → upload to
   Kie → create Notion Content Board records first → cost gate →
   generate images → user approves → write video prompts → cost gate
   → generate videos.
2. **Multi-provider abstraction** (`tools/providers/google.py`,
   `tools/providers/kie.py`, `tools/providers/wavespeed.py`) , already
   covered by `docs/reference/cross-vendor-fallback-pattern.md` from
   the prior session.

### Verbatim files worth stealing

Under
`410db1af99764d0f9c0f9034ebdd068f/downloads/extracted/creative-engine-template/`:

- `.claude/commands/generate-content.md` , the 7-step gated command.
- `references/docs/prompt-best-practices.md` , same as R57's; one
  canonical copy in `docs/reference/`.

### Studio angle

The 7-step gated `/generate-content` is **the canonical Studio command**.
Once Studio has produced a few manual runs, codify them through this
slash command so the manual workflow becomes one-shot.

---

## Cross-cutting (across all 4 lessons)

### The "agentsHQ skill template" we don't have

Every Antigravity/Claude-Code template ships SKILL.md files in the
same shape:

1. Frontmatter (name, description)
2. **HARD RULES** block at top , non-negotiable invariants
3. **When to use / when NOT to use**
4. Workflow steps with **Pause Points table** (human checkpoints)
5. **Cost Check** rule before any paid action
6. Output contract / file shapes
7. **Lessons Learned** appendix tied to scars

agentsHQ skills vary in shape. The Council recommended NOT doing a
51-skill retrofit sweep (massive editing burden, no revenue lever).
**Codify the template in `skills/boubacar-skill-creator/SKILL.md`** so
**new** skills inherit it, and retrofit existing skills only when they
are touched for a real reason. **Tier 2 low**.

### The "scoped creative engine" insight (Expansionist)

R56 + R57 are not two lessons. They are the same engine at two scopes:

- **Studio**: 30-day campaign scope (the R57 workflow).
- **Boubacar's content board**: 1-week scope (a possible new griot
  mode).
- **Catalyst Works engagement-ops**: 1-deliverable scope (a SHIELD
  artifact build).

One engine, three scopes. **Tier 2 medium** , informs how griot evolves
once Studio's manual proof is done.

### The "build-log as episodic memory" insight (Expansionist)

R59's design-combo build-log is the seed of a real memory primitive:

- Same pattern prevents ctq-social writing two LinkedIn posts with the
  same opener in a week.
- Same pattern prevents boub_voice_mastery reusing the same anecdote
  across articles.
- Same pattern prevents griot generating two campaigns with overlapping
  pillars.

This is a candidate **Phase 4 / Phase 5 token-economy companion** ,
content state across runs, not just LLM cost. **Tier 2 high** if Studio
scales past one channel.

### The "MCP install runbook template" insight

R58 produced the only true reusable install pattern: USER-MUST-DO
markers in the setup file, two-actor flow (agent does X, user does Y,
wait for confirmation), `claude mcp add` one-liner. **Tier 1 low** ,
zero-cost doc to create at `docs/playbooks/mcp-setup-pattern.md`.
Future MCPs reuse it.

---

## Provenance

- Council ran twice on this batch (2026-04-25). Second pass cut the
  list from 25 items to ~5 Tier 1 items.
- Each archived item below Tier 2 has a "When to revisit" trigger.
- Source lessons live in `workspace/skool-harvest/robonuggets/` and
  remain harvestable.

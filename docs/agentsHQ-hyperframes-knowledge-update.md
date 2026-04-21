# agentsHQ Knowledge Update . Hyperframes Video Production Capability

## Date: April 2026 | Status: NEW CAPABILITY . NOT YET INTEGRATED

---

## WHAT THIS DOCUMENT IS

This is a structured knowledge injection for agentsHQ. It introduces a new
production capability (Hyperframes video generation), maps it to existing
agents and skills, defines integration points, and specifies exactly what
should and should not be built in Phase 0.

Drop this into your agentsHQ system context, Claude Code session, or any
agent that needs to understand this capability.

---

## SECTION 1 . WHAT IS HYPERFRAMES

Hyperframes is an open-source framework by HeyGen that converts plain HTML
into deterministic, frame-by-frame rendered video. It is not a drag-and-drop
tool. It is not a video editor. It is a code-driven video production pipeline
designed explicitly for AI agent use.

**How it works:**

1. Author a composition as a plain HTML file using GSAP for animation and
   `data-*` attributes for timing.
2. Preview in browser with `npx hyperframes preview` (live reload, no build step).
3. Render to MP4 or WebM with `npx hyperframes render -o output.mp4` via
   headless Chrome + FFmpeg.

**Why it matters for this stack:**
LLMs already speak HTML. This means any agent in agentsHQ can generate,
iterate, and render video without specialized tooling or a human touching
a timeline editor. The composition is just a file. The render is just a
CLI command. This is the missing output format for leGriot and for
Catalyst Works client deliverables.

**Key constraint:** Hyperframes produces video files (MP4, WebM). It does
not animate live websites. These are distinct use cases. Do not conflate them.

---

## SECTION 2 . TECHNICAL REQUIREMENTS

```
Node.js 22+       . runtime for CLI and dev server
FFmpeg            . video encoding
npm or bun        . package manager
Docker (optional) . for deterministic, reproducible CI renders

CLI commands:
  npx hyperframes init my-video     . scaffold project
  npx hyperframes preview           . browser preview with hot reload
  npx hyperframes render -o out.mp4 . render to MP4
  npx hyperframes lint              . structural validation
  npx hyperframes validate          . runtime error check (JS, assets, contrast)
```

**Skills installation (for Claude Code / Cursor / Codex):**

```
npx skills add heygen-com/hyperframes
```

This registers three slash commands:

- `/hyperframes` . composition authoring (HTML structure, timing, captions, TTS, transitions)
- `/hyperframes-cli` . CLI commands
- `/gsap` . GSAP animation API, timelines, easing

Always invoke `/hyperframes` at the start of any composition task.

---

## SECTION 3 . HARD RULES (NON-NEGOTIABLE IN EVERY COMPOSITION)

Every agent generating a Hyperframes composition must honor these. Breaking
any of them produces incorrect or non-deterministic renders.

1. Register every GSAP timeline on `window.__timelines`. The renderer cannot
   seek animations it does not know about.
2. All `<video>` elements must be `muted`. Audio routes through separate
   `<audio>` elements for proper mixing.
3. No `Math.random()` anywhere. Use a seeded PRNG (mulberry32 or similar)
   if pseudo-randomness is needed. Random values break determinism.
4. GSAP timeline construction is synchronous. No `async`/`await` or `fetch()`
   during setup.
5. Every timed element needs: `class="clip"` plus `data-start`, `data-duration`,
   `data-track-index`.
6. Every scene gets an entrance animation. No elements appearing un-animated.
7. Every scene boundary gets a transition. No unintentional jump cuts.

---

## SECTION 4 . VOCABULARY (MAPS NATURAL LANGUAGE TO GSAP SETTINGS)

Agents should use this vocabulary in prompts so the framework picks the correct
GSAP configuration automatically.

**Motion easing:**
| Say this   | GSAP ease      | Feels like              |
|------------|----------------|-------------------------|
| smooth     | power2.out     | Natural deceleration    |
| snappy     | power4.out     | Quick and decisive      |
| bouncy     | back.out       | Overshoots then settles |
| springy    | elastic.out    | Oscillates into place   |
| dramatic   | expo.out       | Fast start, long glide  |
| dreamy     | sine.inOut     | Slow, symmetrical       |

**Timing shorthand:**

- fast = 0.2s (energy)
- medium = 0.4s (professional)
- slow = 0.6s (luxury)
- cinematic = 1 to 2s

**Caption tones:**
| Tone        | Typography          | Animation    | Size range |
|-------------|---------------------|--------------|------------|
| Hype        | Heavy weight        | Scale-pop    | 72-96px    |
| Corporate   | Clean sans-serif    | Fade + slide | 56-72px    |
| Tutorial    | Monospace           | Typewriter   | 48-64px    |
| Storytelling| Serif               | Slow fade    | 44-56px    |
| Social      | Rounded, playful    | Bounce       | 56-80px    |

**Transitions by energy:**
| Energy | CSS option      | Shader option      |
|--------|-----------------|---------------------|
| Calm   | Blur crossfade  | Cross-warp morph   |
| Medium | Push slide      | Whip pan           |
| High   | Zoom through    | Glitch, ridged burn|

**Audio-reactive intensity:**

- Text elements: 3 to 6 percent
- Background elements: 10 to 30 percent

**Audio bands to visual properties:**

- Bass -> scale (pulse on the beat)
- Treble -> glow (shimmer intensity)
- Amplitude -> opacity (breathing)
- Mids -> shape (morphing)

**TTS voices (Kokoro, no API key needed):**
| Content type  | Recommended voices           |
|---------------|------------------------------|
| Product demo  | af_heart, af_nova            |
| Tutorial      | am_adam, bf_emma             |
| Marketing     | af_sky, am_michael           |

**Render quality:**

- draft . fast iteration
- standard . review and feedback
- high . final delivery

---

## SECTION 5 . STANDARD COMPOSITION BRIEF TEMPLATE

Every Hyperframes video production task must supply these inputs. Agents
must stop and ask if any field is missing. Do not guess.

```
- Purpose: [what this video is for and where it will be published]
- Duration: [e.g., 15s, 30s, 45s]
- Aspect ratio: [16:9 landscape | 9:16 vertical | 1:1 square]
- Mood/style: [e.g., minimal Swiss grid, warm analog, high-energy social]
- Brand palette: [hex values with usage caps . e.g., primary #00B7C2, accent #FF7A00 max 10%]
- Typography: [body font, heading font]
- Key scenes/elements: [title card, lower third, captions, background footage, logo, etc.]
- Audio: [none | music at assets/path.mp3 | TTS with voice preference]
- Caption tone: [Hype | Corporate | Tutorial | Storytelling | Social]
- Transitions: [energy level or mood description]
- Asset paths: [exact file paths for any media . do not invent paths]
```

**Output format every composition agent must produce:**

1. Complete HTML composition in a fenced code block. Nothing elided.
2. Exact CLI render command in a second fenced code block.
3. Two sentences explaining motion and transition choices for iteration.
4. If brief is ambiguous or underspecified: stop and ask. Do not guess
   brand colors, durations, or copy.

---

## SECTION 6 . ANTI-PATTERNS (DO NOT DO THESE)

- Do not output React or Vue components. Hyperframes is plain HTML.
- Do not request 4K or 60fps unless explicitly instructed. Defaults are
  1920x1080 at 30fps. Higher specs slow rendering meaningfully.
- Do not skip the `/hyperframes` slash command in Claude Code sessions.
  Without it, the agent guesses at HTML video conventions instead of
  using the framework's actual rules.
- Do not paste long error logs into prompts without running lint first.
  Run `npx hyperframes lint` then `npx hyperframes validate` before
  escalating to the agent.
- Do not invent asset paths. If a media file is needed and no path is
  provided, flag it and stop.
- Do not auto-render without a brief review step. Draft renders are fast.
  Use them. Save high-quality renders for final delivery.

---

## SECTION 7 . INTEGRATION MAP: EXISTING AGENTS AND WHERE HYPERFRAMES FITS

### leGriot (social media agent . deferred until agentsHQ fully live)

**Current scope:** Text-only. Extracts quotes and ideas, drafts and posts
content in Boubacar's voice to LinkedIn and X. Personal, not client-facing.

**Hyperframes addition:**
leGriot gains a video output layer. This must be designed into leGriot's
architecture now, not retrofitted later.

The updated leGriot workflow:

1. Idea or quote captured via Telegram brain dump inbox.
2. leGriot drafts hook copy in Boubacar's voice.
3. leGriot passes the brief to a Hyperframes composition task.
4. Hyperframes agent generates the HTML composition.
5. CLI renders to a 9:16 MP4 (standard quality for draft, high for publish).
6. Video returned to Boubacar via Telegram for approval before posting.
7. On approval: post to LinkedIn or X with caption copy already drafted.

**Default video spec for leGriot outputs:**

- Aspect ratio: 9:16 vertical (LinkedIn and TikTok native)
- Duration: 15 to 30 seconds
- Caption tone: Social (bouncy, rounded, playful)
- Transitions: Medium energy (push slide)
- TTS: optional, off by default unless narration is in the brief

**Architecture note:** The Hyperframes task is a sub-task spawned by
leGriot's orchestrator. It is not a standalone agent. leGriot owns the
content decision. Hyperframes is the production tool.

---

### Catalyst Works Consulting Deliverables (Phase 1 capability . do not build in Phase 0)

**Current scope:** Post-call artifact is a written document designed to
circulate inside client organizations.

**Hyperframes addition:**
Add a 45-second animated findings brief video as an optional deliverable
layer on top of the written artifact. Not a replacement. An addition.

The findings brief video format:

- Duration: 30 to 60 seconds
- Aspect ratio: 16:9 (boardroom and email-forward friendly)
- Scenes: 3 to 5 key findings, one per scene, with a closing CTA
- Caption tone: Corporate (clean sans-serif, fade + slide)
- Transitions: Calm (blur crossfade)
- Audio: TTS narration with professional male or female voice
- Brand palette: client-specific or Catalyst Works palette per engagement

**Why this matters:**
A video that a client forwards internally is a referral vehicle. It has
Boubacar's name on it. It markets the practice every time it moves. The
written artifact stays internal. The video escapes the building.

**Phase gate:** Do not build this until after first revenue. The constraint
in Phase 0 is generating clients, not producing new deliverable formats.
File this as a Phase 1 build item.

---

### Sankofa Council (strategic pressure-testing layer)

No direct Hyperframes integration needed. The Council reviews decisions and
deliverables, not production pipelines. However:

If the Council is ever convened to review a video brief before production,
the Contrarian voice should specifically challenge:

- Is this the right format for this message?
- Is a video actually better than a tight written post here?
- Does the production complexity justify the output?

The default answer to "should we make a video?" is not automatically yes.

---

### Outreach Agent (cold email . manual execution in Phase 0)

No Hyperframes integration. Outreach is text-only. Video in cold outreach
is a Phase 2 or Phase 3 consideration at the earliest.

---

## SECTION 8 . WHAT TO BUILD NOW vs LATER

**Phase 0 (current) . build nothing:**

- Learn the Hyperframes vocabulary and rules (done via this document).
- Add Hyperframes to leGriot's architecture spec.
- Note the consulting deliverable video format in the Phase 1 backlog.
- Do not install, scaffold, or render anything during Phase 0.
  The constraint is first revenue. Not infrastructure.

**Phase 1 (after first revenue):**

- Install Hyperframes on agentsHQ VPS alongside existing Docker stack.
- Build the leGriot video output layer using the workflow defined in Section 7.
- Test with one real post: social hook video, 15 seconds, 9:16.

**Phase 2:**

- Add the consulting findings brief video to the Constraint Diagnostic Sprint
  deliverable package.
- Automate the render pipeline so Boubacar only approves via Telegram.
- Add to Manual Fallback Protocol as Protocol 5 (Video Production).

---

## SECTION 9 . MANUAL FALLBACK PROTOCOL ADDITION (to be added to agentsHQ-manual-fallback-protocols.md in Phase 1)

```
## PROTOCOL 5: VIDEO PRODUCTION (Hyperframes)

Primary: agentsHQ leGriot video sub-task via Hyperframes CLI on VPS
Fallback: Claude Code session with /hyperframes skill + local render

Pre-flight checklist:
- [ ] Brief is complete (all fields in Section 5 of Hyperframes knowledge doc)
- [ ] Asset paths are verified and files exist at those paths
- [ ] Node.js 22+ and FFmpeg are installed on render machine
- [ ] /hyperframes skill is loaded in agent session

Quality checklist:
- [ ] All 7 hard rules honored (see Section 3)
- [ ] Draft render reviewed before high-quality render
- [ ] Human approval via Telegram before any video is posted or sent
- [ ] No auto-publish. Human-in-the-loop at all times.

Fallback path:
1. Open Claude Code locally
2. Run: npx skills add heygen-com/hyperframes
3. Prompt with /hyperframes and the full brief from Section 5
4. Preview: npx hyperframes preview
5. Render: npx hyperframes render -o output.mp4
6. Review and post manually

Time estimate: 20 to 40 minutes for a 15 to 30 second draft render.
```

---

## SECTION 10 . RESOURCES

- Docs: https://hyperframes.heygen.com/introduction
- Prompt guide: https://hyperframes.heygen.com/guides/prompting
- GSAP animation: https://hyperframes.heygen.com/guides/gsap-animation
- Component catalog (50+ blocks): https://hyperframes.heygen.com/catalog
- GitHub: https://github.com/heygen-com/hyperframes
- Common mistakes: https://hyperframes.heygen.com/guides/common-mistakes

---

## DOCUMENT STATUS

| Field       | Value                                    |
| ----------- | ---------------------------------------- |
| Created     | April 2026                               |
| Author      | Catalyst Works / agentsHQ                |
| Phase gate  | Phase 0 (knowledge only, no build yet)   |
| Next review | Phase 1 kickoff (after first revenue)    |
| File name   | agentsHQ-hyperframes-knowledge-update.md |
| Location    | /home/agentshq/docs/                     |

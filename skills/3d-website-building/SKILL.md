---
name: 3d-website-building
description: >
  Builds premium 3D animated scroll-driven websites by chaining 4 skills in sequence:
  website-intelligence (competitive research + HTML report), image-generator (3 AI
  prompts for scroll-stop assets), 3d-animation-creator (Next.js + Framer Motion build),
  and seo-strategy (final audit). Produces a complete deliverable set: competitive
  analysis report, copyable asset prompts, Next.js project, and SEO/accessibility audit.
  Trigger when the user says "3D website", "animated website", "scroll animation site",
  "scrollytelling", "Apple-style website", "premium animated site", "3D scroll",
  "build me a 3D site", or provides a video/images and wants a scroll-driven build.
allowed-tools: Read, Write, Grep, Glob, Bash, WebFetch
---

# 3D Website Building — Intelligence-to-Delivery Pipeline

You build premium scroll-driven animated websites by running four skills in sequence.
Each skill produces a deliverable. The whole pipeline runs in one session.

All source skills are in `D:/Ai_Sandbox/agentsHQ/skills/`:
- `website-intelligence/SKILL.md` — competitive research + HTML report
- `image-generator/SKILL.md` — AI image/video prompts
- `3d-animation-creator/SKILL.md` — Next.js scroll-driven build
- `seo-strategy/SKILL.md` — SEO + accessibility audit

---

## Before You Start: Check Tools

Confirm Firecrawl is connected (look for `mcp__firecrawl__scrape` in your tools).
If not connected, fall back to WebFetch for individual URLs — note this limits competitor
discovery but the rest of the pipeline still works.

---

## Step 0: Interview (MANDATORY — do not skip)

Ask these questions before touching any code or doing any research:

1. **Client website URL** — "Do you have an existing website I should start from? (I'll scrape it for brand assets)"
2. **Business type and niche** — "What kind of business is this for? (e.g., luxury watch brand, pool cleaner, SaaS product)"
3. **Scroll animation subject** — "What should the scroll animation show?
   - A product assembling/deconstructing (e.g., a watch revealing its internals)
   - A before→after transformation (e.g., dirty pool → crystal clean)
   - A product exploding into components (e.g., sneaker breaking into layers)"
4. **Background color** — "What background color? (dark works best — default is #050505)"
5. **Accent color** — "What's your primary accent color? (hex or describe it)"
6. **Overall vibe** — "What feel? (e.g., Apple/luxury tech, bold DTC brand, minimal SaaS, premium automotive)"

Once you have answers, proceed phase by phase.

---

## Phase 1: Competitive Intelligence

**Follow the `website-intelligence` skill (read skills/website-intelligence/SKILL.md for full details).**

Run the 4-phase intelligence process:
1. Scrape client's existing site → extract brand colors, fonts, messaging
2. Find top 5 competitors via Firecrawl search
3. Deep-scrape top 3 → extract design patterns, CTAs, content structure
4. Synthesize: what do top sites share? What gaps exist?

Save research brief to `research/01-intelligence-brief.md`.

Build the **competitive analysis HTML report**:
- Warm paper tone (#f6f4f0 background, #c45d3e accent)
- Instrument Serif headings + DM Sans body (Google Fonts)
- Competitor profiles with color swatches, scores, strengths
- @media print rules for PDF export
- Save as `competitive-analysis.html`

**HARD STOP — show the intelligence brief and ask: "Ready to build the 3D site based on this research?"**
Do not proceed until the user approves.

---

## Phase 2: Asset Prompts

**Follow the `image-generator` skill (read skills/image-generator/SKILL.md for full details).**

Generate 3 coordinated prompts based on the animation subject:

**PROMPT 1 — START FRAME (hero/assembled/before)**
Pure solid background matching the site background color (default #050505).
Product centered, slight natural tilt. Soft studio lighting. 16:9. Apple/luxury DTC aesthetic.

**PROMPT 2 — END FRAME (exploded/after)**
For products: cinematic exploded view, components floating on a clear axis.
For transformations: dramatic after-state. Same background, same lighting. 16:9. No text/labels.

**PROMPT 3 — GOOGLE FLOW (video transition)**
Smooth cinematic transition Prompt 1 → Prompt 2. Mid-rotation pose, components build
progressively. Energy effect midway. Ultra-sharp. 5-6 seconds. 16:9.
Works in Kling, Higgsfield, Runway, or Pika.

Deliver in `asset-prompts.html` (tabbed page, one-click copy) and `asset-prompts.md`.

Tell the user:
> "Use Prompt 1 in your image generator (16:9, 2K, 4 generations).
> Use Prompt 2 the same way, optionally referencing Prompt 1 as a style reference.
> Use Prompt 3 in your video model with Prompt 1 as start frame, Prompt 2 as end frame.
> When ready, drop the video into the project — I'll extract frames and wire it up."

---

## Phase 3: Build the 3D Website

**Follow the `3d-animation-creator` skill (read skills/3d-animation-creator/SKILL.md for full details).**

If the user has a video file, extract frames with FFmpeg:
```bash
mkdir -p site/public/sequence
ffmpeg -i "{VIDEO_PATH}" -vf "fps=30,scale=1920:-2" -q:v 2 "site/public/sequence/frame_%04d.webp"
```
Target 60-120 frames. Use WebP for smaller files.

**Tech Stack (mandatory):**
- Next.js 14 (App Router)
- Tailwind CSS
- Framer Motion
- HTML5 Canvas
- TypeScript

**Core scroll mechanic:**
```typescript
// components/ScrollCanvas.tsx
'use client'
import { useEffect, useRef, useState } from 'react'
import { useScroll, useSpring } from 'framer-motion'

const FRAME_COUNT = 120  // adjust to actual frame count

export default function ScrollCanvas() {
  const containerRef = useRef<HTMLDivElement>(null)
  const canvasRef = useRef<HTMLCanvasElement>(null)
  const frames = useRef<HTMLImageElement[]>([])
  const [loaded, setLoaded] = useState(false)
  const [progress, setProgress] = useState(0)

  const { scrollYProgress } = useScroll({ target: containerRef })
  const smoothProgress = useSpring(scrollYProgress, { stiffness: 100, damping: 30 })

  useEffect(() => {
    let loadedCount = 0
    const imgs: HTMLImageElement[] = []
    for (let i = 0; i < FRAME_COUNT; i++) {
      const img = new Image()
      img.src = `/sequence/frame_${String(i).padStart(4, '0')}.webp`
      img.onload = () => {
        loadedCount++
        setProgress(Math.round((loadedCount / FRAME_COUNT) * 100))
        if (loadedCount === FRAME_COUNT) setLoaded(true)
      }
      imgs.push(img)
    }
    frames.current = imgs
  }, [])

  useEffect(() => {
    return smoothProgress.on('change', (v) => {
      const canvas = canvasRef.current
      if (!canvas || !loaded) return
      const ctx = canvas.getContext('2d')
      if (!ctx) return
      const idx = Math.min(Math.floor(v * (FRAME_COUNT - 1)), FRAME_COUNT - 1)
      const img = frames.current[idx]
      if (!img) return
      const dpr = window.devicePixelRatio || 1
      canvas.width = window.innerWidth * dpr
      canvas.height = window.innerHeight * dpr
      ctx.scale(dpr, dpr)
      const scale = Math.max(
        window.innerWidth / img.naturalWidth,
        window.innerHeight / img.naturalHeight
      )
      const x = (window.innerWidth - img.naturalWidth * scale) / 2
      const y = (window.innerHeight - img.naturalHeight * scale) / 2
      ctx.drawImage(img, x, y, img.naturalWidth * scale, img.naturalHeight * scale)
    })
  }, [smoothProgress, loaded])

  if (!loaded) {
    return (
      <div className="fixed inset-0 flex flex-col items-center justify-center bg-[#050505]">
        <div className="w-48 h-1 bg-white/10 rounded-full overflow-hidden">
          <div className="h-full bg-white transition-all duration-100" style={{ width: `${progress}%` }} />
        </div>
        <p className="text-white/40 text-sm mt-3">Loading</p>
      </div>
    )
  }

  return (
    <div ref={containerRef} style={{ height: '400vh' }}>
      <canvas ref={canvasRef} className="sticky top-0 w-full h-screen" style={{ background: '#050505' }} />
    </div>
  )
}
```

**Scrollytelling beats** — populate with real content from the brief:
```typescript
// Opacity transforms in app/page.tsx
const beatA = useTransform(scrollYProgress, [0, 0.10, 0.18, 0.20], [0, 1, 1, 0])
const beatB = useTransform(scrollYProgress, [0.25, 0.35, 0.43, 0.45], [0, 1, 1, 0])
const beatC = useTransform(scrollYProgress, [0.50, 0.60, 0.68, 0.70], [0, 1, 1, 0])
const beatD = useTransform(scrollYProgress, [0.75, 0.85, 0.93, 0.95], [0, 1, 1, 0])
```

If no video yet: create placeholder canvas div with comment `<!-- DROP FRAMES INTO /public/sequence/ -->`.

Output to `site/`:
- `site/app/page.tsx`
- `site/components/ScrollCanvas.tsx`
- `site/app/globals.css` (Tailwind base + dark custom scrollbar)
- `site/package.json` (Next.js 14, Tailwind, Framer Motion)
- `site/README.md` (setup, where to drop frames, Vercel/Netlify deploy)

---

## Phase 4: SEO and Accessibility Audit

**Follow the `seo-strategy` skill in Mode 2 (read skills/seo-strategy/SKILL.md for full details).**

Audit the generated Next.js files and fix:

**SEO:**
- `<title>` and `<meta name="description">` in `site/app/layout.tsx`
- Open Graph tags (og:title, og:description, og:type, og:image)
- JSON-LD schema markup for the business type
- Single H1, logical heading hierarchy

**Accessibility:**
- `prefers-reduced-motion` wrapping ALL Framer Motion animations
- Skip navigation link
- Focus indicators on interactive elements
- Alt text on all images

**Performance:**
- Next.js `<Image>` component for images
- Font display swap on Google Fonts

Fix everything directly. Output a numbered list of fixes applied.

---

## Delivery Checklist

Before calling this done:

- [ ] `competitive-analysis.html` — polished, print-ready, well-formed HTML
- [ ] `asset-prompts.html` — 3 prompts with copy buttons, model instructions
- [ ] `research/01-intelligence-brief.md` — competitive research saved
- [ ] `site/app/page.tsx` — real content, not Lorem ipsum
- [ ] `site/components/ScrollCanvas.tsx` — scroll-driven canvas
- [ ] `site/app/globals.css` — Tailwind base + dark scrollbar
- [ ] `site/package.json` — Next.js 14, Tailwind, Framer Motion
- [ ] `site/README.md` — setup + deploy instructions
- [ ] SEO/accessibility fixes applied

---

## Error Recovery

| Issue | Fix |
|---|---|
| Firecrawl not connected | Use WebFetch for individual URLs, skip /map |
| No video provided yet | Placeholder canvas, explain in README |
| FFmpeg not installed | `choco install ffmpeg` (Windows) / `brew install ffmpeg` (macOS) |
| Too many frames (>150) | Reduce FPS: `-vf "fps=15,scale=1920:-2"` |
| Canvas blurry | Check devicePixelRatio — must scale both canvas dimensions and ctx |
| Scroll feels too fast | Increase container height: 500vh–600vh |
| useSpring jitter | Reduce stiffness to 60, increase damping to 40 |
| Build fails | Requires Node 18+: `node --version` |

---

## Related Skills

- hyperframes: Use when the brief requires a companion video (social hook video,
  animated findings brief, product demo). Hyperframes is a sibling skill, not
  part of this skill. Invoke it independently. Do not merge HTML outputs.

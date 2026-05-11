# Composition Patterns

## Picture-in-Picture (Video in a Frame)

Animate a wrapper div for position/size. The video fills the wrapper. The wrapper has NO data attributes.

```html
<div
  id="pip-frame"
  style="position:absolute;top:0;left:0;width:1920px;height:1080px;z-index:50;overflow:hidden;"
>
  <video
    id="el-video"
    data-start="0"
    data-duration="60"
    data-track-index="0"
    src="talking-head.mp4"
    muted
    playsinline
  ></video>
</div>
```

```js
tl.to(
  "#pip-frame",
  { top: 700, left: 1360, width: 500, height: 280, borderRadius: 16, duration: 1 },
  10,
);
tl.to("#pip-frame", { left: 40, duration: 0.6 }, 30);
```

## Title Card with Fade

```html
<div
  id="title-card"
  data-start="0"
  data-duration="5"
  data-track-index="5"
  style="display:flex;align-items:center;justify-content:center;background:#111;z-index:60;"
>
  <h1 style="font-size:64px;color:#fff;opacity:0;">My Video Title</h1>
</div>
```

```js
tl.to("#title-card h1", { opacity: 1, duration: 0.6 }, 0.3);
tl.to("#title-card", { opacity: 0, duration: 0.5 }, 4);
```

## Slide Show with Section Headers

Use separate elements on the same track, each with its own time range. Slides auto-mount/unmount based on `data-start`/`data-duration`.

```html
<div class="slide" data-start="0" data-duration="30" data-track-index="3">...</div>
<div class="slide" data-start="30" data-duration="25" data-track-index="3">...</div>
<div class="slide" data-start="55" data-duration="20" data-track-index="3">...</div>
```

## Top-Level Composition Example

```html
<div
  id="comp-1"
  data-composition-id="my-video"
  data-start="0"
  data-duration="60"
  data-width="1920"
  data-height="1080"
>
  <!-- Primitive clips -->
  <video
    id="el-1"
    data-start="0"
    data-duration="10"
    data-track-index="0"
    src="..."
    muted
    playsinline
  ></video>
  <video
    id="el-2"
    data-start="el-1"
    data-duration="8"
    data-track-index="0"
    src="..."
    muted
    playsinline
  ></video>
  <img id="el-3" data-start="5" data-duration="4" data-track-index="1" src="..." />
  <audio id="el-4" data-start="0" data-duration="30" data-track-index="2" src="..." />

  <!-- Sub-compositions loaded from files -->
  <div
    id="el-5"
    data-composition-id="intro-anim"
    data-composition-src="compositions/intro-anim.html"
    data-start="0"
    data-track-index="3"
  ></div>

  <div
    id="el-6"
    data-composition-id="captions"
    data-composition-src="compositions/caption-overlay.html"
    data-start="0"
    data-track-index="4"
  ></div>

  <script>
    // Just register the timeline — framework auto-nests sub-compositions
    const tl = gsap.timeline({ paused: true });
    window.__timelines["my-video"] = tl;
  </script>
</div>
```

## Pad Sub-Composition Timelines to Master Slot Duration

**Why:** HyperFrames decides composition visibility from each sub-composition's GSAP `timeline.duration()`, NOT from the `data-duration` attribute on the master host. The runtime strips `data-duration` from non-root composition hosts (`packages/core/src/runtime/init.ts:231-246`, `:1205-1220`). If a sub-composition's timeline is shorter than its master slot, HF sets `visibility: hidden` early and the next beat hasn't started yet → black frame flash at the boundary.

**Fix:** add a no-op tween at the END of every sub-composition's timeline to extend `timeline.duration()` to match the master slot:

```js
// Pad timeline to master slot duration (e.g., 1.71s) to prevent black frames at beat tail
tl.to({}, { duration: 1.71 }, 0);
window.__timelines["flex-css"] = tl;
```

The empty-object tween animates nothing — it only extends the timeline's reported duration so HF holds the composition visible until the master slot ends.

**When to apply:** every sub-composition whose creative timeline ends before its master `data-duration`. Common in fast-cut beat sequences (sub-compositions under 2s).

**Verify in studio preview console:**

```js
const p = document.querySelector("hyperframes-player");
const iw = p.shadowRoot.querySelector("iframe").contentWindow;
Object.fromEntries(Object.entries(iw.__timelines).map(([k, v]) => [k, +v.duration().toFixed(4)]));
```

Compare each composition's reported duration against its master `data-duration` in `index.html`. Any composition where `timeline.duration() < master slot` will flash black at its tail.

Source: heygen-com/hyperframes-launch-video HANDOFF.md Session 4 (2026-04-15) — fixed 10 sub-compositions with this pattern.

## Caption Track Pattern (body-level overlay clips)

For per-line captions (LinkedIn-style title cards, lyric reveals, beat-synced subtitles): place each caption as a body-level `<div class="cap clip">` element with `data-start` + `data-duration` + a UNIQUE high `data-track-index` per caption (20+ range to avoid collision with sub-compositions). The framework treats each as an independent timed clip — auto-mounts/unmounts on its window.

```html
<style>
  .cap {
    position: absolute;
    bottom: 80px;
    left: 50%;
    transform: translateX(-50%);
    text-align: center;
    font-family: "Inter", system-ui, sans-serif;
    font-weight: 500;
    font-size: 40px;
    color: rgba(240, 235, 220, 0.92);
    background: rgba(10, 8, 5, 0.55);
    padding: 12px 28px;
    border-radius: 10px;
    backdrop-filter: blur(8px);
    z-index: 9999;
    pointer-events: none;
  }
</style>
<div class="cap clip" data-start="7.29" data-duration="1.86" data-track-index="30">HyperFrames by HeyGen.</div>
<div class="cap clip" data-start="9.10" data-duration="3.44" data-track-index="31">Agents can now write HTML and render MP4s.</div>
<div class="cap clip" data-start="12.73" data-duration="2.48" data-track-index="32">Claude Code made this launch video.</div>
```

Each caption gets its OWN track index — same-track clips can't overlap, and you usually want adjacent captions to bleed into each other slightly during a transition. `z-index: 9999` keeps them above all sub-composition content.

Source: heygen-com/hyperframes-launch-video index.html.

# Session Handoff - Signal Works Roofing Pitch Reel - 2026-04-27

## TL;DR

Built a 22-second HyperFrames prospect pitch video for the Signal Works roofing demo site. Attempted Seedance 2 first (wrong tool: hallucinates content, does not reproduce actual site). Rebuilt with HyperFrames using real screenshots. Three render iterations: fixed object-fit crop bug, then improved text overlay variety and animations. Final render is clean. Video uploaded to Drive and logged to Notion Content Board.

## What was built / changed

- `output/websites/signal-works-demo-roofing/pitch-reel/index.html`: HyperFrames composition (5 scenes, blur-crossfade + vertical-push transitions, frosted pill overlays, word-stagger on S3, scale-in on S4)
- `output/websites/signal-works-demo-roofing/pitch-reel.mp4`: final 22s rendered MP4 (3.1 MB)
- `output/websites/signal-works-demo-roofing/index.html`: hero section now has `<video>` background embed (hero-reel.mp4, discarded Seedance output, opacity 0.35) + `.hero > *:not(video)` z-index fix
- `output/websites/signal-works-demo-roofing/hero-reel.mp4`: Seedance 2 output, kept in repo but NOT the actual pitch video
- `output/websites/signal-works-demo-roofing/hero-poster.jpg`: fallback poster for video embed
- `skills/kie_media/SKILL.md`: added HARD RULE: Seedance does not reproduce actual website content
- `~/.claude/projects/.../memory/feedback_media_drive_notion_required.md`: new hard rule
- `~/.claude/projects/.../memory/feedback_hyperframes_screenshot_video.md`: new patterns memory
- `~/.claude/projects/.../memory/feedback_hyperframes_screenshot_fit.md`: updated with CSS specifics
- `~/.claude/projects/.../memory/project_kie_media_operational_facts.md`: 4 new sections added

## Decisions made

- **Seedance is NOT for prospect demos.** It hallucinates. HyperFrames is the correct tool when you need the actual site shown.
- **`object-fit: contain`** is the rule for all screenshot backgrounds in HyperFrames: never `cover`.
- **Frosted dark pill** (`rgba(10,10,10,0.72)` + border) replaces gradient bars for text overlays.
- **Alternate pill position** top/bottom across scenes to avoid same-frame monotony.
- **Drive + Notion Content Board immediately after render**: not at session end. Notion row created: `34fbcf1a-3029-81b3-ab3e-cc9f15a48c04`.

## What is NOT done

- The hero video embed (`hero-reel.mp4`) on the main site is the Seedance output which has watermarked/hallucinated footage. It was left in because removing it wasn't requested, but it should probably be replaced with the `pitch-reel.mp4` or removed entirely.
- The pitch-reel is not yet embedded on the demo site itself: it's a standalone file for direct sharing.
- No audio/music track added to pitch-reel (was not requested).

## Open questions

- Should `pitch-reel.mp4` replace or supplement `hero-reel.mp4` as the hero video embed on the site?
- Does the pitch-reel need a music bed before sharing with prospects?
- Any other Signal Works demo sites (dental?) need the same pitch-reel treatment?

## Next session must start here

1. Decide fate of `hero-reel.mp4` embed on index.html: replace with pitch-reel or remove the video embed entirely
2. Check if dental demo site needs a matching pitch-reel
3. If adding music, use `npx hyperframes tts` / add `<audio>` element with royalty-free track

## Files changed this session

```
output/websites/signal-works-demo-roofing/
  index.html                    (hero video embed added)
  hero-reel.mp4                 (Seedance output, new)
  hero-poster.jpg               (new)
  pitch-reel.mp4                (new, final)
  pitch-reel/
    index.html                  (HyperFrames composition)
    01-hero.png ... 04-cta.png  (new, copied screenshots)

skills/kie_media/SKILL.md       (Seedance HARD RULE added)

memory/
  feedback_media_drive_notion_required.md    (new)
  feedback_hyperframes_screenshot_video.md   (new)
  feedback_hyperframes_screenshot_fit.md     (updated)
  project_kie_media_operational_facts.md     (4 new sections)
  MEMORY.md                                  (index updated)
```

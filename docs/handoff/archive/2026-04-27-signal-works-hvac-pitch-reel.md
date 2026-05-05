# Session Handoff - Signal Works HVAC Pitch Reel - 2026-04-27

## TL;DR
Built a 19-second HyperFrames pitch reel for the Signal Works HVAC demo site (Summit Comfort Systems). Rendered twice: first with frosted pill containers around text, then stripped to floating text with drop-shadow per Boubacar's request. Final render is clean, lint-clear, 0 errors.

## What was built / changed

- `output/websites/signal-works-demo-hvac/pitch-reel/index.html` :  4-scene HyperFrames composition
- `output/websites/signal-works-demo-hvac/pitch-reel/hyperframes.json` :  config (copied from roofing)
- `output/websites/signal-works-demo-hvac/pitch-reel/meta.json` :  metadata
- `output/websites/signal-works-demo-hvac/pitch-reel/01-hero.png` through `04-cta.png` :  source screenshots
- `output/websites/signal-works-demo-hvac/pitch-reel.mp4` :  2.8 MB, 19s, 1920x1080, 30fps
- `output/websites/signal-works-demo-hvac/pitch-reel-thumbnail.png` :  extracted at t=2.5s (Scene 1 peak)

## Decisions made

- **No pill containers**: Boubacar overrode the frosted box rule. Floating text + strong drop-shadow is now the HVAC pattern. Future reels: render with pill first, remove on request.
- **Fonts**: Barlow Condensed 700/900 (display, mechanical urgency) + Space Grotesk 400 (CTA tagline). Both compiled from Google Fonts by the HyperFrames engine.
- **Accent color**: `#E8A020` amber (matches HVAC demo site palette).
- **Duration**: 19s. Scene timing: S1 0-5s, S2 5-8.4s, S3 8.4-12.9s, S4 12.9-19s.
- **Transitions**: vertical push (S1->S2), horizontal push left (S2->S3), blur crossfade (S3->S4).
- **Four distinct entrance animations**: word stagger from right / rise+fade / scale 85%->100% / slide up from 40px.

## What is NOT done

- HVAC demo site is NOT deployed to Vercel (only local at `output/websites/signal-works-demo-hvac/`)
- Pitch reel is NOT uploaded to Drive or logged in Notion Content Board (media-drive-notion rule was not applied this session)
- No audio/music track in the reel (spec called for background music but HyperFrames audio was out of scope)

## Open questions

- Should the HVAC demo site be deployed to Vercel alongside dental and roofing?
- Should the HVAC pitch reel go to the Content Board / Drive like other media assets?

## Next session must start here

1. Deploy HVAC demo site to Vercel: `output/websites/signal-works-demo-hvac/` -> GitHub repo `bokar83/signal-works-demo-hvac` -> Vercel
2. Upload `output/websites/signal-works-demo-hvac/pitch-reel.mp4` to Drive (Signal Works folder) and log in Notion Content Board
3. If building more niches: use the HVAC reel structure as template (4 scenes, no pills, floating text + drop-shadow, same timing scaffold)

## Files changed this session

```
output/websites/signal-works-demo-hvac/
  pitch-reel/
    index.html          <- new composition
    hyperframes.json    <- copied
    meta.json           <- copied
    01-hero.png         <- copied from workspace/
    02-services.png     <- copied from workspace/
    03-trust.png        <- copied from workspace/
    04-cta.png          <- copied from workspace/
  pitch-reel.mp4        <- rendered (final, no boxes)
  pitch-reel-thumbnail.png <- extracted at t=2.5s

memory/project_signal_works_demos.md    <- added HVAC entry
memory/feedback_hyperframes_screenshot_video.md  <- added Rule 6 (pill optional)
memory/feedback_hyperframes_screenshot_fit.md    <- updated container rule
memory/MEMORY.md        <- updated two pointers
```

# Session Handoff: Seedance 2 Reference-to-Video Enhancement: 2026-04-26

## TL;DR

Short session. Boubacar brought in a third-party `seedance-skill` repo (from RoboNuggets/Skool) for installing Seedance 2.0 via Fal AI. Before installing anything, verified that Seedance 2 was already in the Kie stack at rank-4 of `text_to_video`. Determined the real gap was not API access but the multi-screenshot reference-to-video pipeline (liquid glass promo aesthetic). Added `generate_promo_video()` to `kie_media.py` plus tool wiring, with no new credentials needed.

## What was built / changed

- `orchestrator/kie_media.py`: Added `MODEL_REGISTRY["reference_to_video"]` (Seedance 2 only, no ladder) + `SEEDANCE_LIQUID_GLASS_TEMPLATE` string + `_build_seedance_prompt()` helper + `generate_promo_video()` public function. Updated `__all__`.
- `orchestrator/tools.py`: Added `generate_promo_video as _kie_generate_promo_video` to import block + `KieGeneratePromoVideoTool` class + added to `MEDIA_TOOLS` list.
- `docs/kai_model_registry.md`: New "Promo Video (reference-to-video) Models" section documenting the entry point, budget ceiling ($3.50 auto-approve), and golden rule.
- `skills/kie_media/SKILL.md`: Updated function signatures block with `generate_promo_video()` signature, added routing table (promo vs standard video), added `kie_generate_promo_video` to tools list.
- Both Python files SCP'd to VPS `root@72.60.209.109` and verified present via SSH grep.

## Decisions made

- **No Fal AI account needed.** Seedance 2 is already accessible via Kie (`bytedance/seedance-2`). The third-party skill was not installed.
- **Separate entry point, not merged into `generate_video()`.** Seedance reference-to-video is a distinct aesthetic and API call shape (multi-image `imageList`). Merging would muddy the routing logic.
- **No fallback ladder for reference_to_video.** Seedance is the only Kie model with this capability. On failure: report clearly, don't fall back to a different aesthetic.
- **Key input field is `imageList`** (the Kie unified jobs input key), not `image_urls` (that's the Python function/tool parameter name). Future debugging note.
- **Budget ceiling set at $3.50 auto-approve** (covers the 10s production sweet spot at $3.03 with margin).

## What is NOT done (explicit)

- The `imageList` field name has not been empirically verified against the Kie API. It's the best inference from the Kie unified jobs pattern. If the first real call fails, the most likely fix is checking the exact field name Kie expects for multi-image Seedance input (could be `image_urls`, `images`, `referenceImages`).
- No test run against the live API has been performed this session.
- The `docs/kai_model_registry.md` "Last audit" date was not updated (still shows 2026-04-21): minor.

## Open questions

1. **What is the exact Kie API field name for multi-image Seedance input?** `imageList` is the best inference but must be confirmed on first live call. Check Kie docs or run a cheap Fast/480p test.
2. **Should reference_to_video get its own Kie credits budget ceiling in `kie_media.py`?** Currently only image ($0.20) and video ($2.00) ceilings are enforced. A $3.50 promo ceiling should probably be codified.

## Next session must start here

1. Run a cheap test: call `generate_promo_video()` with 2-3 screenshots of any app, `duration_hint="4"`, Fast tier if possible. Check if `imageList` is accepted or if Kie rejects with a field error.
2. If `imageList` fails, grep Kie docs or check the Kie dashboard for the correct multi-image field name and update `_build_seedance_prompt()` in `kie_media.py`.
3. After first successful call, update `docs/kai_model_registry.md` "Last audit" date and note the verified field name.

## Files changed this session

```
orchestrator/kie_media.py       : reference_to_video registry + generate_promo_video()
orchestrator/tools.py           : KieGeneratePromoVideoTool + MEDIA_TOOLS update
docs/kai_model_registry.md      : new Promo Video section
skills/kie_media/SKILL.md       : function sigs + routing table + tools list
docs/handoff/2026-04-26-seedance-kie-enhancement.md : this file
```

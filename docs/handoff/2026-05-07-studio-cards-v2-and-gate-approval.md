# Session Handoff — Studio Cards v2 + Gate Approval Mechanism — 2026-05-07

## TL;DR

Two threads, both shipped. **Thread 1:** rebuilt all 6 Studio brand intro/outro MP4s on HyperFrames v0.5.0-alpha.15 with GPT Image 2 cinema backgrounds, channel_id-prefixed filenames, longer durations (4s/5s, was 1s/1s) — replaces stale 1s placeholders inherited from May 4 work. **Thread 2:** discovered Gate's "Tap to approve" Telegram message was vaporware (no callback, no command), built `/gate-approve <branch>` and `/gate-reject <branch>` slash commands with marker-file pattern, also fixed Gate's conflict detector to ignore line-ending-only false positives (CRLF vs LF). Tested end-to-end: held branch → marker dropped → next tick processed approval → merged to main. Branch reconciliation along the way: `feature/social-media-daily-analytics` archived under `archive/` prefix after determining its 1 unique commit was identical content to `feat/sever-notion-crm-sync`.

## What was built / changed

### Studio cards v2 (workspace/studio-cards/ — gitignored)

- `package.json`: hyperframes pinned `0.4.44 → 0.5.0-alpha.15`. v0.5.3 is GitHub-only, npm has alpha line.
- `index.html`: 27s root composition stitching 6 cards (4s intro + 5s outro per brand) at 1080×1920
- `compositions/ai_catalyst_intro.html` — Convergence Spark motion (ember pulse → particle inhale → flare detonation → wordmark bloom)
- `compositions/ai_catalyst_outro.html` — black-rises-behind-wordmark fade
- `compositions/first_generation_money_intro.html` — Cloth and Compounding (coin stack rise + gradual sparkline)
- `compositions/first_generation_money_outro.html` — pure black coordinated fade
- `compositions/under_the_baobab_intro.html` — Galaxy Awakening (zoom-out + stars + shooting star + letter-by-letter wordmark)
- `compositions/under_the_baobab_outro.html` — bg holds with words then both fade together (no overlay, brightness 0.45 floor — silhouette stays visible)
- `assets/bg_{catalyst,1stgen,baobab}.jpg` — 3 GPT Image 2 cinema backgrounds (replaces older May 4 versions)
- `channel_cards/{ai_catalyst,first_generation_money,under_the_baobab}_{intro,outro}.mp4` — 6 rendered MP4s
- `channel_cards/_archive/` — old short-named MP4s preserved (per "never delete" rule)
- `compositions/_archive/` — old HTML comps preserved

### Brand configs (configs/ — git-tracked)

- `brand_config.ai_catalyst.json`: durations 1→4/5, intro_template `catalyst_intro` → `ai_catalyst_intro`, outro likewise
- `brand_config.first_generation_money.json`: same pattern, templates renamed `firstgen_*` → `first_generation_money_*`
- `brand_config.under_the_baobab.json`: same pattern, templates renamed `baobab_*` → `under_the_baobab_*`
- `docker cp` to orc-crewai container required (configs baked by Dockerfile COPY, per existing memory rule)

### Gate (orchestrator/)

- `gate_agent.py:_files_differ()` — new helper. Runs `git diff --quiet --ignore-all-space --ignore-blank-lines` between two branches for an overlapping file. Only flags as conflict if real content diverges (not line-ending-only).
- `gate_agent.py:_detect_conflicts()` — now calls `_files_differ` per overlap. Logs "content matches -- not a conflict" when false positive caught.
- `gate_agent.py:_check_approval()` + `_approval_marker_path()` — reads markers from `data/gate_approvals/`, consumes on use (single-use), returns `approve` / `reject` / `pending`.
- `gate_agent.py:gate_tick()` — high-risk path now checks marker first; instructions text rewritten from "Tap to approve" (vaporware) to "Reply '/gate-approve <branch>' to approve, '/gate-reject <branch>' to discard."
- `handlers_commands.py:_cmd_gate_approve()` + `_cmd_gate_reject()` — slash commands with `OWNER_TELEGRAM_CHAT_ID` auth gate. Write JSON marker to `data/gate_approvals/`. Async — return immediately, work happens on Gate's next tick.
- Both registered in `_COMMANDS` list before `_cmd_approve`/`_cmd_reject` (longer prefix wins).

### Branch hygiene

- `feature/social-media-daily-analytics` archived → `archive/feature-social-media-daily-analytics-2026-05-07` (Gate skips `archive/` prefix per `SKIP_PREFIXES` config). 1 unique commit content-identical to sever branch (CRLF/LF only).
- `feat/sever-notion-crm-sync` reconciled with social branch via merge, then merged to `main` twice (once via bypass script after dogfooding, once via the new approval mechanism).

### Memory

- New: `reference_hyperframes_v0_5_install.md` (alpha-only on npm, install on VPS not Windows due to SSL)
- New: `reference_gate_handoff_protocol.md` (push [READY] feature branches, check enable flag, slash command approval)
- New: `reference_studio_cards_v2_pipeline.md` (filenames, bind mount, render workflow on VPS)
- All 3 indexed in `MEMORY.md`. Line count: 158 (under 200 cap).

## Decisions made

- **HF v0.5.3 not on npm** — only alphas published. Used `0.5.0-alpha.15`. v0.5.3 is GitHub release tag only. User accepted alpha for this work.
- **Render path** — install + render on VPS (Linux Node 22, SSL works). Local Windows install failed `UNABLE_TO_VERIFY_LEAF_SIGNATURE`. Memory captured.
- **Single render + ffmpeg split** instead of per-comp HF render. One 27s output → 6 named MP4s via `ffmpeg -ss N -t M`. Faster than per-project init.
- **Skipped 9:16 + 16:9 dual render** — Studio is Shorts-first per memory. Single 1080×1920 render covers production. Future 16:9 needs separate work.
- **Studio cards v2 = no logos** — typography-forward per Boubacar feedback. Logos drop-shadowed in earlier iterations were "weird shaped" / wrong-aspected on mobile. Removed.
- **Baobab outro gets unique treatment** — no overlay, no constellation effects. Just bg + words → coordinated fade-out via `filter: brightness()`. Bg ends at 0.45 brightness so silhouette stays visible at clip cut.
- **Approval mechanism = slash command + marker file**, NOT Telegram inline button. Karpathy P2/P3: smaller scope. Async pattern doesn't block bot handler with long merge.
- **Branch reconciliation = merge social INTO sever, archive social** — "We don't delete unless truly necessary" rule. `archive/` prefix preserves history + Gate ignores via `SKIP_PREFIXES`.
- **Don't push to main directly** — coding agent protocol. Push [READY] feature branch, Gate handles merge.

## What is NOT done (explicit)

- **SW pitch reels consolidation** (variables system on `signal-works-pitch-reel` skill) — surveyed, deferred. Existing skill works; 3 demo dirs are stale outputs not active code. Memory note: A real consolidation = ~4-6h skill rewrite. Not high-leverage right now.
- **catalystworks-site v0.5 port** — `feat/hyperframes-video-sections` branch is 10+ commits stale on main since main shipped major v3 cinematic + Constraints AI rebrand. Decision needed: rebuild HF sections fresh on new v3, or skip.
- **Cold outreach personalization** — strategic use case for HF v0.5 variables, deferred. Needs its own brainstorm session (which prospects, what data, integration with outreach skill).
- **9:16 + 16:9 dual renders** for the 6 cards — only 9:16 done. If long-form ever needs 16:9 versions, re-render at that aspect.
- **Studio test of new MP4s end-to-end** — pipeline lookup verified inside container (filenames + sizes OK), but no actual Studio production run yet executed against the new assets. Will validate on next scheduled Studio render.
- **Gate approval flow load-tested** — only one branch tested through it (the dogfood test). Multi-branch concurrent approval, marker collision handling, etc. not stressed.

## Open questions

- **HF v0.5 GA timing** — when does v0.5.0 (non-alpha) hit npm? Currently on alpha.15. If GA ships with breaking changes, comp HTML may need updates. Watch GitHub releases.
- **Studio cards QA** — should there be a QA pass on the new MP4s before next Studio reel runs in production? Or trust the lint + visual previews from the localhost dogfood session?
- **Gate enable flag** — currently set to `True` (you enabled it this session). Stay enabled or revert to disabled until further work?
- **Branch cleanup cadence** — `archive/feature-social-media-daily-analytics-2026-05-07` will accumulate over time. Need a periodic cleanup routine or just let GitHub track them forever.

## Next session must start here

1. **Verify next Studio production run picks up the new branded MP4s.** Check `docker logs orc-crewai --tail 100` after next scheduled studio_render_publisher tick. Confirm: 4s intro + 5s outro present in rendered video. If not, RCA the bind-mount path.
2. **Boubacar review of the 6 new MP4s.** All on VPS at `/root/agentsHQ/workspace/studio-cards/channel_cards/`. Pull one down with `scp` to view, OR queue a dummy render through the pipeline to see them in action.
3. **Decide catalystworks-site HF sections fate.** Branch `feat/hyperframes-video-sections` is stale. Options: (a) rebuild fresh on current v3 main, (b) abandon HF on the site, (c) defer indefinitely.
4. **Decide on Gate enable flag.** It's currently ON. If staying ON: confirm cron schedule (every 15 min 9-22 + overnight checkpoints) is desired. If OFF: flip in `data/autonomy_state.json` `crews.gate.enabled = false`.

## Files changed this session

```
configs/brand_config.ai_catalyst.json                           [git]
configs/brand_config.first_generation_money.json                [git]
configs/brand_config.under_the_baobab.json                      [git]
orchestrator/gate_agent.py                                      [git]
orchestrator/handlers_commands.py                               [git]
workspace/studio-cards/index.html                               [gitignored]
workspace/studio-cards/package.json                             [gitignored]
workspace/studio-cards/compositions/ai_catalyst_intro.html      [gitignored]
workspace/studio-cards/compositions/ai_catalyst_outro.html      [gitignored]
workspace/studio-cards/compositions/first_generation_money_intro.html [gitignored]
workspace/studio-cards/compositions/first_generation_money_outro.html [gitignored]
workspace/studio-cards/compositions/under_the_baobab_intro.html [gitignored]
workspace/studio-cards/compositions/under_the_baobab_outro.html [gitignored]
workspace/studio-cards/compositions/_archive/                   [gitignored]
workspace/studio-cards/channel_cards/{6 new MP4s}               [gitignored]
workspace/studio-cards/channel_cards/_archive/                  [gitignored]
workspace/studio-cards/assets/bg_catalyst.jpg                   [gitignored]
workspace/studio-cards/assets/bg_1stgen.jpg                     [gitignored]
workspace/studio-cards/assets/bg_baobab.jpg                     [gitignored]
~/.claude/projects/.../memory/reference_hyperframes_v0_5_install.md [memory]
~/.claude/projects/.../memory/reference_gate_handoff_protocol.md    [memory]
~/.claude/projects/.../memory/reference_studio_cards_v2_pipeline.md [memory]
~/.claude/projects/.../memory/MEMORY.md                             [memory index]
docs/handoff/2026-05-07-studio-cards-v2-and-gate-approval.md       [this file]
```

## Git state at session close

| Location | Branch | HEAD |
|---|---|---|
| GitHub `main` | — | `fcf9f33` (merged via Gate dogfood approval) |
| Local | `main` | `fcf9f33` |
| VPS `/root/agentsHQ` | `main` | `fcf9f33` |
| GitHub `feat/sever-notion-crm-sync` | — | `993678b` (parent of merge) |
| GitHub `archive/feature-social-media-daily-analytics-2026-05-07` | — | `13f9f0e` (preserved) |

All synced. Working trees clean. Source Control panel empty.

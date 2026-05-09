# Session Handoff - Multiplier iter 4 shipped + pipeline fixes - 2026-05-07

## TL;DR

Long session. Started by fixing the morning Telegram pipeline ("no posts queued today" stale message + 3 silently-broken wakes since 2026-05-06 unification). Restored cadence. Fixed gkirz greeting bug across CW/SW/legacy outreach paths (36 tests). Built content_multiplier crew end-to-end across 4 iterations with Sankofa Council twice ruling against premature wiring. Iter 4 graded ~76% voice fidelity by Claude review (Boubacar's ship bar = 70-80%) so iter 4 ships. Auto-promote guardrail added: nothing auto-publishes to Boubacar's personal LinkedIn or X. M3.7.3 wiring (callbacks, heartbeat, bulk approve) deferred to next session per Sankofa.

## What was built / changed

**Morning pipeline fixes (commit 611dd2a):**
- `orchestrator/scheduler.py`, `app.py`, `publish_brief.py` — `docker cp`ed over baked `/app/` to kill the stale 7:30 publish_brief tick
- 3 silently-failed wakes restored: `story_prompt_tick.py`, `studio_story_bridge.py`, `griot_signal_brief.py` — none baked into image; `docker cp` + restart
- Queue #9 reset from `enhancing` → `pending`; Telegram re-sent (msg_id 2662)
- Trend scout cadence split: Studio niches daily Mon-Sat 5:30 MT; CW Mon/Wed/Fri 5:30 MT; Sun off (Sabbath)
- Griot morning UX: `_pipeline_summary` surfaces NEXT-day queued count when TODAY empty; cross-platform date format

**gkirz greeting fix (commit 611dd2a):**
- `skills/outreach/sequence_engine.py` — new `_looks_like_initial_plus_lastname` heuristic + 70-name cons-cons allowlist (Scott, Chris, Brian, Bryan, Kyle, Jack, Luke, Ryan, Sean...)
- `skills/outreach/outreach_tool.py` legacy path — now uses `build_body` + `_extract_first_name`, confidence-aware
- `signal_works/email_builder.py:_opening` — owner_name routes through extractor; greets only on confidence=high
- `orchestrator/tests/test_first_name_extraction.py` — 36 tests covering CW + SW + legacy paths

**Content multiplier (4 iterations, commits 611dd2a, 935d76c, a7fecfb, fc1ee3c):**
- `orchestrator/content_multiplier_crew.py` — verbatim/remix/auto modes, channel-aware piece routing, diversity penalty, cost cap, Notion writes
- `skills/content_multiplier/SKILL.md` + 4 prompt files (`lens_classifier.md`, `piece_generator.md`, `remix_classifier.md`, `remix_piece_generator.md`)
- Voice loading: `_load_skill_md` + `_load_voice_profile_with_references` reads `boub_voice_mastery/SKILL.md` + `references/brand-spine-audit.md` + `references/voice-fingerprint.md` (~13.5k chars) + `ctq-social/SKILL.md` (~12k chars). Embedded verbatim with delimiters.
- Channel routing: UTB / 1stGen = video-only faceless; AIC = full personal-piece set + video-AIC; Boubacar-personal = same minus video
- Cap = 4 pieces, lens classifier ranks via `recommended_piece_types`, crew honors
- Diversity penalty: first piece solo, rest parallel with prior-hook context; pieces returning `SKIP_NO_NEW_ANGLE` dropped
- Auto-promote guardrail: `AUTO_PROMOTE_PIECE_TYPES = {video-UTB, video-1stGen, video-AIC}` → Status=Ready. Everything else → Status=Idea.
- Title fence + label-prefix bug fixed (`_strip_code_fences` + `_LABEL_RE`)
- Path resolution handles local-dev / container-mounted / container-baked
- `orchestrator/tests/test_content_multiplier.py` — 21 tests

**FGM rename (commit 935d76c):**
- 12 active files: content_multiplier_crew, tests, studio_trend_scout, studio_story_bridge, story_prompt_tick, crews, all 4 multiplier prompts, SKILL.md, studio.md, atlas.md
- All identifiers, channel codes, prompts, tests now use `1stGen`
- CTQ filter blocks the literal 3-letter acronym (built from char-join)

**Roadmap (commit 935d76c):**
- `docs/roadmap/studio.md` — M3.7 entry with remix scope, 3-state QA verdict, cadence change

## Decisions made

1. **Iter 4 ships.** Boubacar set edit-time bar at 70-80% voice fidelity. Claude graded iter 4 ~76% (one piece B+, rest B). Per-piece edit cost ~30-60s. Net-positive draft engine. M3.7.3 wiring is the next-session work, not more voice tuning.
2. **Personal accounts firewalled from auto-publish.** AIC X = `@boubacarbarry` (his personal); AIC LinkedIn = his personal. Multiplier output to LI/X = `Status=Idea` always. Only `video-*` piece types auto-promote.
3. **FGM banned permanently.** Means female genital mutilation. Channel code, prompts, identifiers = `1stGen`. CTQ filter blocks the literal in output.
4. **Voice profile loaded as content, not reference.** Iter 1-3 had the prompt say "see skills/boub_voice_mastery/SKILL.md" — Sonnet ignored it. Iter 3+ loads body verbatim with delimiters. Pattern documented in `feedback_multiplier_voice_loading_pattern.md`.
5. **Voice fingerprint markers used sparingly.** Boubacar's correction: "I don't want to repeat the same signature phrasing every single time." Markers = signature, not boilerplate. Brand-spine anchors = context, almost never named directly.
6. **Sankofa Council ruled twice against premature wiring.** First time when proposing M3.7.3 8-step plan. Second time when proposing iter 5 voice refactor. Both were sophistication theater. Pattern: validate output BEFORE building autonomy.
7. **Cap pieces at 4.** Down from 9. Boubacar: "1-2 fine. Never force it."
8. **Trend scout: Studio daily, CW M/W/F, Sun off.** Replaces Mon-only.
9. **studio_qa_crew refactor deferred to M3.7.4.** Sankofa Contrarian flagged it as risky to bundle.

## What is NOT done (explicit)

- **M3.7.3 wiring (next session):** scout_approve callback fires multiplier; /multiply slash command; multiplier-tick heartbeat (every 5m polls Notion Status=Multiply); bulk Telegram review handler (approve all 4 in one tap); Notion schema extension (`Multiplier Run ID`, `Piece Type`, `Source Treatment`, `QA Verdict` properties)
- **studio_qa_crew refactor (M3.7.4):** 3-state verdict (passed / remix / failed), FATAL/FIXABLE failure tagging
- **Container rebuild for youtube-transcript-api:** added to requirements.txt by Codex but never installed. Defer until first YouTube source ingest is attempted; rebuild is 15-25 min and the package is only needed for YouTube path. Raw text + URL paths work today.
- **Notion records from today's manual smoke runs (run 30a2c63c, 76ff8767, 2caa8c27, a40e0338):** sit at Status=Idea with metadata-prefixed Drafts because schema doesn't have Multiplier Run ID / Piece Type / Source Treatment properties yet. Will clean up when schema lands.
- **Iter 4 smoke runs were not validated by Boubacar against actual edit time.** He approved on principle ("if it's at 70-80% I'm good") and Claude self-graded ~76%. Real edit-time test happens when M3.7.3 wires the auto-fire.
- **Anti-repetition scan across runs (not just within a run):** memory feedback notes that markers like "hidden factory" should be tracked across the LAST N runs and avoided if recent. Currently only intra-run dedup. Defer.
- **Boubacar-personal as a real channel:** today it's a piece-fit tag in lens classifier, not a Notion Channel option. When wiring scout_approve, decide whether Boubacar-personal pieces need their own Channel value or stay tagged via Platform.

## Open questions

- Studio production tick: 0 qa-passed candidates queued all day per logs. Trend scout fired (6 picks) but they sit at Status=scouted in Pipeline DB. Need to manually QA-pass at least one to test studio production end-to-end. Or wire scout_approve → multiplier so this happens automatically.
- The 3 silently-broken wakes were silent for ~24h. Should there be a daily diagnostic that greps `docker logs orc-crewai --since 24h | grep "wake registration failed"` and Telegram-alerts? Pattern recurrence likely as Codex adds more orchestrator modules.
- voice-fingerprint.md was extracted from 10 of Boubacar's posts. The Sankofa Expansionist flagged: should we use the actual posts as few-shot examples rather than only the extracted fingerprint? Defer until edit-time data shows iter 4 is actually too generic.
- AIC video script is supposed to be "a little bit more personal" per Boubacar but currently shares the same prompt as UTB / 1stGen video. Channel-conditional voice prompt was killed by Sankofa as premature. Real test: when AIC video starts shipping, see if it sounds too faceless. If yes, add light POV layer then.
- Auto_publisher fires on Status=Queued + ScheduledDate=today. griot_scheduler promotes Ready → Queued. New: video-* multiplier output writes Status=Ready. Need to verify griot_scheduler picks up these new Ready records correctly. Risk: scheduler might skip them if it expects approval-queue origin. Test in next session before relying on auto-promote in production.

## Next session must start here

1. **Verify morning ticks fired correctly.** `ssh root@72.60.209.109 "docker logs orc-crewai --since 16h 2>&1 | grep -iE 'griot_morning|publish_brief|trend_scout|story_prompt|signal_brief'"`. Confirm: (a) griot morning sent NEXT-day line at 7:00 MT, (b) NO publish_brief 7:30 msg, (c) trend scout fired Studio niches at 5:30 MT (Friday = 1stGen + UTB + AIC daily; CW M/W/F also fires Friday).
2. **Check Queue #9 disposition.** Did Boubacar tap approve / enhance / reject?
3. **Audit overnight outreach drafts for gkirz pattern.** Open Gmail drafts on `boubacar@catalystworks.consulting` and `catalystworks.ai@gmail.com`. Any "Hi <single-word-lastname>"? If zero false positives → fix is solid.
4. **Manual multiplier QA on today's scouted picks.** 6 picks (run 30a2c63c, 76ff8767, 2caa8c27, a40e0338) sit at Status=scouted in Pipeline DB. Pick one, manually flag qa_verdict, fire `python -m content_multiplier_crew <url> --mode auto --qa-verdict qa-passed --channels <channel>`. Verify Status=Ready writes correctly for video pieces, Status=Idea for everything else.
5. **Begin M3.7.3 wiring** in this priority order:
   - 5a: Notion schema extension (add `Multiplier Run ID`, `Piece Type`, `Source Treatment`, `QA Verdict`, `Fixable Strips`, `Concept To Keep`, `Remix Hint` properties to Content Board DB `339bcf1a-3029-81d1-8377-dc2f2de13a20`)
   - 5b: `multiplier-tick` heartbeat wake (every 5m, polls Notion for Status=Multiply records, calls `multiplier_tick()`). Crew_name=`studio` for kill-switch parity.
   - 5c: `/multiply <url>` slash command in `orchestrator/router.py`. Build via griot_propose pattern.
   - 5d: scout_approve callback in `handlers_approvals.py` fires `multiply_source` in daemon thread. **Risk: container restart kills daemon thread** (Queue #9 lesson). Mitigation: persist intent in approval_queue first, multiplier consumes from queue. Defer if too risky for one session.
   - 5e: Bulk Telegram review handler (`multiplier_approve_all:run_id`, `multiplier_per_piece:run_id`, `multiplier_reject_all:run_id`) in `handlers_approvals.py`.
6. Pre-commit pause: SANKOFA again. New wiring touches handlers_approvals (baked-precedence file per memory rule). Restart container with all changes. Audit logs for failures.

## Files changed this session

```
orchestrator/content_multiplier_crew.py        (NEW, ~870 lines)
orchestrator/tests/test_content_multiplier.py  (NEW, 21 tests)
orchestrator/tests/test_first_name_extraction.py (NEW, 36 tests)
orchestrator/griot.py                          (NEXT-day surfaced + cross-platform date)
orchestrator/studio_trend_scout.py             (cadence split: Studio daily, CW M/W/F)
orchestrator/studio_story_bridge.py            (FGM → 1stGen)
orchestrator/story_prompt_tick.py              (FGM → 1stGen)
orchestrator/crews.py                          (FGM → 1stGen in story signal text)
orchestrator/requirements.txt                  (added youtube-transcript-api)
skills/content_multiplier/SKILL.md             (NEW + HARD RULES section)
skills/content_multiplier/prompts/lens_classifier.md (NEW)
skills/content_multiplier/prompts/piece_generator.md (NEW + voice/CTQ embed)
skills/content_multiplier/prompts/remix_classifier.md (NEW)
skills/content_multiplier/prompts/remix_piece_generator.md (NEW + voice/CTQ embed)
skills/outreach/sequence_engine.py             (gkirz fix + 70-name allowlist)
skills/outreach/outreach_tool.py               (legacy path uses build_body)
signal_works/email_builder.py                  (gkirz fix in SW path)
docs/roadmap/studio.md                         (M3.7 entry expanded)
docs/roadmap/atlas.md                          (FGM → 1stGen)
docs/handoff/2026-05-07-multiplier-iter4-shipped-pipeline-fixes.md (this file)

VPS docker cp'd (baked-precedence files):
/app/scheduler.py, /app/app.py, /app/publish_brief.py
/app/story_prompt_tick.py, /app/studio_story_bridge.py, /app/griot_signal_brief.py
/app/content_multiplier_crew.py
/app/griot.py, /app/studio_trend_scout.py
/app/studio_story_bridge.py, /app/story_prompt_tick.py, /app/crews.py
```

**Commits this session:**
- `611dd2a` feat(studio,outreach): M3.7 content multiplier + remix QA + gkirz fix + griot UX
- `935d76c` fix(multiplier): iter 2 - channel rules + 1stGen rename + Notion 400 fix
- `a7fecfb` fix(multiplier): iter 3 - actually load voice + CTQ skill content into prompts
- `fc1ee3c` feat(multiplier): iter 4 ship + auto-promote guardrail + iter 5 voice fixes

All pushed to `feature/social-media-daily-analytics`.

# Session Handoff - Ideas DB Council Review + Newsletter Crew + beehiiv - 2026-04-27

## TL;DR

Session continued after context compaction. Cleaned up all uncommitted files (6 committed, 5 junk deleted). Ran Sankofa Council on 11 Ideas DB items: Council found that 9 of 11 should not be built yet because the constraint is clients, not media capability. All 11 entries updated in Notion with Council verdicts and full architectural specs (crew/agent/skill placement). Boubacar confirmed newsletters are live on beehiiv: built newsletter_crew (leGriot voice, colleague-not-professor standard, citation superscripts, 8-point QA). beehiiv REST API enhancement queued for this week.

## What was built / changed

- `orchestrator/router.py`: 'newsletter' task type added (10 keywords, routes to newsletter_crew)
- `orchestrator/constants.py`: 'newsletter' added to SAVE_REQUIRED_TASK_TYPES + CONTENT_TASK_TYPES
- `orchestrator/crews.py`: build_newsletter_crew() with full voice spec: planner + leGriot + QA, 8-point QA checklist, citation superscripts, Sources section
- `orchestrator/engine.py`: newsletter summary label added
- `docs/roadmap/atlas.md`: session log entries for file audit, newsletter ship, beehiiv enhancement
- `docs/handoff/2026-04-27-harvest-p1-p5-video-crew.md`: committed
- `docs/handoff/2026-04-27-notebooklm-drive-pipeline-shipped.md`: committed
- `docs/reference/model-review-2026-04-26.md`: committed
- `orchestrator/contracts/video_crew.md`: committed
- `scripts/nlm_registry_export.py`: committed
- Notion Ideas DB: all 11 items updated with Council verdicts + arch specs; n12 + R25 marked Done
- Notion Ideas DB: new beehiiv REST API entry created (id: 34fbcf1a-3029-815c-b1bc-de7364215adb)
- Memory: feedback_sankofa_ideas_db_protocol.md (NEW)
- Memory: feedback_newsletter_voice_standard.md (NEW)
- Memory: project_newsletter_beehiiv.md (NEW)
- 5 junk files deleted from thepopebot/chat-ui/ (font files, mockups, empty tmp)

## Decisions made

1. **Sankofa Council mandatory for all Ideas DB reviews**: always include current stack state and revenue constraint; Council must output crew/agent/skill arch spec for every activated item, not just a gate date.
2. **Newsletter platform is beehiiv**: not n8n, not Mailgun. Current flow: crew drafts -> Drive -> manual paste. Future: beehiiv REST API (~1h Codex).
3. **Newsletter voice: colleague not professor**: story anchor from Boubacar's real experience, citation superscripts inline with Sources section at bottom, wit and forwardability required.
4. **9 of 11 Ideas DB items gated on "first production job exists"**: Council found constraint is clients, not media capability. ib5 Droid FFMPEG is the only unconditional build.
5. **n12 and R25 marked Done**: both were already shipped; keeping them Queued was organizational debt.

## What is NOT done (explicit)

- **beehiiv REST API wiring**: queued for this week (by 2026-05-03). Codex task: orchestrator/beehiiv.py + BeehiivCreateDraftTool + BEEHIIV_API_KEY + BEEHIIV_PUBLICATION_ID env vars.
- **Branch merges**: feat/m11d-model-review (P1-P5) and feat/atlas-m9b-web-chat (M9b + newsletter) not merged to main, VPS not deployed.
- **P5 dry runs**: scheduled for May 8 via remote routine trig_01LWzVfXvcxWMFZwYrv8ondt.
- **ib5 Droid FFMPEG**: unconditional build, ~3.5h Codex, target May 8 session.
- **R25 platform decision**: which platforms beyond LinkedIn+X to activate in Blotato (15-min config).

## Open questions

- Merge feat/m11d-model-review + feat/atlas-m9b-web-chat to main and deploy to VPS now?
- R25: which 1-2 extra platforms beyond LinkedIn+X does Boubacar want active?

## Next session must start here

1. Run beehiiv REST API Codex task (by 2026-05-03): orchestrator/beehiiv.py + BeehiivCreateDraftTool + env vars + update build_newsletter_crew() task_write.
2. Merge feat/m11d-model-review to main (P1-P5 code), then merge feat/atlas-m9b-web-chat, then VPS deploy: `ssh root@72.60.209.109 "cd /root/agentsHQ && git pull && docker compose up -d --build orchestrator"`.
3. R25 platform decision: tell Claude which platforms to activate in Blotato beyond LinkedIn+X.
4. May 8: P5 dry runs (routine auto-fires at 9am MT).

## Files changed this session

```
orchestrator/router.py              MODIFIED (newsletter task type)
orchestrator/constants.py           MODIFIED (newsletter in task sets)
orchestrator/crews.py               MODIFIED (build_newsletter_crew)
orchestrator/engine.py              MODIFIED (newsletter label)
orchestrator/contracts/video_crew.md  COMMITTED (was untracked)
scripts/nlm_registry_export.py      COMMITTED (was untracked)
docs/roadmap/atlas.md               MODIFIED (session log + beehiiv note)
docs/handoff/2026-04-27-harvest-p1-p5-video-crew.md   NEW + committed
docs/handoff/2026-04-27-notebooklm-drive-pipeline-shipped.md  NEW + committed
docs/reference/model-review-2026-04-26.md  NEW + committed
docs/handoff/2026-04-26-m9b-complete.md    COMMITTED (was untracked, em dashes fixed)
thepopebot/chat-ui/atlas-chat.js.tmp        DELETED
thepopebot/chat-ui/atlas-preview.html       DELETED
thepopebot/chat-ui/atlas-font-compare.html  DELETED
thepopebot/chat-ui/OpenDyslexic-Bold.otf    DELETED
thepopebot/chat-ui/OpenDyslexic-Regular.otf DELETED
memory/feedback_sankofa_ideas_db_protocol.md  NEW
memory/feedback_newsletter_voice_standard.md  NEW
memory/project_newsletter_beehiiv.md          NEW
memory/MEMORY.md                               UPDATED
```

Commits this session: 9b7976d, 25e1eae, 62fbff3, 6a3e9f2, 5150f8c
Current branch: feat/atlas-m9b-web-chat

# Session Handoff - Studio Pipeline Fixes + Re-render Queue - 2026-05-05

## TL;DR

Found and fixed a three-bug chain in `studio_render_publisher.py` that caused all renders to either fail silently or use stale `.pyc` bytecode (old title-card code with burned-in captions). Deployed fixes to container. Reset 13 Notion records to `qa-passed` for re-render with correct pipeline (branded intro/outro cards + no burned captions + Drive upload working). Re-render batch is in progress on VPS.

## What was built / changed

- `orchestrator/studio_render_publisher.py`:
  - Removed corrupted em-dash byte `\x97` from docstring (line 169) - was causing UTF-8 SyntaxError, Python fell back to stale `.pyc`
  - Added `_ASSETS_DIR = Path(os.environ.get("STUDIO_ASSETS_DIR", "/app/workspace/assets"))` constant (was referenced but never defined)
  - Fixed `_upload_to_drive()` call from 2 args to 4: `_upload_to_drive(local_path, fmt_folder, local_path.name, "video/mp4")`

- `orchestrator/studio_qa_crew.py`:
  - `source_citation` check now skipped for `length_target == "short (<60s)"` (was blocking all AI Catalyst + First Gen Money candidates)

- `docs/roadmap/studio.md`:
  - M3.4 milestone added (Ken Burns - Mixed Video, QUEUED)
  - Session log entry appended for 2026-05-05 session 1 + session 2

- Notion: 12 archived records + 1 Baobab record reset to `qa-passed`, `Asset URL` cleared
- VPS: Old renders moved to `/app/workspace/renders/archive/2026-05-05/`
- Container: restarted with all 3 fixes live

## Decisions made

- **Archive not delete**: Old renders (broken pipeline) moved to `/app/workspace/renders/archive/`, not deleted. Drive links preserved. Boubacar's rule.
- **AI Catalyst archived records stay archived**: They contain scraped YouTube titles with no Draft script. Not ours to re-render.
- **Intro/outro assets confirmed live at**: `/app/workspace/assets/intros/{channel_id}_intro.mp4` and `outros/` - all 6 files present.
- **`.pyc` delete protocol**: Every `docker cp` must be followed by `rm __pycache__/*.pyc` + `py_compile.compile()` check + container restart.

## What is NOT done (explicit)

- **First re-render not yet reviewed**: Batch started but no Drive link confirmed for a correct video yet. Next session does the acceptance check.
- **M3.4 scene motion upgrade**: Queued milestone, not started. Implement after first-batch review.
- **AI Catalyst scout queue**: 0 AI Catalyst candidates in re-render queue. Pipeline will scout fresh ones automatically on next scout tick.

## Open questions

- Did the re-render batch complete overnight? Check 13 records in Notion - should all be `scheduled` with Drive URLs.
- Is the first video correct? Verify intro card visible, no burned captions, outro card at end.

## Next session must start here

1. Check Notion pipeline DB: how many of the 13 records are now `scheduled` with Asset URLs?
2. Open first completed video from Drive - verify intro card + no burned captions + outro card.
3. If correct: Boubacar approves or requests changes. If wrong: diagnose which step failed.
4. Once batch confirmed good: check AI Catalyst scout queue - if empty, may need to trigger scout manually.
5. Begin M4 publisher warm-up planning (Blotato fires at 09:00 MT on `Status=scheduled AND ScheduledDate=today`).

## Files changed this session

```
orchestrator/studio_render_publisher.py  -- 3 bugs fixed
orchestrator/studio_qa_crew.py           -- source_citation skip for shorts
docs/roadmap/studio.md                   -- M3.4 milestone + 2 session log entries
```

Memory files written:
```
memory/feedback_studio_render_publisher_bugs.md  -- 3-bug chain root cause
memory/feedback_pyc_stale_on_docker_cp.md        -- docker cp protocol
memory/project_studio_rerender_queue.md           -- 13 queued re-renders state
```

# RCA: Telegram /sw command -- 2026-05-08

**Root cause:** Dockerfile `COPY orchestrator/*.py .` bakes all handlers into `/app/`. uvicorn CWD is `/app/`, so Python imports `/app/handlers_commands.py` (baked, stale) before the volume-mounted `/app/orchestrator/handlers_commands.py`. Edits to the orchestrator volume never reach the running import.

**Fix applied:** `docker exec orc-crewai cp /app/orchestrator/handlers_commands.py /app/handlers_commands.py` — overwrote baked copy with volume-mounted version containing `_cmd_sw`. Container restarted. Verified `_cmd_sw present` on import.

**Success criterion verified:** `docker exec orc-crewai python3 -c "from handlers_commands import _cmd_sw; print('_cmd_sw present')"` -> `_cmd_sw present`

**Never-again rule:** After editing any file listed in the baked-import precedence list, ALWAYS run `docker exec orc-crewai cp /app/orchestrator/<file>.py /app/<file>.py` AND delete pyc before restart — volume mount alone is not enough.

**Memory update:** yes -- update feedback_baked_image_import_precedence.md to add handlers_commands.py to the list.

## Files that need docker cp after edit (baked image import precedence)

These files exist at both `/app/<file>.py` (baked) and `/app/orchestrator/<file>.py` (volume).
Python imports the baked copy. Always sync with docker cp after editing.

- handlers_commands.py (confirmed 2026-05-08)
- handlers.py
- handlers_approvals.py
- handlers_chat.py
- handlers_doc.py
- dream_handler.py
- blotato_publisher.py
- studio_render_publisher.py
- studio_blotato_publisher.py
- studio_voice_generator.py
- griot.py
- griot_signal_brief.py
- studio_trend_scout.py
- story_prompt_tick.py
- studio_story_bridge.py
- content_multiplier_crew.py

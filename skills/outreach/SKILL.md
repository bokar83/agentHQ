---
name: outreach
description: Core outreach engine for SW + CW pipelines. Agent-internal only -- not Boubacar-invoked. sequence_engine.py runs 4/5-touch email sequences imported by morning_runner, engine.py, and send_scheduler. outreach_tool.py and email_templates.py are production code.
---

# Outreach (Agent-Internal)

Production code module. Not a Boubacar-invoked skill. Contains:

- `sequence_engine.py` -- 4/5-touch email sequence runner (SW + CW). Imported by `morning_runner.py`, `orchestrator/engine.py`, `send_scheduler.py`.
- `outreach_tool.py` -- outreach pipeline tool.
- `email_templates.py` -- email template library.

**DO NOT archive.** These files are active production imports.

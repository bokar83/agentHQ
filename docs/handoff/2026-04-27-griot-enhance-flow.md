# Session Handoff - Griot Enhance Flow - 2026-04-27

## TL;DR

Built the full interactive post enhancement loop into the griot approval flow. What started as a question about why the approval queue only showed a title turned into a complete redesign: posts now show their full body, empty-body posts are allowed through (Enhance writes the body), and the Telegram interface supports an iterative leGriot rewrite loop that can go as many rounds as needed before approving. All live on VPS at commit 84d9563.

## What was built / changed

- `orchestrator/griot.py`:
  - `_row_from_notion`: added `"draft": _get_text(props.get("Draft", {}))` to fetch post body
  - `_split_pool`: candidate filter changed to `title or hook or draft` (body optional)
  - payload block: added `"text": (top.get("draft") or "")` so preview shows full post body

- `orchestrator/approval_queue.py`:
  - `_format_proposal_preview`: rewritten to show `Queue #N [Platform]: Title / --- / body (or "(no body)") / ---`
  - `enqueue`: buttons changed to Approve / Enhance / Reject for initial proposals
  - `KNOWN_FEEDBACK_TAGS`: added `"enhance"`

- `orchestrator/handlers_approvals.py`:
  - `enhance_queue_item` callback: marks row `enhancing` via direct SQL, fires `_run_enhance_crew` in daemon thread
  - `approve_variation` callback: writes chosen variation to Notion Draft field, calls `_aq_approve`
  - `reject_variation` callback: removes one variation from payload list; if last variation removed, rejects row
  - `enhance_variation` callback: builds synthetic qrow with that variation as draft, re-fires `_run_enhance_crew`
  - `_run_enhance_crew()` function: runs social crew with title+draft context, parses VARIATION labels, stores list in payload, sends one Telegram message per variation with Approve/Enhance/No buttons

## Decisions made

1. **Variations are payload, not rows.** Stored as `payload["variations"]` JSON array on the existing queue row. No new DB schema needed.
2. **"No" on a variation removes only that variation.** Other variations stay live. Only when the last one is removed does the row get rejected.
3. **"Reject" on the initial proposal kills the whole row.** This is intentional and clearly distinct from variation-level "No".
4. **Empty-body posts surface.** Removed the hard `draft` requirement from the candidate filter. Enhance can write the body for a post that only has a title or hook.
5. **Enhance is recursive.** `enhance_variation` fires `_run_enhance_crew` with the chosen variation as the new draft. No depth limit.
6. **Notion Draft write on Approve.** The chosen variation text gets written back to the Notion `Draft` rich_text field before scheduling. The source of truth stays in Notion.

## What is NOT done (explicit)

- No test coverage for the new callbacks (enhance_queue_item, approve_variation, reject_variation, enhance_variation). Should be added before this flow scales.
- `_run_enhance_crew` failure path marks the row rejected: a retry mechanism would be better for transient errors.
- The variation index in callback_data is 1-based and immutable. If you Enhance variation 2, the new variations come back as 1/2/3 again: there's no ancestry tracking.

## Open questions

- Should there be a maximum Enhance depth to prevent infinite loops if quality never satisfies?

## Next session must start here

1. Check griot approval queue for any pending proposals: `docker exec orc-postgres psql -U postgres -d postgres -c "SELECT id, status, payload->>'title' as title, ts_created FROM approval_queue ORDER BY ts_created DESC LIMIT 5;"`
2. Build beehiiv REST API (due 2026-05-03): `orchestrator/beehiiv.py` + `BeehiivCreateDraftTool` in `tools.py` + `BEEHIIV_API_KEY` + `BEEHIIV_PUBLICATION_ID` in `.env` and `docker-compose.yml` + update `build_newsletter_crew()` to call `create_draft()` after `save_output`. Run as Codex task.
3. Start Signal Works outreach (contract target 2026-05-02): email queue at `signal_works/email_queue_pediatric_dentist_Salt_Lake_City.csv`, templates at `signal_works/templates/`, HVAC demo at `output/websites/signal-works-demo-hvac/` needs Vercel deploy.

## Files changed this session

```
orchestrator/griot.py                   draft field in _row_from_notion; filter + payload
orchestrator/approval_queue.py          preview format; Approve/Enhance/Reject buttons; enhance tag
orchestrator/handlers_approvals.py      4 new callbacks + _run_enhance_crew function

memory/project_atlas_m9_m11_state.md   updated state
memory/project_griot_enhance_flow.md   NEW: full spec of enhance flow
memory/MEMORY.md                        2 pointer updates
docs/handoff/2026-04-27-griot-enhance-flow.md  THIS FILE
```

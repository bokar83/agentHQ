# Newsletter Monday-Tight Cadence - Design Spec

**Date:** 2026-04-30
**Codename area:** atlas (autonomy layer)
**Status:** approved, ready for implementation plan
**Build target:** 2.5-3.5h
**First live fire:** Monday 2026-05-05 12:00 MT (Issue 3)
**Test fire:** Sunday 2026-05-04 18:00 MT (editorial prompt path)

## Goal

Boubacar's weekly newsletter ships every Tuesday using fresh-this-Monday data, with editorial input captured Sunday evening (not Monday morning), no required taps if Boubacar is unavailable, and a paste-ready handoff to beehiiv by Monday 12:10 MT.

## Why this design

The newsletter is the authority piece. Subscribers expect it to be more curated than daily LinkedIn posts. Two structural realities drove the design:

1. **Engagement-ranked topics ≠ newsletter-worthy topics.** The studio_trend_scout's Total Score optimizes for view velocity. The newsletter wants Boubacar's lived observation from the week. Source the topic from Boubacar's Sunday-night brain dump, not from a scout ranking.
2. **Boubacar is not always at his phone Monday 06:00-11:30 MT.** The earlier "Anchor button by 11:30" design failed loud when he wasn't watching. This design makes Boubacar's editorial input arrive Sunday evening (when he's actually thinking about the week) and treats Monday as a writing day, not a decision-day.

## Architecture

```
Sun 18:00 MT - newsletter-editorial-prompt heartbeat wake
   ↓ Telegram message: "What did you notice this week worth a newsletter? One sentence reply."
   ↓ Free-text reply between Sun 18:00 and Mon 06:00 captured to Postgres newsletter_editorial_input
   ↓ Last reply wins if multiple sent

Mon 06:00 MT - studio_trend_scout_tick (existing)
   ↓ scout 9 niches, write picks to Notion + Telegram with [Approve][Reject][📰 Newsletter] on CW picks
   ↓ AFTER niches loop, choose anchor:
     - If Postgres has a Sunday reply for this week: create synthetic Notion record
       (Title=first 80 chars of reply, Source Note=full reply, Status=Ready,
        Type=Newsletter, Platform=[Newsletter], Anchor Date=today)
     - Else: pick highest Total Score CW pick (deterministic tie-break on source_url),
       set its Status=Ready, Type=Newsletter, Platform+=Newsletter, Anchor Date=today
   ↓ Telegram summary: which path was taken + anchor title

Mon 06:05-11:59 MT - override window
   ↓ Boubacar can tap [📰 Newsletter] on a different scout pick to swap anchor
   ↓ Handler clears previous anchor's Type/Platform, sets them on the tapped pick
   ↓ Cross-talk guard: rejects if tapped pick already has Type set to non-Newsletter

Mon 12:00 MT - newsletter-anchor heartbeat wake
   ↓ Query Content Board for Anchor Date=today AND Type=Newsletter
   ↓ 0 records: Telegram alert "no newsletter anchor today, skipping" + audit row
   ↓ 1 record: build user_request from Title + Source Note URL, run newsletter_crew
   ↓ newsletter_crew: plan → write → verify_sources (NEW) → SankofaCouncil (NEW) → qa
   ↓ Telegram: full draft + thumbnail + [✅ Approve][✏️ Revise]

Approve tap:
   ↓ Render beehiiv-ready HTML
   ↓ Send via gws CLI (CW creds) to boubacar@catalystworks.consulting
   ↓ Telegram reply: "Draft in your inbox for posting. Subject: [...]. Drive: [...]"
   ↓ Notion: write Source Note timestamp

Revise tap:
   ↓ Telegram reply: "Acknowledged. Edit in Drive and reply with edits, or re-tag a different pick."
```

## Components

### Component 1 - Sunday 18:00 editorial prompt

**Files:**
- NEW: `orchestrator/newsletter_editorial_prompt.py` (~60 lines)
- MODIFY: `orchestrator/scheduler.py` (+12 lines, register wake)
- MODIFY: `orchestrator/handlers_chat.py` or wherever Telegram replies are routed (capture free-text reply window)
- NEW: Postgres table `newsletter_editorial_input` (week_start_date date PK, reply_text text, received_at timestamptz)

**Logic:**
- Heartbeat wake `newsletter-editorial-prompt` registered with `at="18:00"`, `crew_name="newsletter_crew"`.
- Callback gates on `weekday() == 6` (Sunday).
- Sends Telegram message exactly once per Sunday.
- Reply capture: in the main Telegram message handler, if a free-text message (not a callback button) arrives in the operator chat between Sun 18:00 MT and Mon 06:00 MT, INSERT or UPDATE on `newsletter_editorial_input` for `week_start_date = next Monday's date`. Last write wins.

**Success criterion:** Heartbeat log on 2026-05-04 18:00 MT shows `HEARTBEAT: fire <id> newsletter-editorial-prompt`. Telegram message arrives within 60 seconds. Reply (if sent) creates Postgres row visible via `psql -c "SELECT * FROM newsletter_editorial_input"`.

### Component 2 - Mon 06:05 anchor selection

**Files:**
- MODIFY: `orchestrator/studio_trend_scout.py` (+30 lines)
- Notion schema: add `Anchor Date` (date type) property to Content Board (one-time)

**Logic:**
- After the niches loop in `studio_trend_scout_tick`, before `_send_summary`:
  - Query Postgres: `SELECT reply_text FROM newsletter_editorial_input WHERE week_start_date = today_iso`.
  - **If reply found:** create new Notion Content Board page with `Title=reply_text[:80]`, `Source Note=reply_text`, `Status={"select":{"name":"Ready"}}`, `Type={"select":{"name":"Newsletter"}}`, `Platform={"multi_select":[{"name":"Newsletter"}]}`, `Anchor Date={"date":{"start":today_iso}}`. Send Telegram summary: "Newsletter anchor for this Monday: your Sunday note. Drafting at 12:00 MT."
  - **If no reply:** filter the run's picks to CW-niche only (`cw_picks = [p for p in all_picks if p.destination == "Content Board"]`), then find top-scored: `sorted(cw_picks, key=lambda p: (-p.total_score, p.source_url))[0]`. Update that pick's Notion record with same four properties. Send Telegram summary: "No Sunday note received. Using top scout pick: [title]. Tap [📰 Newsletter] on a different pick to swap."
- Auto-anchor logic only runs when at least one CW pick was written OR when a Sunday reply exists. If both empty, no anchor is set; Mon 12:00 will alert.

**Success criterion:** After 06:00 fire, exactly 1 Content Board record matches `Anchor Date=today AND Type=Newsletter`. Telegram summary names the path taken.

### Component 3 - `[📰 Newsletter]` override button

**Files:**
- MODIFY: `orchestrator/studio_trend_scout.py:_send_pick_with_buttons` (+3 lines)
- MODIFY: `orchestrator/handlers_approvals.py` (+30 lines for `scout_newsletter:` handler)

**Logic:**
- In `_send_pick_with_buttons`: if `cand.destination == "Content Board"`, append `("📰 Newsletter", f"scout_newsletter:{notion_page_id}")` to the buttons row. Studio Pipeline picks unchanged.
- New handler in `handlers_approvals.py`:
  ```python
  elif cb_data.startswith("scout_newsletter:"):
      notion_page_id = cb_data.split(":", 1)[1]
      notion = _open_notion()
      page = notion.get_page(notion_page_id)
      current_type = page.get("properties", {}).get("Type", {}).get("select", {})
      # Cross-talk guard
      if current_type and current_type.get("name") and current_type.get("name") != "Newsletter":
          answer_callback_query(cb_id, "Already typed as " + current_type["name"])
          send_message(cb_chat_id, f"This pick is already typed as {current_type['name']}. Newsletter must be tagged on a different pick.")
          return
      # Tag this pick
      today_iso = datetime.now(pytz.timezone(TIMEZONE)).date().isoformat()
      notion.update_page(notion_page_id, properties={
          "Status": {"select": {"name": "Ready"}},
          "Type": {"select": {"name": "Newsletter"}},
          "Platform": {"multi_select": [{"name": "Newsletter"}]},
          "Anchor Date": {"date": {"start": today_iso}},
      })
      # Clear previous anchors for today
      previous = notion.query_database(CONTENT_BOARD_DB_ID, filter_obj={
          "and": [
              {"property": "Anchor Date", "date": {"equals": today_iso}},
              {"property": "Type", "select": {"equals": "Newsletter"}},
          ]
      })
      for p in previous:
          if p["id"] == notion_page_id:
              continue
          notion.update_page(p["id"], properties={
              "Type": {"select": None},
              "Platform": {"multi_select": []},
              "Anchor Date": {"date": None},
          })
      answer_callback_query(cb_id, "Newsletter anchor swapped.")
      send_message(cb_chat_id, f"Newsletter anchor swapped to: {page['properties']['Title']['title'][0]['text']['content']}")
  ```

**Success criterion:** Manual swap test in Sunday dry-run: tap button on pick #2 when pick #1 was the auto-anchor. Notion shows pick #2 tagged, pick #1 cleared.

### Component 4 - Mon 12:00 newsletter draft + email handoff

**Files:**
- NEW: `orchestrator/newsletter_anchor_tick.py` (~180 lines)
- MODIFY: `orchestrator/scheduler.py` (+12 lines, register wake)
- MODIFY: `orchestrator/crews.py:1004-1163` `build_newsletter_crew` (+50 lines: add `task_verify_sources`, wire SankofaCouncil pre-qa)
- MODIFY: `orchestrator/handlers_approvals.py` (+60 lines for `newsletter_approve:` and `newsletter_revise:` handlers)

**Logic:**
- Heartbeat wake `newsletter-anchor` registered with `at="12:00"`, `crew_name="newsletter_crew"`.
- Callback gates on `weekday() == 0` (Monday).
- Tick:
  ```python
  def newsletter_anchor_tick():
      tz = pytz.timezone(TIMEZONE)
      now = datetime.now(tz)
      if now.weekday() != 0:
          return
      today_iso = now.date().isoformat()
      notion = _open_notion()
      records = notion.query_database(CONTENT_BOARD_DB_ID, filter_obj={
          "and": [
              {"property": "Anchor Date", "date": {"equals": today_iso}},
              {"property": "Type", "select": {"equals": "Newsletter"}},
          ]
      })
      if not records:
          send_telegram_alert("No newsletter anchor today, skipping this week.")
          write_audit_row("newsletter-anchor", "no_anchor", None)
          return
      record = records[0]
      title = _extract_title(record)
      source_note = _extract_source_note(record)
      user_request = f"Topic: {title}\n\nContext: {source_note}"
      crew = build_newsletter_crew(user_request, metadata={"high_stakes": True})
      result = crew.kickoff()
      thumbnail_path = generate_thumbnail(title)
      drive_link = save_to_drive(result, thumbnail_path)
      send_telegram_with_buttons(
          text=_format_draft_preview(result, drive_link),
          photo=thumbnail_path,
          buttons=[[
              ("✅ Approve", f"newsletter_approve:{record['id']}"),
              ("✏️ Revise", f"newsletter_revise:{record['id']}"),
          ]]
      )
      write_audit_row("newsletter-anchor", "drafted", record["id"])
  ```
- newsletter_crew changes (crews.py:1004-1163):
  - Add `task_verify_sources` between `task_write` and `task_qa`. Researcher agent. Description: "For each external stat or study cited in the draft, verify the citation is real and accurate. If the source cannot be verified, flag it for removal or re-citation. Do not invent verifications. If you cannot verify, say so."
  - Wire SankofaCouncil: at the top of `build_newsletter_crew`, call `should_invoke_council("consulting_deliverable", metadata={"high_stakes": True})`. If `CouncilTier.FULL`, run the council on the draft after `task_write` (mirror the pattern in `build_consulting_crew` at lines 720-770).
- newsletter_approve handler:
  - Extract subject + body + sources from QA task output.
  - Render beehiiv-ready HTML: `<h1>{subject}</h1><body>{body_paragraphs}</body><hr><h2>Sources</h2>{sources}`.
  - Send via gws CLI: `gws gmail users drafts create --params '{"userId":"me"}' --json '{...}' --upload-content-type "message/rfc822"` (use the existing `signal_works.gmail_draft` Python helper since it's CW creds).
  - Recipient: `boubacar@catalystworks.consulting` only.
  - Telegram reply: "Draft in your inbox for posting. Subject: [...]. Drive link: [...]"
  - Update Notion record's Source Note: append "[email-sent: {timestamp}]"
  - Audit row.
- newsletter_revise handler:
  - Telegram reply: "Acknowledged. Edit in Drive and reply with edits, or re-tag a different pick to redraft from scratch."
  - Audit row.

**Success criterion:** Heartbeat log on 2026-05-05 12:00 MT shows `HEARTBEAT: fire <id> newsletter-anchor`. Log line `newsletter_anchor_tick: anchor found page=<8-char prefix>`. Telegram draft message arrives by 12:08 MT. On Approve tap: Gmail thread "Weekly Signal - [subject]" lands in `boubacar@catalystworks.consulting` by 12:10 MT. Telegram reply confirms.

## Data flow

```
Sunday reply text (Telegram chat)
   → newsletter_editorial_input (Postgres, weekly row)

Monday 06:00 anchor selection
   → either: synthetic Notion page (if Sunday reply) → Anchor Date=today, Type=Newsletter
   → or:    existing scout pick (top Total Score CW)  → Anchor Date=today, Type=Newsletter

Monday 12:00 newsletter draft
   → newsletter_crew(user_request from Notion record) → draft text + sources
   → kie_media generates thumbnail
   → saved to Drive
   → posted to Telegram with Approve/Revise buttons

Approve
   → beehiiv-ready HTML email → boubacar@catalystworks.consulting
   → Notion Source Note appended with timestamp
   → task_outcomes audit row
```

## Schema changes

**Postgres (one-time):**
```sql
CREATE TABLE newsletter_editorial_input (
  week_start_date date PRIMARY KEY,
  reply_text text NOT NULL,
  received_at timestamptz NOT NULL DEFAULT NOW()
);
```

**Notion Content Board (one-time):**
- Add property: `Anchor Date` (date type)

## Operational rules

1. **Only nudge on failure.** No "newsletter is happening tomorrow" reminders. The Sunday prompt is editorial input, not a schedule reminder.
2. **Email is convenience; Drive doc is the SLA.** If gws CLI auth fails or the email doesn't land, the Drive link in the Telegram approve message is the canonical handoff path.
3. **No silent stalls.** If Mon 12:00 finds 0 anchor records, send Telegram alert. Boubacar must know the newsletter slipped.
4. **Weekly attention budget cap (CADENCE_CALENDAR Rule #4):** this design adds 1 Sunday touchpoint (1 Telegram message + optional 1-sentence reply, ~2 min) and the existing Mon 12:00 review window (15 min). Total weekly add: ~17 min. Within budget.

## Rollback

- `autonomy_state.json` → `studio.enabled=false` silences C2 (auto-anchor at scout fire) and C3 (override button on scout picks).
- `autonomy_state.json` → `newsletter_crew.enabled=false` silences C1 (Sunday prompt) and C4 (12:00 wake).
- For Mon 2026-05-05 specifically: if Sunday 2026-05-04 dry-run shows any failure, set `newsletter_crew.enabled=false` and revert to manual (Issue 2 process).

## Test plan

**Sunday 2026-05-04 evening (dry-run):**
- 18:00 MT: heartbeat fires `newsletter-editorial-prompt`. Verify Telegram message arrives.
- Reply with a one-sentence test note. Verify Postgres `newsletter_editorial_input` row exists.
- Manually run `docker exec orc-crewai python -m orchestrator.newsletter_anchor_tick --once`. The `--once` flag fires the full path with `[TEST]` prefix on Telegram message and Gmail subject. Verify draft + thumbnail + Approve/Revise buttons appear in Telegram with [TEST] prefix.
- Tap Approve. Verify [TEST] email lands in `boubacar@catalystworks.consulting`.

**Monday 2026-05-05 live fire:**
- 06:00 MT: scout fires. Verify auto-anchor logic picked Sunday-reply path (or top pick if no reply). Telegram summary describes path.
- 12:00 MT: newsletter_anchor wake fires. Verify draft message in Telegram by 12:08 MT.
- Tap Approve. Verify production email lands by 12:10 MT.
- Verify Notion record updated with timestamp.

If any step fails, set `newsletter_crew.enabled=false` and revert to manual.

## Karpathy fixes embedded

| # | Fix | Location in design |
|---|---|---|
| 1 | Read crews.py + council.py first | Done before spec write. Result: SankofaCouncil exists in council.py and is wired into build_consulting_crew only; newsletter_crew has no source verification. Component 4 grows by +50 lines in crews.py. |
| 2 | Deterministic tie-break on Total Score | `sorted(cw_picks, key=lambda p: (-p.total_score, p.source_url))[0]` in Component 2 |
| 3 | --dry-run replaced with --once | Component 4 test plan uses `--once` flag with [TEST] prefix on artifacts (permanent, not throwaway) |
| 4 | Audit row to task_outcomes | `write_audit_row(tick_name, status, record_id)` after every wake fire in C1, C2, C4 |
| 5 | Cross-talk rejection | Component 3 handler rejects Newsletter tag if Type is already non-Newsletter |

## Open items resolved

| Question | Resolution |
|---|---|
| Manual Anchor button vs auto-anchor | Sunday-prompt-default with scout fallback (Design B from Sankofa round 1) |
| Email recipients | One inbox: boubacar@catalystworks.consulting |
| Button label | `[📰 Newsletter]` (not Anchor) |
| Sunday reminder | Repurposed as editorial input prompt, not schedule reminder |
| 11:30 fallback nudge | Dropped (system always has anchor by 06:05) |
| dry-run flag scope | Replaced with `--once` permanent flag |
| Anchor Date property | NEW Notion date property on Content Board, deterministic signal |
| crews.py held read | Resolved: source verification gap confirmed, SankofaCouncil wiring needed for newsletter_crew |
| project_task_backlog.md | Does not exist on disk despite memory references; tracking via atlas roadmap session-log instead. Memory cleanup to follow at session end. |

## File touch summary

| File | Lines | Type |
|---|---|---|
| `orchestrator/scheduler.py` | +24 | MODIFY (register 2 wakes) |
| `orchestrator/studio_trend_scout.py` | +30 | MODIFY (anchor selection + override button) |
| `orchestrator/handlers_approvals.py` | +90 | MODIFY (3 handlers + reply capture) |
| `orchestrator/newsletter_anchor_tick.py` | ~180 | NEW |
| `orchestrator/newsletter_editorial_prompt.py` | ~60 | NEW |
| `orchestrator/crews.py` | +50 | MODIFY (verify_sources task + Sankofa wiring) |
| Postgres migration | +1 table | NEW |
| Notion Content Board schema | +1 property | NEW |

**Total:** ~434 lines across 6 files, 1 Postgres table, 1 Notion property. Build estimate **2.5-3.5h**.

## Out of scope (explicit)

- Beehiiv API integration beyond existing draft-create (Enterprise plan would unlock; non-goal here).
- Newsletter scheduling logic (Boubacar manually schedules send time in beehiiv UI).
- Multi-week editorial backlog (one anchor per week max; future weeks queued via Sunday prompts each week).
- Newsletter analytics / open rates / click rates (post-send tracking is a separate milestone).
- A/B subject line testing.

# Atlas — Second Brain Ingest Layer — Phase A

**Codename:** atlas-second-brain
**Phase:** A (foundation: capture surface)
**Status:** spec ready, build pending
**Started:** 2026-05-12 (spec)
**Build start:** 2026-05-12 (Boubacar wake)
**Target ship:** May 2026
**Owner:** Boubacar Barry
**One-line:** Unified ingest layer that captures every save (X bookmarks, YT Watch Later, Skool lessons) into one inbox the agent processes overnight.

---

## Why this exists

Boubacar consumes high-signal content (X threads, YT videos, Skool lessons) faster than he integrates it. Bookmarks rot. The save button feels like learning; retrieval never happens. This is the **capture friction** gap.

agentsHQ already has the "act" layer (74 skills, Notion Content Board, MEMORY.md, /agentshq-absorb). Missing: the **stream** that feeds those systems with what Boubacar actually consumes.

**Three-phase rollout:**

| Phase | What | Order |
|---|---|---|
| **A** | Foundation: web-session-harvester w/ skool + x-bookmarks + yt-watch-later adapters → workspace/inbox/ | **This month** |
| **C** | Query surface: `/recall` skill grepping inbox + MEMORY + handoffs + skills | After A |
| **B** | LLM router: tag each item (kind/motion/action), dispatch to content-board / studio-seed / absorb-queue / archive | After C (C is the test harness for B) |

Phase B intentionally last. Without C, B is guessing what "useful routing" means.

---

## Phase A scope (what gets built this month)

### 1. New skill: `web-session-harvester`

**Replaces** `skool-harvester`. Existing skool scripts become the `skool` adapter inside the new skill. No skill-count growth (74 → 74).

**Skill location:** `~/.claude/skills/web-session-harvester/SKILL.md`
**Script location:** `d:/Ai_Sandbox/agentsHQ/scripts/web-session-harvester/`

### 2. Adapter contract

Every adapter implements three functions:

```python
def login(state_path: Path) -> None:
    """Interactive: headed Playwright, detect auth, save storage_state."""

def check_session(state_path: Path) -> bool:
    """Probe request → True if session valid, False if expired."""

def harvest(state_path: Path, out_dir: Path, **kwargs) -> list[dict]:
    """Run one pass. Return list of Item dicts. Write raw artifacts to out_dir."""
```

### 3. Three adapters

| Adapter | Surface | Auth state | Pagination | Transcript? |
|---|---|---|---|---|
| `skool` | skool.com lessons | `skool.json` (exists) | scroll | n/a |
| `x-bookmarks` | x.com/i/bookmarks | `x.json` (new) | infinite scroll | n/a |
| `yt-watch-later` | youtube.com/playlist?list=WL | `yt.json` (new) | XHR (full list) | hand off to `transcribe` skill (URL-only in Phase A) |

**X adapter:** runs LOCAL Windows machine (not VPS) — TOS mitigation. VPS-IP + fixed-cron = bot-pattern flag. Local Windows Task Scheduler or manual trigger only for X. Skool + YT fine on VPS.

**YT adapter Phase A:** records URL + title + channel + duration. NO transcript. Transcription = manual `/transcribe <url>` later OR Phase B router decides.

### 4. Output schema

One `item.json` per captured item:

```yaml
source: "skool" | "x-bookmarks" | "yt-watch-later"
url: "https://..."
captured_at: "2026-05-12T14:22:00Z"  # ISO-8601 UTC
author: "handle or channel name"
kind: "tweet" | "thread" | "video" | "lesson" | "link"
title: ""        # tweet first 80 chars / video title / lesson title
body: ""         # full text where applicable
status: "raw"    # raw → routed → absorbed | skipped
tags: []         # empty in Phase A (filled by Phase B router)
media_urls: []   # embedded images/CDN URLs
transcript_path: ""  # filled by Phase B if transcribed
surface_meta: {}     # adapter-specific (skool: community/lesson_id; yt: duration; x: reply_to_url)
```

**Inbox path:**
```
workspace/inbox/<surface>/YYYY-MM-DD/<slug>/item.json
workspace/inbox/<surface>/YYYY-MM-DD/<slug>/downloads/  # if any
```

### 5. Index file (Phase C contract)

`runner.py` appends one JSONL line per item to `workspace/inbox/_index.jsonl`:

```json
{"id": "x-bookmarks/2026-05-12/abc123", "source": "x-bookmarks", "url": "...", "title": "...", "author": "...", "kind": "tweet", "captured_at": "...", "status": "raw", "tags": [], "item_path": "workspace/inbox/x-bookmarks/2026-05-12/abc123/item.json"}
```

Phase C (`/recall`) reads this as its corpus. Phase A guarantees: every item written = one index line. Atomic (write item.json → append index in try/finally).

### 6. Session management

State files at `~/.claude/playwright-state/<surface>.json`.

| Surface | State file | Expiry behavior |
|---|---|---|
| skool | `skool.json` (exists) | weeks-to-months |
| x | `x.json` (new) | ~30 days (X auth cookies) |
| yt | `yt.json` (new) | longer, but IP-sensitive |

**Re-auth trigger:** `check_session()` probe before every cron run. Expired = skip surface, append `auth_needed: true` to `workspace/inbox/_status.json`, send Telegram alert via `notifier.send_message()` with login command. Boubacar re-runs login script manually (same pattern as skool today).

### 7. Cron auto-absorb

**VPS host cron** (`root@72.60.209.109`). NOT local Windows scheduler.

**File:** `/etc/cron.d/web-session-harvester`

```
# web-session-harvester — M-F full, Sat lite, Sun skip (Sabbath)
0 10 * * 1-5  root  cd /root/agentsHQ && python scripts/web-session-harvester/runner.py --all >> /var/log/wsh.log 2>&1
0 10 * * 6    root  cd /root/agentsHQ && python scripts/web-session-harvester/runner.py --all --lite >> /var/log/wsh.log 2>&1
```

**Sabbath:** schedule itself enforces (1-5 + 6 only, no Sunday). `--lite` flag passes `max_items=20`/adapter for Saturday.

**X exception:** X adapter runs locally on Windows (Task Scheduler), not VPS. VPS cron skips X. See risk #1.

### 8. Auto-absorb (Phase A — hardcoded heuristic, no LLM)

After each harvest, `runner.py` calls `auto_absorb.py` on new items:

| Condition | Action |
|---|---|
| `kind=lesson` AND `surface=skool` AND `downloads/` contains `*.json` or `*.zip` | Call `/agentshq-absorb <url>` (autonomous) |
| `kind=video` AND title contains keyword from `config/auto_absorb_rules.json` watchlist (`n8n`, `claude`, `agent`, `workflow`, `automation`) | Append to `workspace/inbox/_absorb_queue.jsonl` (manual review batch) |
| `kind=tweet` AND author in `config/watch_handles.json` | Append to `_absorb_queue.jsonl` |
| All others | `status=raw`, sits in inbox for Phase C query |

**Why heuristic not LLM:** Phase B router not built. Heuristic = cheap, deterministic, false-positive-rate measurable. Tune keyword list + watch handles after 2 weeks of real data. Replace with LLM router in Phase B.

**No volume cap.** Hoarder-rate metric instead — see #9.

### 9. Hoarder-rate metric (replaces volume cap)

`runner.py` appends to `workspace/inbox/_harvest_log.jsonl` after every run:

```json
{"date": "2026-05-12", "surface": "x-bookmarks", "new_items": 38, "auto_absorbed": 0, "queued_for_review": 2, "archived_stale": 0}
```

Morning digest (already wired) reads this. Daily brief includes:

```
Last 24h: 47 items captured, 0 routed, 4 absorbed, 0 archived
Save-to-Action ratio: 8.5% (you hoarded 91.5%)
Largest source: x-bookmarks (38 items)
Throttle adapter? [boubacar decides]
```

Threshold in `config/auto_absorb_rules.json`: if `sum(new_items last 7 days) > 200`, flag in digest. Configurable, not enforced.

### 10. Files to create

```
scripts/web-session-harvester/
  runner.py                          # cron entrypoint
  auto_absorb.py                     # hardcoded heuristic
  sync_sessions.py                   # local → VPS state-file scp helper
  config/
    auto_absorb_rules.json           # keyword list + watch handles + hoarder threshold
  adapters/
    __init__.py                      # adapter registry
    skool/
      __init__.py                    # exposes contract; wraps existing scripts
      skool_login.py                 # MOVED from scripts/skool-harvester/
      skool_harvest.py               # MOVED
      skool_walk.py                  # MOVED
    x/
      __init__.py
      x_login.py                     # headed Playwright → x.json
      x_harvest.py                   # infinite scroll bookmarks
    yt/
      __init__.py
      yt_login.py                    # headed Playwright → yt.json
      yt_harvest.py                  # WL playlist scraper

~/.claude/skills/web-session-harvester/
  SKILL.md                           # replaces skool-harvester/SKILL.md

workspace/inbox/
  _harvest_log.jsonl                 # appended per run
  _absorb_queue.jsonl                # pending manual absorb review
  _status.json                       # auth_needed flags per surface
  _index.jsonl                       # Phase C corpus (CONTRACT)
  <surface>/YYYY-MM-DD/<slug>/item.json
  <surface>/YYYY-MM-DD/<slug>/downloads/

/etc/cron.d/web-session-harvester    # VPS cron (deploy via ssh)
C:\Windows\... or local launchd      # Local X cron (Windows Task Scheduler)
```

**Modify:**
- `C:\Users\HUAWEI\.claude\skills\skool-harvester\SKILL.md` → archive in place with deprecation header
- `docs/SKILLS_INDEX.md` → replace skool-harvester entry with web-session-harvester
- `~/.claude/projects/.../memory/MEMORY.md` → add reference line under Workflow/SOP

---

## Risk register

**Risk 1 — X TOS / bot detection.**
X prohibits automated scraping. VPS IP + fixed cron = bot pattern.
**Mitigation:** X adapter runs LOCAL Windows only (Task Scheduler). 1.5-3.5s random scroll jitter. Cap X harvest at 50 items/run default (config-tunable). VPS handles skool + YT only.

**Risk 2 — Session expiry breaks silent cron.**
Expired session = harvester produces zero items, no error.
**Mitigation:** `check_session()` probes before every harvest. `auth_needed: true` flag in `_status.json`. Telegram alert via `notifier.send_message()` immediately (NOT deferred to morning digest). Alert message includes exact login command.

**Risk 3 — Auto-absorb false positives flood absorb-log.**
Keyword-match on tweets/videos = noisy until Phase B LLM router.
**Mitigation:** Phase A autonomous absorb gated to skool lessons w/ downloadable artifacts only (proven low-false-positive). Tweets + YT videos → manual-review queue, not autonomous. Tune keyword list after 2 weeks of real data.

---

## Phase C contract (for /recall, post-Phase-A)

Phase C reads `workspace/inbox/_index.jsonl` as its corpus + greps:

- MEMORY.md index + topic files
- `docs/handoff/*.md`
- `skills/*/SKILL.md`

Returns top 5 matches with source attribution + date. Phase A guarantees `_index.jsonl` is the single source of truth — Phase C does not read raw item.json paths except via item_path field.

---

## Build sequence (Phase A)

Build order — ship incrementally:

1. **Port skool → adapter pattern** (~2hr). Refactor existing scripts into `adapters/skool/`. Verify existing skool workflow still works via new entrypoint. Foundation for adapter contract.
2. **Build x-bookmarks adapter** (~4-6hr). Local Windows. `x_login.py` headed Playwright → save `x.json`. `x_harvest.py` infinite scroll → write items. Test on Boubacar's actual bookmarks.
3. **Build yt-watch-later adapter** (~2-3hr). VPS-compatible. `yt_login.py` headed (local only) → save `yt.json`. `yt_harvest.py` reads WL playlist → write items (URL+title only).
4. **runner.py** (~2hr). Calls each adapter. Writes `_index.jsonl` + `_harvest_log.jsonl`.
5. **auto_absorb.py** (~1hr). Hardcoded heuristic rules.
6. **Cron deploy** (~30min). VPS cron entry + sync `*.json` state files via `sync_sessions.py`.
7. **Local X cron** (~30min). Windows Task Scheduler for X adapter.
8. **Morning digest extend** (~1hr). Add hoarder-rate section reading `_harvest_log.jsonl`.

**Total estimate:** 13-16hr build. Target: ship by 2026-05-25 (gives Post 5 publish on 5/18 buffer if Phase A slips → push Post 5 to 5/25 OR flip "I built mine" wording).

---

## Phase A → Post 5 dependency

**Post 5** ("Build Reveal") publish-gated on Phase A. Currently:
- Status=Draft in Notion Content Board
- Scheduled Date 2026-05-18

**Decision rules:**
- Phase A operational (real items in inbox, real auto-absorb firing) by 5/17 → flip Post 5 Status=Queued for 5/18 publish
- Phase A NOT operational by 5/17 → either (a) change "I built mine" → "I am building mine" + ship anyway, or (b) push Scheduled Date to 5/25 (next Monday)

---

## What we explicitly DO NOT build in Phase A

- LinkedIn adapter (Round 2)
- Reddit adapter (Round 2)
- LLM router (Phase B)
- `/recall` query skill (Phase C)
- Weekly "firmware upgrade" auto-refactor of CLAUDE.md/MEMORY.md (drift risk, breaks 200-line cap)
- 5th "cite memory" rule (rejected by council; if needed, pre-tool-use hook is right pattern not memory file)
- Standalone Codex Knowledge Vault repo (already have CLAUDE.md + 74 skills + MEMORY.md)
- Volume cap on cron auto-absorb (replaced by hoarder-rate metric)

---

## Origin

Absorb of Ziwen's "Codex Knowledge Vault" pattern (X post, 2026-05-11). Full reframe: not a "knowledge vault" but an **ingest layer that feeds the systems we already have**. Sankofa council ran on the absorb proposal; verdict was "PROCEED on YT-pipe only, ARCHIVE everything else." Boubacar reframed: build second-brain ingest layer with adapter pattern (generalize skool-harvester), respecting 74-skill ceiling.

See conversation 2026-05-12 (this session) for full council + reframe trace.

Companion content: 5-post "Digital Hoarder" arc shipping 5/12-5/18. Post 5 = build reveal teaser, gated on Phase A operational status.

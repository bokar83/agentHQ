---
name: skool-harvester
description: >
  Harvests Skool community lessons , text, attachments (n8n JSONs, agent template
  zips, PDFs), screenshots, and metadata , into workspace/skool-harvest/<community>/.
  Uses a saved Playwright session at ~/.claude/playwright-state/skool.json so no
  re-login is needed. Trigger on "harvest skool", "scrape skool", "pull skool
  lesson", "/skool-harvester", or when given a skool.com classroom or lesson URL.
---

# Skool Harvester

Pulls lesson content + attachments out of any Skool community where Boubacar is
a member. Designed for the recurring task of mining communities (RoboNuggets,
etc.) for n8n workflows, Claude Code skills, and Antigravity agent templates.

---

## When to use

Trigger phrases:
- "harvest [name] from skool"
- "pull this skool lesson"
- "scrape the [community] classroom"
- "what's in [skool URL]"
- Direct invocation: `/skool-harvester <url>`

Do NOT trigger for:
- Public web scraping (use website-intelligence or Firecrawl).
- Skool pages outside `skool.com/<community>/classroom/...` (this skill assumes
  the lesson player layout).

---

## Prerequisites

1. **Saved login at `~/.claude/playwright-state/skool.json`.**
   If missing or expired, run:
   ```
   python d:/Ai_Sandbox/agentsHQ/scripts/skool-harvester/skool_login.py
   ```
   A real Chrome window opens. Log in. Script auto-detects login and saves the
   state file. Re-run only when Skool logs you out (rare; weeks-to-months).

2. **Python + Playwright installed** , already true on this machine
   (`playwright==1.58`, browsers in `~/AppData/Local/ms-playwright/`).

---

## Four modes

### Mode A , single lesson (spot check)

Use when you have one lesson URL.

```bash
cd d:/Ai_Sandbox/agentsHQ/scripts/skool-harvester
python skool_harvest.py "<lesson_url>" "<output_subdir>"
```

Writes to `workspace/skool-harvest/<community>/<output_subdir>/`. Community slug
is parsed from the URL automatically. Per-lesson artifacts:
- `screenshot.png` , full-page screenshot
- `page.html` , raw HTML
- `text.txt` , visible text
- `links.json` , all links on the page
- `attachments_meta.json` , Skool resource metadata (file_id, name, content type)
- `downloads/` , actual downloaded files (n8n JSONs, zips, PDFs)
- `downloads_log.json` , download URLs + sizes
- `media.json` , videos and iframes
- `network_interesting.json` , JSON / file responses captured during load
- `summary.json` , one-line metrics

### Mode B , list classroom (top-level only, FAST)

Use to see what is in a classroom. ~10 seconds even for 80+ courses.

```bash
python skool_walk.py "https://www.skool.com/<community>/classroom" --list
```

Paginates the classroom (`?p=1`, `?p=2`, ...) until empty. Reads the
`__NEXT_DATA__` SSR payload to extract every course with its module count,
title, slug, access flag, and timestamps. Does NOT visit each course detail
page. Saves `_index.json` with the course list.

### Mode C , list classroom (deep, every lesson enumerated)

Use when you need a full lesson index, e.g. before a planned harvest.

```bash
python skool_walk.py "https://www.skool.com/<community>/classroom" --list --deep
```

After the shallow walk, also visits each accessible course page and reads its
`course.children` tree to enumerate every lesson (modules and modules nested
inside sets). Slow: roughly 1 page load per course (~3 minutes for 78 courses).

### Mode D , diff or full sweep harvest

```bash
# Show only lessons not yet harvested (always deep)
python skool_walk.py "<classroom_url>" --new

# Harvest every lesson in the classroom; skip already-harvested
python skool_walk.py "<classroom_url>" --all

# Re-harvest everything
python skool_walk.py "<classroom_url>" --all --force

# Harvest only the next N lessons (good for first runs)
python skool_walk.py "<classroom_url>" --all --max 5
```

Both `--new` and `--all` always do a deep walk, since they need lesson IDs.
The index keeps a `harvested_at` timestamp per lesson so reruns of `--new` and
`--all` only do the delta. Re-running after RoboNuggets adds new lessons just
finds and harvests the new ones automatically.

---

## Pattern recognition (what to look for in harvest output)

When reviewing a lesson's `downloads/`:

| Filename pattern | Likely content | What to do |
|---|---|---|
| `*.json` ~50-200 KB | n8n workflow export | Open, count nodes, list node types, find sticky notes for instructions. Compare patterns to existing n8n workflows before importing. |
| `*-template-community.zip` ~5-50 MB | Antigravity / Claude Code agent pack | Unzip. Look for `.agent/AGENT.md`, `.agent/skills/`, `tools/`, `references/`. Extract reusable parts (skills, prompt scripts, useful Python tools). |
| `*.pdf` | Slides or notes | Read for prompts, frameworks, diagrams worth banking in `docs/reference/`. |

When reviewing `text.txt` and `links.json`:
- "Set up instructions & ..." or "Set Up" links usually point to a sibling page
  (same lesson family, different `md=` query param) where the actual file lives.
  Always harvest the sibling too if the main lesson is light on text.
- Look for explicit MCP server config blocks , they often appear inline.
- "Resources" section at bottom typically lists external partner links worth
  catching.

---

## Decision rules: what to take from a harvested lesson

**Take and adapt** when the artifact:
- Targets a tool already in our stack (Kie AI, Notion, Supabase, Modal, etc.).
- Solves a problem we have a roadmap entry for (e.g. Blotato while M7a is open).
- Provides reusable prompt or interview scripts.

**Reference only (don't copy)** when:
- It's a complete agent template using a stack we don't share (Airtable + Modal-only).
- The pattern is good but the implementation conflicts with our conventions.

**Skip** when:
- Tool is explicitly out of scope (Airtable per CRM strategy).
- Pattern is already better-covered by an existing skill.
- It's marketing fluff with no technical artifact.

---

## Output destination

Default: `d:/Ai_Sandbox/agentsHQ/workspace/skool-harvest/<community>/<lesson_slug>/`.

The `workspace/` dir is gitignored, so harvest output stays local. Promote
useful artifacts (a workflow JSON, a skill, a prompt script) into:
- `skills/<name>/` for Claude Code skills.
- `orchestrator/` for Python tools wired into crews.
- `docs/reference/` for prompt/interview scripts.
- `n8n/imported/` for raw workflow JSONs (create this dir on first use).

Always commit the **adapted** version, never the raw harvested file.

---

## Common pitfalls

- **`networkidle` never fires on Skool.** The lesson player keeps a long-poll
  open. Use `domcontentloaded` + manual settle (already done in script).
- **Clicking the resource label opens a preview, not a download.** Real download
  trigger is a `button:has-text("Download")` inside the preview modal (already
  handled in script).
- **Light lesson body.** Some lessons have most content rendered server-side and
  most content lives on the "Set Up" sibling page. If `text.txt` is < 1 KB,
  check `links.json` for a sibling `md=` URL and harvest that too.
- **Session expires.** Cookies last weeks but not forever. If harvest hits a
  login wall, re-run `skool_login.py`.
- **Emoji in lesson titles crash on Windows (cp1252).** `page.title()` on Windows raises `UnicodeEncodeError: 'charmap' codec can't encode character` when lesson titles contain emoji (e.g., "🍌 Pro"). Fix already applied in skool_harvest.py line 87: `print(f"[harvest] title: {page.title().encode('ascii', 'replace').decode()}")`. If the script is updated or copied, carry this pattern forward.

---

## Files

- `scripts/skool-harvester/skool_login.py` , one-time login, saves state.
- `scripts/skool-harvester/skool_harvest.py` , single-lesson harvester.
- `scripts/skool-harvester/skool_walk.py` , classroom walker (`--list`,
  `--list --deep`, `--new`, `--all`).
- `~/.claude/playwright-state/skool.json` , session cookies + localStorage.
- `workspace/skool-harvest/<community>/_index.json` , durable lesson catalog
  with `harvested_at` timestamps; the diff between runs is what `--new` shows.
- `workspace/skool-harvest/<community>/<lesson_id>/` , per-lesson harvest output.

## Discovery internals (for the curious)

Skool's classroom is a paginated Next.js app. The walker exploits that:

- Each `?p=N` page embeds the next 30 entries in
  `<script id="__NEXT_DATA__">` as `props.pageProps.allCourses`.
- Each course detail page embeds its module tree at
  `props.pageProps.course.children`. Modules have `unitType: "module"`;
  folders are `unitType: "set"` and recurse.
- Lesson URLs are `/<community>/classroom/<course_slug>?md=<lesson_id>`. The
  walker constructs them from the SSR data; no DOM scraping needed.

If Skool changes the SSR shape, re-run the probe scripts under
`scripts/skool-harvester/probe_*.py` to confirm the new keys.

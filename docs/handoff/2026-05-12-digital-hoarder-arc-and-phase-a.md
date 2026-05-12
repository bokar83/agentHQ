# Session Handoff — Digital Hoarder Arc + Phase A Spec — 2026-05-12

## TL;DR

Absorbed Ziwen's "Codex Knowledge Vault" X post via `/agentshq-absorb`. Reframed
his Obsidian-shaped solution into an agentsHQ-shaped one: not a "knowledge
vault" but an **ingest layer** that feeds existing systems (Notion, MEMORY.md,
74 skills, /agentshq-absorb). Sankofa council ran on the proposal. Three-phase
build agreed: Phase A foundation (web-session-harvester w/ skool + x-bookmarks
+ yt-watch-later adapters) → Phase C query surface (/recall) → Phase B LLM
router last. Phase A spec written, build starts 2026-05-12, target ship
2026-05-25.

Companion content arc: 5-post "Digital Hoarder" series, CTQ-passed (9-9.5/10
scores), all 10 records written to Notion Content Board. Ships 5/12-5/18 via
Blotato (Post 3 X manually scheduled by Boubacar in X for 5/14 = marked
Posted in advance). Post 5 (build reveal) Status=Draft pending Phase A
operational by 5/18.

## What was built / changed

**Phase A spec (committed + pushed, Gate-pending):**
- `docs/roadmap/atlas-second-brain-phase-a.md` (NEW, 289 lines) — full spec
  for `web-session-harvester` skill. Adapter contract, output schema, session
  management, cron config, auto-absorb heuristic, hoarder-rate metric, file
  manifest, build sequence (13-16hr estimate), risk register, Phase C contract.
- `docs/roadmap/atlas.md` — added item 3a in default-next-moves pointing to
  Phase A spec.

**Followup logged:**
- `docs/reviews/absorb-followups.md` — appended Phase A build entry, target
  2026-05-25.

**Content drafts (workspace/, gitignored):**
- `workspace/content-ideas/2026-05-12-digital-hoarder-V5-FINAL.md` (Post 1, CTQ 9.5/10)
- `workspace/content-ideas/2026-05-12-digital-hoarder-POST2.md` (Post 2, Story PASS)
- `workspace/content-ideas/2026-05-12-digital-hoarder-POST3.md` (Post 3, Boubacar raw)
- `workspace/content-ideas/2026-05-12-digital-hoarder-POST4.md` (Post 4, CTQ 9/10)
- `workspace/content-ideas/2026-05-12-digital-hoarder-POST5.md` (Post 5, CTQ 9/10, gated)

**Notion Content Board (10 new records):**
| Post | X | LinkedIn |
|---|---|---|
| 1 | Queued 5/12 | Queued 5/12 |
| 2 | Queued 5/13 | Queued 5/13 |
| 3 | **Posted 5/14** (manual) | Queued 5/14 |
| 4 | Queued 5/15 | Queued 5/15 |
| 5 | **Draft** (Phase A gated) | **Draft** (Phase A gated) |

**Memory files added (3, outside repo):**
- `feedback_no_signature_line_on_posts.md` — never sign LinkedIn/X posts with "— Boubacar"
- `feedback_story_review_protect_raw.md` — Story Review = protect voice, parentheticals are voice, show raw vs polish side-by-side
- Updated `MEMORY.md` — both rules indexed under Communication / Voice

## Decisions made

1. **web-session-harvester replaces skool-harvester** via adapter pattern. Existing skool scripts become `adapters/skool/`. No skill-count growth.
2. **X adapter runs LOCAL Windows only** (not VPS). TOS mitigation — VPS IP + fixed cron flagged as bot pattern.
3. **YT WL adapter records URL+title only** in Phase A. No inline transcription. Hand off to existing `transcribe` skill via Phase B decision.
4. **Cron green-lit, no volume cap.** Hoarder-rate metric in morning digest instead. User decides throttling, not system.
5. **Build order: Phase A → C → B.** Phase C (/recall query surface) is the test harness for Phase B (LLM router). B is guessing without C.
6. **Sabbath enforced via cron schedule itself** (M-F + Sat-lite, no Sunday).
7. **Auto-absorb in Phase A = hardcoded heuristic.** LLM router = Phase B. Skool lessons w/ downloadable artifacts only auto-absorb. Tweets + YT → manual-review queue.
8. **Post 5 publish gated on Phase A operational by 5/17.** If slips: change "I built mine" → "I am building mine" OR push to 5/25.
9. **No signature on social posts.** Standing rule, indexed in MEMORY.md.
10. **Story Review = protect raw voice.** Standing rule, indexed in MEMORY.md.

## What is NOT done (explicit)

- **Phase A build itself.** Spec only. Build starts 2026-05-12 (Boubacar wake).
- **VPS Postgres `memory` table writes** (Step 2b of tab-shutdown skill). Skipped — flat files cover the rules. Add to Phase A build session if time.
- **Memory archive trim.** MEMORY.md is at acceptable size (~150 lines target hit), no archive trim needed.
- **VPS deployment of Phase A spec.** Sitting on `compass/c8-c9-memory-hygiene` branch awaiting Gate merge. Gate watches every 5 min. Expected live within 30 min of push.

## Open questions

- **Phase A build start time tomorrow** — Boubacar said "when I wake up." First action = port skool adapter (~2hr).
- **X adapter local cron mechanism** — Windows Task Scheduler vs PowerShell scheduled task vs manual trigger. Decide at build time.
- **YT WL Whisper trigger** — Phase B will decide which videos auto-transcribe. Until B ships, manual `/transcribe` on demand.

## Next session must start here

1. **Verify Gate merged branch.** Check `git -C d:/Ai_Sandbox/agentsHQ pull origin main && git log --oneline -3 main` — confirm `489402c docs(roadmap)` is in main. If not after 30 min, debug Gate.
2. **Read Phase A spec.** `docs/roadmap/atlas-second-brain-phase-a.md`. Internalize adapter contract + output schema + build sequence.
3. **Start build — Step 1 of sequence:** port skool scripts to adapter pattern. ~2hr. Refactor `scripts/skool-harvester/*.py` into `scripts/web-session-harvester/adapters/skool/`. Verify existing skool workflow still works via new entrypoint. Move skool-harvester SKILL.md to deprecation header pointing to web-session-harvester.
4. **Check Blotato fired Post 1.** Should have published to X + LinkedIn on 5/12. Confirm `auto_publisher` logs in VPS: `docker logs orc-crewai --tail 50 | grep -i "blotato\|publish"`. If fail: check Notion Status field — should be Posted not Publishing.
5. **Confirm Post 2 queued for 5/13.** Same check, different date.

## Files changed this session

```
d:/Ai_Sandbox/agentsHQ/
├── docs/
│   ├── roadmap/
│   │   ├── atlas.md (modified, item 3a added)
│   │   └── atlas-second-brain-phase-a.md (NEW)
│   ├── reviews/
│   │   └── absorb-followups.md (appended)
│   └── handoff/
│       └── 2026-05-12-digital-hoarder-arc-and-phase-a.md (NEW, this file)
└── workspace/content-ideas/ (gitignored, local only)
    ├── 2026-05-12-digital-hoarder.md
    ├── 2026-05-12-digital-hoarder-FINAL.md (V1 superseded)
    ├── 2026-05-12-digital-hoarder-V2.md (superseded)
    ├── 2026-05-12-digital-hoarder-V4.md (superseded)
    ├── 2026-05-12-digital-hoarder-V5-FINAL.md (Post 1 SHIP)
    ├── 2026-05-12-digital-hoarder-POST2.md (Post 2 SHIP)
    ├── 2026-05-12-digital-hoarder-POST3.md (Post 3 SHIP)
    ├── 2026-05-12-digital-hoarder-POST4.md (Post 4 SHIP)
    └── 2026-05-12-digital-hoarder-POST5.md (Post 5 SHIP, Phase A gated)

C:/Users/HUAWEI/.claude/projects/d--Ai-Sandbox-agentsHQ/memory/ (outside repo)
├── MEMORY.md (modified — Communication/Voice section)
├── feedback_no_signature_line_on_posts.md (NEW)
└── feedback_story_review_protect_raw.md (NEW)
```

**Commits:**
- `489402c` docs(roadmap): Atlas Phase A second-brain ingest layer spec
- `50edc38` chore: re-signal [READY] after docs commit

**Branch:** `compass/c8-c9-memory-hygiene` (Gate-pending)
**Pushed:** YES
**VPS live:** PENDING Gate merge (expected within 30 min)

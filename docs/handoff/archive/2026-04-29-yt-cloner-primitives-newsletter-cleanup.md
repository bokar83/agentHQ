# Session Handoff - YT Cloner Primitives + Newsletter Content Board Cleanup - 2026-04-29

## TL;DR

Started with strategist analysis of a YouTube channel-cloning video. Sankofa Council overruled selling it as a $497 audit SKU and redirected to internal primitive. Built and smoke-tested two foundation skills (`transcript-style-dna`, `scene-segmenter`). Boubacar opted to add the full cloner pipeline as Studio M3.5 (post-M3) rather than Harvest. M3.5 milestone written into studio roadmap with full sub-skill table. Then cleaned up the Issue 2 weekly signal newsletter Content Board record, added Newsletter+Beehiiv as schema options, and ran the segmenter on the actual posted text (42 beats, clean output). Two memory entries written, MEMORY.md at 193 lines.

---

## What was built / changed

### New skills (foundation for Studio M3.5 cloner pipeline)

**transcript-style-dna**: voice fingerprint extractor
- `skills/transcript-style-dna/SKILL.md`
- `skills/transcript-style-dna/extract.py`: N reference texts + target context → JSON style profile + opener line, single Sonnet 4.6 call
- `skills/transcript-style-dna/samples/`: 3 LinkedIn-style roofer posts for smoke testing
- Em-dash ban enforced via prompt rule + `_scrub()` recursive post-process
- Smoke test on Bill at Acme Roofing: high confidence, opener in voice, zero dashes
- Indexed in `skills/_index.md` line 60 (revenue category)

**scene-segmenter**: script to scene beats
- `skills/scene-segmenter/SKILL.md`
- `skills/scene-segmenter/segment.py`: script + style profile → ~167 paired image+video prompts at 200 wpm
- `skills/scene-segmenter/samples/sample_script.txt` (c0mrade hacker history, 437 words)
- Same em-dash scrub pattern as transcript-style-dna
- Smoke tests: 36 beats on c0mrade script, 42 beats on Issue 2 newsletter, both clean
- Indexed in `skills/_index.md` line 53 (media category)

### Studio roadmap

- `docs/roadmap/studio.md`: added **M3.5 Channel Cloner Pipeline** between M3 and M4
- Full pipeline shape (12 steps), sub-skill table with status, IP/policy risk flagged
- Trigger: post-M3 (do not start orchestrator until M3 produces working video)

### Newsletter Issue 2 Content Board cleanup

- Page `350bcf1a-3029-81a3-a9a2-c07dfd211a21` updated:
  - Status: Draft → Published
  - Posted Date: empty → 2026-04-28
  - Title: corrected to "...Before You Buy Another AI Tool, Read This"
  - Hook: "The most expensive mistake in AI adoption is not the wrong tool. It's skipping the diagnosis."
  - Topic: AI, AI Strategy, Catalyst Works
  - Type: Newsletter (new schema option)
  - Platform: Beehiiv (new schema option)
  - Format: Long-form article
  - Agent: Boubacar
  - Content Type: Timely
  - Draft: replaced fabricated-Sarah Drive draft with actual posted text
  - Source Note: notes beehiiv URL gap, rewrite vs Drive divergence, thumbnail link
- Schema additions (persistent for all future records):
  - `Type` SELECT now includes "Newsletter"
  - `Platform` MULTI_SELECT now includes "Beehiiv"

### Local newsletter files

- `workspace/newsletter/issue2-final.md`: pre-rewrite Drive draft (with fabricated Sarah hook), pulled from Drive
- `workspace/newsletter/issue2-posted.md`: actual posted text Boubacar provided in chat
- `workspace/scenes/issue2-newsletter.json`: segmenter output, 42 beats

### Memory writes

- `memory/project_channel_style_dna_audit.md`: original $497 SKU recommendation, then KILLED status, lift test contract by 2026-06-01
- `memory/project_studio_m35_cloner.md`: M3.5 milestone summary, sub-skill table, trigger conditions
- `memory/feedback_em_dash_scrub_pattern.md`: prompt + scrub pattern for LLM JSON output
- `memory/reference_content_board_type_vs_platform.md`: Type=what, Platform=where; pattern for new channels
- `MEMORY.md` index updated (193 lines, under 195 cap)
- `MEMORY_ARCHIVE.md`: both project pointers added

---

## Decisions made

1. **Kill the $497 Channel Style DNA Audit SKU.** Sankofa Council overruled the original recommendation. Reason: wrong-ICP buyer wallet (faceless YouTubers don't pay $497), brand collision with Signal Session, IP cover story too thin. Build the primitive private; sell nothing new.
2. **Internal-only wire-in for transcript-style-dna.** Two cash-path use sites: Signal Works cold outreach personalization, Catalyst Works pre-discovery prep. Studio M2 niche research cut from initial scope until lift test resolves.
3. **30-day lift test, then delete or keep.** By 2026-06-01: +20% reply rate on cold outreach OR +1 close on a discovery call that would have stalled. Neither = delete the skill, no iteration.
4. **YouTube channel cloner goes on Studio roadmap, not Harvest.** Studio M3.5, post-M3 trigger. Cloner is a faceless agency production capability, not a Catalyst Works revenue lane.
5. **Build cloner sub-skills incrementally as foundation work.** Two shipped today (transcript-style-dna, scene-segmenter). Four remaining (channel-branding-kit, video-idea-generator, kie_media reference-consistency upgrade, thumbnail-reverse-engineer) plus orchestrator. ~10 hr total. Build independently in spare cycles; orchestrator gated on M3.
6. **Content Board Type vs Platform separation.** Type = what (Newsletter is the content shape). Platform = where (Beehiiv is the channel). Cross-posting adds Platforms, doesn't change Type.
7. **No external lander for the cloner work.** Confirmed by Boubacar after Sankofa.

---

## What is NOT done (explicit)

- **Specific Beehiiv post URL for Issue 2 not in record.** Boubacar needs to grab the post URL from beehiiv UI and paste it (or I add a `Beehiiv Posted URL` field via ALTER COLUMN if newsletter cross-posting becomes routine).
- **transcript-style-dna NOT wired into Signal Works runner.** `email_builder.py::_opening()` not modified yet. Wire-in spec is documented in SKILL.md. Will fire on next real prospect.
- **transcript-style-dna NOT wired into engagement-ops.** Will activate on next discovery call.
- **scene-segmenter NOT used for production video yet.** Issue 2 segmenter output exists at `workspace/scenes/issue2-newsletter.json`; not rendered into actual video.
- **Drive copy of Issue 2 still has fabricated Sarah-COO draft.** Notion `Draft` field now has the posted version, but Drive file `1MDM5jV-UAQDDlvagCTaB6nE-cPjoRA49` was not overwritten.
- **Cloner sub-skills 3-6 not built:** channel-branding-kit, video-idea-generator, kie_media reference-consistency upgrade, thumbnail-reverse-engineer. ~10 hr remaining.
- **Cloner orchestrator not built.** Gated on Studio M3 producing a working video first.
- **No git commit.** All changes uncommitted as of session end.

---

## Open questions

- Does Boubacar want a dedicated `Beehiiv Posted URL` field on the Content Board? (One ALTER COLUMN, persistent.) Useful if newsletters become routine.
- Should the Drive copy of Issue 2 be overwritten with the posted text? Currently Drive = pre-rewrite, Notion = posted. Notion is the better canonical source.
- Studio M3 trigger conditions for starting M3.5 orchestrator: is Boubacar tracking M3 status anywhere? Roadmap status snapshot still shows "M3 QUEUED."
- 30-day lift test for transcript-style-dna runs to 2026-06-01. Does Boubacar want a scheduled agent to evaluate at that date and trigger keep/delete decision?

---

## Next session must start here

1. **Check git status** in `d:/Ai_Sandbox/agentsHQ`. All session work is uncommitted. Decide: commit + push, or keep uncommitted.
2. **Optionally grab the Beehiiv Issue 2 URL** from beehiiv UI and patch the Notion record's Source Note (or add a Beehiiv Posted URL field if cross-posting will recur).
3. **Pick the next cloner sub-skill** if continuing M3.5 foundation work. Recommended order: `channel-branding-kit` (~2 hr) since it doubles as Studio M2 (First Generation Money channel branding).
4. **Or pivot to cash-path work**: wire `transcript-style-dna` into Signal Works `email_builder.py::_opening()` so it actually fires on next prospect batch. Spec is in SKILL.md.
5. **Optional**: schedule the 2026-06-01 lift-test evaluation agent for transcript-style-dna.

---

## Files changed this session

```
skills/transcript-style-dna/                            (NEW skill)
  SKILL.md                                              (NEW)
  extract.py                                            (NEW)
  samples/sample_roofer_post1.txt                       (NEW)
  samples/sample_roofer_post2.txt                       (NEW)
  samples/sample_roofer_post3.txt                       (NEW)

skills/scene-segmenter/                                 (NEW skill)
  SKILL.md                                              (NEW)
  segment.py                                            (NEW)
  samples/sample_script.txt                             (NEW)

skills/_index.md                                        (MOD: +2 entries)
docs/roadmap/studio.md                                  (MOD: +M3.5 milestone)

workspace/style-dna/acme-roofing-test.json              (NEW: smoke test)
workspace/scenes/comrade-test.json                      (NEW: smoke test)
workspace/scenes/issue2-newsletter.json                 (NEW: production-ready)
workspace/newsletter/issue2-final.md                    (NEW: Drive draft)
workspace/newsletter/issue2-posted.md                   (NEW: real posted text)

~/.claude/skills/scene-segmenter/SKILL.md               (NEW: global sync)

~/.claude/projects/.../memory/
  project_channel_style_dna_audit.md                    (NEW)
  project_studio_m35_cloner.md                          (NEW)
  feedback_em_dash_scrub_pattern.md                     (NEW)
  reference_content_board_type_vs_platform.md           (NEW)
  MEMORY.md                                             (MOD: +2 pointers)
  MEMORY_ARCHIVE.md                                     (MOD: +2 project pointers)

Notion Content Board:
  Schema: Type +Newsletter, Platform +Beehiiv
  Page 350bcf1a-3029-81a3-a9a2-c07dfd211a21 (Issue 2): full property update
```

# Homelab: Local AI Workstation Build (Deferred)

**Codename:** homelab
**Status:** deferred (parked, watching triggers)
**Lifespan:** open-ended
**Started:** 2026-05-14 (spec date)
**Earliest reopen:** 2026-11-14 (6-month time gate)
**Owner:** Boubacar Barry
**One-line:** own the compute. Build a local RTX-class AI workstation as personal infrastructure for inference / agentic work / model experimentation. Not client-driven, not revenue-tied. Sovereignty over rented compute.

---

## Why This Is Deferred (Not Killed)

Boubacar 2026-05-14: "I want my own build eventually to have more control and to be able to do more testing and other things and not be at the mercy of the big organizations. I will be able to update the models whenever I want to update them and use some of the lower-cost free tiers that exist. Eventually I will build my own system. It's not a question of if but when."

- NOT tied to client demand. Personal-infrastructure capex.
- NOT happening in the next 5-6 months minimum (so Q4 2026 earliest reopen).
- IS happening eventually. Plan is intent-locked. Timing is condition-gated.

This roadmap exists so the spec + Council verdict + trigger conditions do not get lost between now and reopen.

---

## Done Definition

A working local AI workstation in Boubacar's home office that:
- Runs 32B-class LLMs at Q4-Q5 daily at ≥20 t/s
- Runs Whisper Large v3 at RTF ≥20x
- Runs SDXL at <3s/image (1024x1024, 30 steps)
- Accessible from anywhere via Tailscale, zero public ports
- Encrypts client data at rest (LUKS)
- Survives 18 months without rebuild

Re-scoping rule: only Boubacar changes the goalpost. Architecture choice (single 3090 vs dual 3090 vs Apple Silicon vs newer card) re-decides at trigger time, not now.

---

## Status Snapshot (2026-05-14)

- **Full build spec researched.** Component table, vendor URLs, prices, software stack, security posture, performance targets all documented.
- **Council stress-test complete.** 3-way split verdict: spend-more (dual-3090), spend-less (Mac Mini + cloud rental), spend-nothing-until-validated.
- **Spec snapshot** lives in memory: `reference_local_ai_build_spec_2026-05-14.md`.
- **Project status memory:** `project_homelab_build_deferred.md`.
- **Cloud interim path approved** as bridge (NOT permanent): OpenRouter for API work + RunPod Secure on-demand for occasional heavy jobs + Hostinger VPS for orchestration.
- **Cloud is explicitly NOT the destination.** Boubacar rejected cloud-only as a permanent posture.
- **Zero hardware purchased.** Zero buy-trigger fired.

---

## Triggers (parked work resumes when ANY ONE fires AFTER 2026-11-14)

### Time gate (hard floor)

**G1 — Earliest reopen date: 2026-11-14.** No hardware research, no price-checking, no spec updates before this date. Spec will be stale by then anyway, so the first action on reopen is re-research.

### Demand gates (any of)

**G2 — MRR trigger.** Catalyst Works MRR ≥ $5K sustained 90 days. Original Boubacar buy-trigger.

**G3 — Inference-hours trigger.** Logged 100+ hours/month sustained personal inference via cloud (RunPod / OpenRouter) for 3 consecutive months. Demonstrates real demand for owned compute.

**G4 — Cloud-spend trigger.** Monthly cloud-GPU spend crosses $200 sustained for 3 months. Cloud TCO is approaching break-even with local hardware.

### Market gates (any of)

**G5 — GPU market shift.** ONE of:
- Used RTX 5090 32GB drops to $800-$1,000 range
- Used dual-3090 NVLink kits drop to $1,500 combined
- New consumer card with 32GB+ VRAM under $1,200 ships

**G6 — Open-weights MoE shift.** Frontier open model under 50GB at Q4 quant becomes the daily-driver standard. Changes the VRAM floor calculus from "24GB barely viable" to "24GB plenty."

### Soft signals (flag for review, do NOT auto-resurrect)

- Apple announces M4/M5 Ultra Mac Studio at 256GB+ unified memory ≤ $4K
- NVIDIA ships consumer Blackwell refresh with FP4 at sub-$1K
- A client signs a contract explicitly requiring no-cloud inference (would tilt architecture, not timing)

---

## On Reopen, Run These In Order

1. Read `project_homelab_build_deferred.md` (motivation + trigger context).
2. Read `reference_local_ai_build_spec_2026-05-14.md` (component snapshot — prices stale, treat as starting frame).
3. Re-run live pricing research across Newegg + Amazon + B&H + Microcenter for all components.
4. Re-research used GPU market: eBay sold listings + r/hardwareswap + KSL Classifieds Utah + FB Marketplace SLC.
5. Verify Utah ZIP 84095 combined sales tax (was 7.45% on 2026-05-14).
6. Re-run `/council` on the architecture choice with then-current data. The 2026-05-14 council split 3 ways; re-resolve at decision time.
7. Decide architecture: single 3090, dual 3090 NVLink, used 5090, Apple Silicon, or other. Lock and commit.
8. Promote first build milestone (M1: order parts) to active.

---

## Architecture Options (carry-over from 2026-05-14 Council)

| Option | Price snapshot | Future-proof verdict (May 2026) |
|---|---|---|
| Single 3090 24GB + 7900X | $2,404 | 12-month bridge, mislabeled as 18-month anchor |
| Dual 3090 NVLink + collapsed NAS (Proxmox) | $3,200 | Council-recommended. Fits 70B Q5 fully, escape hatch through 2028 |
| Used 5090 32GB + 7900X | $3,000+ (price-gated until 5090 used market opens) | Best if G5 fires |
| Mac Studio M3 Ultra 96GB | $4,000-$4,800 | Best if user values silence + zero admin |
| Cloud-only (RunPod + OpenRouter) | ~$50-200/mo | Boubacar already rejected as permanent. Bridge only. |

Re-decide at trigger time. Do not lock now.

---

## Descoped Items (explicit no-builds)

- **Full model training.** Not the use case. LoRA on 7-13B max. Single 24GB or 32GB card is enough.
- **Cloud-permanent solution.** Explicitly rejected by Boubacar 2026-05-14. Cloud is a bridge until hardware ships.
- **HIPAA / regulated-data tier.** Not in scope. Tier 2 privacy posture (SOC2 cloud or local Tailscale) is the floor.
- **Multi-machine cluster / homelab rack.** Single-box build. NAS may collapse into same chassis (Council Expansionist), but no rack.
- **Buying before time gate (2026-11-14).** Hard floor. No exceptions short of major market shift documented in session log.

---

## Session Log

### 2026-05-14 — Roadmap stub + spec research + Council stress-test

**What changed:**
- Full RTX-3090 + Ryzen 7900X build spec researched live across Newegg / Amazon / B&H. Component table, vendor URLs, prices captured.
- Used 3090 market researched: eBay sold $700-$1,100, r/hardwareswap $700-$850, no local SLC pickups verified.
- Utah ZIP 84095 sales tax verified: 7.45% combined.
- 6 perf benchmarks captured (Llama 8B/32B/70B, Qwen 32B, DeepSeek R1, Whisper, SDXL, BGE-M3).
- NAS path researched: TrueNAS Scale DIY recommended at ~$1,650.
- Council stress-test ran. 3-way split on architecture. Verdict: single-3090 spec is "12-month bridge mislabeled as 18-month anchor." Dual-3090 NVLink + collapsed NAS at $3,200 is the Council-preferred future-proof option.
- Cloud interim path defined: Hostinger VPS for orchestration + OpenRouter for API + RunPod Secure on-demand for heavy jobs.
- Boubacar set deferral: 6 months minimum, not client-tied, personal-sovereignty motivation.

**What's next (on reopen, NOT now):**
- Wait for time gate (2026-11-14) AND one demand/market trigger.
- Until then: monitor cloud spend, log inference hours, watch used GPU market quarterly.

**Memory writes this session:**
- `project_homelab_build_deferred.md` (project status + triggers)
- `reference_local_ai_build_spec_2026-05-14.md` (spec snapshot)
- MEMORY.md index updated

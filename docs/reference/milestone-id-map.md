# Milestone ID Map

Prefix convention: first letter of roadmap codename. Introduced 2026-05-10.
Use this when referencing milestones in any context (Telegram, chat, code, docs).

| Prefix | Roadmap | Example |
|--------|---------|---------|
| A | Atlas (autonomy layer) | A1, A26, A9d |
| E | Echo (async queue) | E1, E3 |
| C | Compass (governance) | C0, C2.5b |
| S | Studio (content agency) | S1, S3.4 |
| H | Harvest (revenue pipeline) | H1, H7, H-news |
| L | Lighthouse (12-wk revenue sprint) | L0-L7 lifecycle, L-R1-L-R8 routines |

## Full current map

### Atlas (A)
A1=L4 Close-Loop, A2=Skip Self-Heal, A3=Reconciliation Polling, A3.7=Voice Learning,
A4=Concierge Crew, A5=Chairman Crew, A6=Hunter Crew, A7a/b=Auto-Publish,
A8=CEO Desk Dashboard, A8a=Queue Notion Activity (read-only), A8b=Queue Actionable (gates on E3),
A9-12=Chat/Contracts/Routing/Startup, A9d=Deep Memory Garden,
A13-15=Spend/Notion/TaskAdd, A16=Cross-provider tokens, A17=Kie Spend,
A18=HALO Loop, A19=CRM Dashboard, A20=Native Social Publisher,
A21-22=Overnight Ambient/LLM Blog, A23=Agent Spawning, A24=Hermes Self-Healing,
A25=Event Bus, A26=Live Roadmap DB

### Echo (E)
E0=tasks table + coordination primitives, E1=/propose /ack /reject,
E2=Second proposal kind (DESCOPED), E2.5=Push Gate file-locking,
E3=Multi-agent ingestion, E4=Auto-detection (DEFERRED), E5=Reversible redirection (DEFERRED)

### Compass (C)
C0=Governance scaffolding, C1=AGENTS.md audit, C2=5 enforcement hooks,
C2.5=Routing evaluator, C2.5b=Routing fixtures 100%, C3=Quarterly purge,
C4=LLM manifest, C5=submodule reconciliation, C6=Security scan gate,
C6-audit=Monthly config self-audit, C7=Branch discipline + secret scan

### Studio (S)
S1=Engine + 3-channel batch, S2=Brand Identity, S3=Content Production Pipeline,
S3.4=Scene Motion Upgrade, S3.5=Channel Cloner, S3.6=Content Intelligence,
S3.7=Content Multiplier, S4=Multi-Channel Publish, S5=Performance Analytics,
S6=Monetization Wiring, S7=Channel 3, S8=Channel 4 + Operations

### Harvest (H)
H1=First Signal Works contract, H1a=Score-report methodology,
H1c=website-teardown skill, H1d=CW self-teardown, H1e=CW v3-WOW,
H1f=art direction lift, H1g=enrichment pipeline,
H2=SaaS Audit offer, H3=First CW Signal Session, H4=AI dept SKU,
H5=Client portal, H6=Repeatable lead source, H7=transcript-style-dna test,
H-auto=CW AI automation delivery, H-news=The Weekly Signal newsletter,
H-sever=Notion CRM sever, H-brand=Brand guide audit + rebuild

### Lighthouse (L)

**Lifecycle (L0-L7) — weekly milestones:**
L0=Day 0 (2026-05-12 setup), L1=W1 Reply Velocity (5/13-5/17),
L2=W2 Open the Funnel (5/19-5/24), L3=W3 First Conversion (5/26-5/31),
L4=W4-6 Expand (6/2-6/21), L5=W7 Mid-Cycle Council (6/23-6/28),
L6=W8-11 Scale (6/30-7/26), L7=W12 Close (7/28-8/2)

**Routines (L-R1 through L-R8) — recurring mechanisms:**
L-R1=Daily Fast-Feedback Sprint (M-F 10:00 MDT),
L-R2=First Win Ceremony (once, auto on first reply),
L-R3=Guilt-Free Reset Trigger (daily 10:30 if L-R1 missed),
L-R4=Weekly Priority Triad Lock (Sat 10:00 MDT, 3 lanes max),
L-R5=Conversion Scorecard (Sat 10:30 MDT),
L-R6=Auto-Close Script (T+24h value, T+72h ask),
L-R7=Idea Vault Lock (anytime),
L-R8=List Hygiene Gate + Reply Classifier Fix (before any cold send)

**Rename history (2026-05-16):** Routine milestones previously used bare `M<n>` (M1-M8). Renamed to `L-R<n>` for codename-prefix consistency with other roadmaps. Pre-2026-05-16 handoffs + frozen artifacts under `docs/handoff/2026-05-1[2-4]-*.md` + `docs/strategy/lead-strategy-2026-05-12.html` retain old M-names (historical snapshots). Translation: `M1↔L-R1, M2↔L-R2, M3↔L-R3, M4↔L-R4, M5↔L-R5, M6↔L-R6, M7↔L-R7, M8↔L-R8`.

**Sub-prefix convention (locked 2026-05-16):** `<codename>-R<n>` denotes ROUTINE milestones (vs lifecycle). Future codenames follow: Ghost = G-R<n> / G<n>, etc. Reasoning: at-a-glance routing without colliding with lifecycle milestones in same codename.

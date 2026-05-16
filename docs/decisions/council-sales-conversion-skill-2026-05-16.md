# Council Research: sales-conversion-vet Skill

Date: 2026-05-16
Method: 5-voice council (Hormozi + Brunson + Miller + DelDuca + Boubacar)
Subject: design + spec new skill at `skills/sales-conversion-vet/` for landing-page + funnel auditing

---

## 1. Skill verdict

**Standalone skill at `skills/sales-conversion-vet/`.** Not merged into hormozi-lead-gen. Not folded into sankofa.

Reasoning:
- hormozi-lead-gen is OFFER + LEAD-GEN procedure (Value Equation, Core Four, follow-up cadence). It assumes you already have a converting landing page. It does not audit one. Merging would bloat it.
- sankofa is decision pressure-test, voice-agnostic. Conversion vetting needs domain-specific lenses, not 5 generic voices.
- The skill itself becomes a SKU. Standalone = clean SKU mapping.
- hormozi-lead-gen remains parent for upstream work. sales-conversion-vet is downstream sibling.

## 2. Skill spec

### Frontmatter

```yaml
---
name: sales-conversion-vet
description: Use when auditing a landing page, sales page, checkout flow, product launch, or pricing page for conversion mechanics. Runs a 5-voice council audit (Hormozi offer math, Brunson funnel architecture, Miller StoryBrand narrative, DelDuca operator anti-patterns, Boubacar voice and moat). Outputs scored rubric and prioritized fix list. Triggers on "audit this landing page", "score this funnel", "convert-or-refund", "vet this page", "is this page converting", "sales-conversion-vet", "/scv".
---
```

### Modes

| Mode | Trigger | Output |
|---|---|---|
| AUDIT | "audit this page", URL or file given | Scored rubric + ranked fixes |
| BUILD | "build a sales page for X", greenfield | Skeleton page with 5-voice gates inline |
| OPTIMIZE | "this page isn't converting", live data given | Re-score + lift hypotheses ranked |

### AUDIT mode protocol (7 steps)

1. Read the artifact end-to-end before any voice speaks
2. List the offer + asking price + guarantee in one sentence. If any missing, halt
3. Score by each voice (5 voices x 1-10)
4. Each voice names its top failure + 1 ship-today fix
5. Chairman picks 3 highest-leverage fixes, ranks by ship-effort
6. Output HTML rubric (5-column score table, 3-card fix queue, defer list)
7. Anti-pattern self-check before shipping

### Verification gates

| Pass | Fail |
|---|---|
| Each voice scored 1-10 with rationale | Voice missing or hedged |
| 3 ship-today fixes are concrete edits, not principles | Generic "improve copy" |
| Anti-pattern self-check documented | No anti-pattern section |
| Total score /50 reported | Score without scale |

### Output

HTML report at `agent_outputs/scv/<page-id>-YYYY-MM-DD.html`. Mirrors SW audit format. Mobile-first card stack.

### Integration

- Calls hormozi-lead-gen if Value Equation lever < 5
- Calls frontend-design if visual/layout dominates
- Calls ctq-social if voice score < 5
- Logged to `data/changelog.md`

## 3. Sample audit: humanatwork.ai/start-ai/ (current draft)

| Voice | Score /10 | Top finding |
|---|---:|---|
| Hormozi (offer math) | 8 | Value Equation strong (dream + proof + time + effort). Weakest lever: PROOF. Zero third-party numbers. |
| Brunson (funnel) | 6 | Value-ladder gap too wide: $19 → $149 (8x) → $697 → $3,997. Missing order-bump at T1 checkout. |
| Miller (StoryBrand) | 7 | Hero + Guide + Plan clear. Failure-state stakes are quiet. Page never names the felt cost. |
| DelDuca (operator anti-patterns) | 7 | "Most picked" badge with zero buyers = fake proof. Bonus stack 6x not 10x. "First 100" w/o live counter. |
| Boubacar (voice + moat) | 8 | Voice clean. Moat buried in About section. Move multi-brand operator line above fold. |

**Total: 36/50.** Acceptable to ship. 7-day improvement path:

### 3 ship-TODAY fixes

1. **Move moat above fold.** Add subhead under H1: "Built by an operator running three brands on this stack. Not a course-seller."
2. **Add failure-state paragraph** above buy-box. Miller hero-stakes.
3. **Drop T2 from $149 to $79** + add T1 order-bump ("+$29: 28 paste-ready prompts ships with your guide"). Brunson 30% AOV lift.

### 3 fixes this week (NOT today)

1. Live buyers-counter widget for "first 100" banner. Until built, change to "Early-bird through May 23" (time-bound).
2. Replace "Most picked" T2 badge with "Most value" or remove until real sales data.
3. Pull 1 named third-party anecdote into proof strip.

### Chairman insight (DelDuca-right order-of-operations)

**Remove fake proof TODAY. Add real proof THIS WEEK.** Reverse order damages trust faster than it builds it.

## 4. SKU repackage angle (this skill as a sellable product)

| SKU | Price | Format | Build time |
|---|---|---|---|
| T1: Convert-Or-Refund Rubric PDF | $29 | 12-page PDF, 5-voice scorecard, 1 worked-example | 4 hours |
| T2: Convert-Or-Refund Workbook | $79 | Rubric + 30 worked-example pages + fill-in template | 2 days |
| T3: Hand-in-Hand Audit | $499 | Boubacar runs rubric live on buyer's page (60 min) + 1-week followup | per booking |

Clean ladder: $29 → $79 (2.7x) → $499 (6.3x). Moat: 30 worked-example landing pages with same rubric applied. Nobody else ships this.

## 5. Anti-pattern self-check (skill MUST refuse)

- Promise specific conversion numbers. Regulated speech. Instead: "operators applying this lift saw measurable improvement; your number depends on traffic + offer fit."
- Override Boubacar voice with templated SaaS copy. Run through ctq-social first.
- Recommend dark patterns. No fake countdown timers. No fake "X people viewing now". No fake "Most picked" badges.
- Score subjectively. Every 1-10 must have 1-sentence rationale another auditor could replicate.

## 6. Voice disagreement surfaced

**Hormozi** says proof is weakest lever (low priority because of it). **DelDuca** says fake-proof patterns are MORE damaging than missing proof. **Chairman**: DelDuca-right on order-of-operations. Remove fake proof TODAY. Add real proof THIS WEEK.

## See also

- skills/hormozi-lead-gen/SKILL.md — upstream offer construction
- skills/sankofa/SKILL.md — decision pressure-test (different purpose)
- skills/ctq-social/SKILL.md — voice gate this skill calls
- skills/frontend-design/SKILL.md — visual layer this skill flags
- C:/Users/HUAWEI/.claude/projects/D--Ai-Sandbox-agentsHQ/memory/feedback_digital_asset_voice_boubacar_fingerprint.md
- C:/Users/HUAWEI/.claude/projects/D--Ai-Sandbox-agentsHQ/memory/feedback_purchased_packs_never_resell_verbatim.md

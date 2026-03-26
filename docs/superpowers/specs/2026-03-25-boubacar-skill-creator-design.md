# boubacar-skill-creator — Design Spec
**Date:** 2026-03-25
**Status:** Approved

---

## Problem

The official `skill-creator` plugin is a powerful but generic tool. It doesn't know who Boubacar is, how he thinks, what his voice sounds like, or what patterns work for him. Every session starts from zero. It also doesn't distinguish between a consulting-domain skill (where Boubacar's leGriot voice matters) and a technical utility skill (where clean, generic instructions are correct).

---

## Goal

Build `boubacar-skill-creator`: a personal, intelligent skill creator that:
1. Knows Boubacar's profile, working style, and voice from Day 1
2. Gets smarter with every skill created — storing atomic learnings as confidence-scored instincts
3. Injects Boubacar's voice only where it genuinely differentiates the skill
4. Checks in at natural moments (not just start/end) to stay aligned
5. Uses existing infrastructure (skill-creator evals, writing-skills TDD) for mechanics — adds the intelligence layer on top
6. Can be tested via simulation before going live

---

## Architecture

Three layers:

### Layer 1 — Identity Layer (always loaded)
- Boubacar's profile from `docs/memory/user_boubacar.md`
- Accumulated instincts from `skills/boubacar-skill-creator/patterns/instincts.json`
- Voice taxonomy from `skills/boubacar-skill-creator/patterns/voice-domains.json`
- Skill taxonomy from `skills/boubacar-skill-creator/patterns/skill-taxonomy.json`

### Layer 2 — Orchestration Layer (the skill itself — `SKILL.md`)
The skill's own workflow, check-in system, and voice injection logic.

Workflow:
```
pre-session brief → understand intent → classify domain →
draft skill → check-in (if triggered) → test with skill-creator →
reflect → store learnings → package
```

### Layer 3 — Mechanics Layer (borrowed, not duplicated)
- `skill-creator`: evals, benchmarking, blind comparison, description optimizer, eval viewer
- `writing-skills`: TDD RED-GREEN-REFACTOR discipline

---

## Data Structures

### instincts.json
Atomic learned behaviors with confidence scoring:
```json
[
  {
    "id": "prefers-minimal-first-draft",
    "domain": "all",
    "observation": "Boubacar prefers a lean first draft before adding complexity",
    "confidence": 0.87,
    "evidence_count": 6,
    "last_updated": "2026-03-25"
  }
]
```

Confidence scores:
- 0.60–0.74: Tentative (seen once or twice)
- 0.75–0.89: Established (recurring pattern)
- 0.90–1.00: Certain (consistent across many sessions)

Only instincts ≥ 0.75 are applied automatically. Lower-confidence instincts surface as suggestions.

### voice-domains.json
Controls where Boubacar's voice gets injected:
```json
{
  "inject_voice": ["leGriot", "consulting", "social-media", "client-facing", "personal-agents"],
  "stay_technical": ["infrastructure", "scripts", "api-wrappers", "git", "data-processing"]
}
```

### skill-taxonomy.json
Growing map of Boubacar's skill domains:
```json
{
  "consulting": [],
  "social-media": [],
  "orchestration": [],
  "infrastructure": [],
  "personal-agents": [],
  "finance": []
}
```

Updated after every new skill is created and packaged.

---

## Check-in System

Check-ins are short, direct, and non-blocking. They fire at these triggers:

| Trigger | Check-in message |
|---------|-----------------|
| First draft written | "Does this sound like you, or generic AI?" |
| Skill domain = consulting/social/personal | "Should your leGriot voice be in this, or keep it technical?" |
| New pattern contradicts stored instinct | "You usually prefer X, but this skill does Y — intentional?" |
| 3+ skills without reflection pass | "Quick check-in: here's what I've learned about how you work lately. Still accurate?" |
| Before packaging | "Before I package: anything you'd want future-you to know when using this skill?" |

All check-in responses optionally update instincts (user must confirm before any learning is stored).

---

## Voice Injection Logic

When domain is in `inject_voice` list:
1. Load leGriot voice rules from `docs/memory/user_boubacar.md` (voice section)
2. Apply to: skill description tone, example phrasings, output format guidance
3. Keep technical steps clean — voice goes in framing, not mechanics
4. Example: a consulting-domain skill's description might read "Use when diagnosing a client bottleneck and you need a structured output fast" rather than "Use when analyzing organizational problems"

When domain is in `stay_technical` list:
- No voice injection. Clean, third-person, standard skill format.

---

## Learning Loop

After each skill creation session:

1. **Reflection pass** (spawned as subagent): reads the session transcript, extracts candidate instincts
2. **User confirmation**: surfaces 1-3 candidate learnings — "I noticed X. Should I remember this?"
3. **Storage**: confirmed learnings added to `instincts.json` (confidence 0.60 to start) + mirrored to `docs/memory/skill_creator_learnings.md`
4. **Confidence growth**: same instinct observed again → confidence increases by ~0.10 per confirmation

Over time, instincts graduate from suggestions → automatic behaviors.

---

## Simulation / Testing Plan

Before going live, validate via the `skill-creator` eval infrastructure:

### Eval scenarios (3 types):
1. **Technical skill** — user asks to build an API wrapper skill. Verify: no voice injection, clean output, proper TDD cycle followed.
2. **Consulting skill** — user asks to build a client-onboarding skill. Verify: voice injected, leGriot tone present, check-in fired at domain classification.
3. **Learning loop** — run 2 skill creation sessions. Verify: instincts extracted after session 1, applied in session 2.

### Grading assertions:
- Voice present in consulting-domain skills
- Voice absent in technical-domain skills
- Check-in fired at correct trigger points
- Instincts stored with correct confidence scores
- Mechanics (evals, benchmarking) delegated to skill-creator correctly

### Baseline comparison:
Run same prompts through plain `skill-creator`. Compare outputs. Grade via blind comparator.

---

## File Structure

```
skills/
  boubacar-skill-creator/
    SKILL.md                    ← main orchestration skill
    patterns/
      instincts.json            ← learned behaviors (confidence-scored)
      voice-domains.json        ← voice injection rules
      skill-taxonomy.json       ← Boubacar's growing skill map
    references/
      voice-guide.md            ← extracted from user_boubacar.md
      check-in-triggers.md      ← full check-in trigger logic
    agents/
      reflector.md              ← post-session learning extraction subagent

docs/memory/
  skill_creator_learnings.md    ← mirrored fast-load instincts index
```

Installed to: `~/.claude/skills/boubacar-skill-creator/`

---

## Success Criteria

- [ ] Creates better skills faster than plain skill-creator (measurable via evals)
- [ ] Voice correctly injected in consulting domain, absent in technical domain
- [ ] Check-ins fire at all 5 trigger points
- [ ] After 3 sessions: at least 3 instincts at confidence ≥ 0.75
- [ ] Simulations pass before live deployment
- [ ] User says "this feels like me"

---

## Out of Scope (v1)

- Auto-generating skills from observed workflow patterns (v2)
- SQLite-backed learning queue (v2 — start with JSON files)
- Sharing skills publicly to anthropics/skills repo

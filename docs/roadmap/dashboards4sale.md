# Dashboards4Sale: Multilingual Budget Dashboards Product

**Codename:** dashboards4sale
**Status:** active (stub; populate in extraction session)
**Lifespan:** open-ended
**Started:** 2026-04-25 (referenced) / 2026-05-02 (roadmap stub)
**Owner:** Boubacar Barry
**One-line:** Arabic / French / English budget dashboards as a standalone SaaS product, satellite to agentsHQ

> **Note:** Stub only. Lock Done Definition + Status Snapshot in the first extraction session when `bokar83/dashboards4sale` becomes its own repo.

---

## Why This Is Separate

Dashboards4Sale is a product Boubacar owns and sells. It has its own URL, its own customer (end users buying dashboards), and its own revenue stream (one-time or subscription product sales). Per the **Platform-with-Satellites rule** locked 2026-04-27, that means it gets its own GitHub repo. The agentsHQ platform powers it (research, content, support automation), but the product code lives in the satellite repo.

It is not Studio (Studio is a faceless content agency / channels). It is not Catalyst Works (CW is consulting). It is its own venture.

---

## Done Definition (placeholder; lock in extraction session)

Possible framings to choose from:
- N paid customers per month
- $X MRR floor
- Multilingual coverage gates (Arabic + French + English shipped, with localized payment + support)
- One signed B2B distribution partner (an accounting firm, a school district, etc.)

---

## Status Snapshot (as of 2026-05-02)

- **Repo location today:** still a submodule inside agentsHQ at `Dashboards4Sale/`: pending extraction
- **Live URL:** TBD
- **Customers:** $0 revenue
- **Build state:** dashboards exist as static templates in the submodule
- **Languages:** templates exist in EN; AR + FR localization pending
- **Distribution:** none yet (no Stripe wiring, no checkout, no marketing site)

---

## Milestones

### M0: Extract to its own repo `bokar83/dashboards4sale`

**Status:** Queued. Trigger: dedicated 30-60 min extraction session.

**Steps:**
1. Create `bokar83/dashboards4sale` on GitHub
2. Push current `Dashboards4Sale/` submodule contents to the new repo
3. `git submodule deinit Dashboards4Sale` in agentsHQ
4. Edit `.gitmodules` to remove the submodule entry
5. `git rm --cached Dashboards4Sale`
6. Add `Dashboards4Sale/` to agentsHQ `.gitignore` (in case the directory persists locally as a working clone)
7. Update `docs/reference/repo-structure.md` and root `AGENTS.md` to mark D4S as extracted
8. Update Ventures Registry in `docs/roadmap/README.md` with the live satellite URL
9. Confirm three-way nsync at the new state

### M1: Multilingual coverage (AR + FR + EN)

**Status:** Pending M0. Trigger: extraction complete, repo working.

### M2: Distribution partner #1

**Status:** Pending. Trigger: M1 done + landing page live + payment wired.

### M3: First $1k month

**Status:** Pending. Revenue floor target.

---

## Cross-References

- Platform-with-Satellites rule: `AGENTS.md` (root), `docs/reference/repo-structure.md`
- Ventures Registry: `docs/roadmap/README.md`
- Notion Tasks: T-260... "Create Dashboards4Sale standalone repository and remove submodule"
- Related skills: `vercel-launch`, `hostinger-deploy`, `clone-builder` (clone-builder pattern is relevant for additional dashboard variants)

---

## Session Log

### 2026-05-02: Roadmap stub created

Stub created during the agentsHQ Move Day session. Ventures mental model added to `docs/roadmap/README.md`; D4S formally registered as a satellite venture pending repo extraction. Code remains inside agentsHQ as a submodule until the extraction session.

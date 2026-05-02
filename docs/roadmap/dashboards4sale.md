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

## Status Snapshot (as of 2026-05-02 evening, post-extraction)

- **Repo location:** EXTRACTED to satellite repo `bokar83/dashboards4sale` (`https://github.com/bokar83/dashboards4sale`) on 2026-05-02. Original tracked content preserved in agentsHQ at `zzzArchive/_pre-cleanup-20260502/Dashboards4Sale-original/`.
- **Live URL:** TBD
- **Customers:** $0 revenue
- **Build state:** dashboards exist as static templates in the satellite
- **Languages:** templates exist in EN, FR, AR (skeleton only); production-ready localization pending
- **Distribution:** none yet (no Stripe wiring, no checkout, no marketing site)

---

## Milestones

### M0: Extract to its own repo `bokar83/dashboards4sale` ✅ SHIPPED 2026-05-02

**Result:** Live at `https://github.com/bokar83/dashboards4sale`. Original tracked content preserved in `zzzArchive/_pre-cleanup-20260502/Dashboards4Sale-original/` per the no-delete rule.

**Verification (Karpathy success criterion):** cloned new satellite to `d:/tmp/d4s-verify`, file-count diff matches expected (67 in satellite, 71 in archive; 4-file delta = pycache + xlsx outputs intentionally gitignored).

**What shipped:**

1. Created `bokar83/dashboards4sale` on GitHub (private)
2. Copied `Dashboards4Sale/` content to clean temp dir, cleaned pycache, added .gitignore (pycache + xlsx + node_modules + .env), git init, single init commit, pushed
3. D4S was NOT a submodule (regular tracked directory); used standard `git mv` to archive instead of `git submodule deinit`
4. `git mv Dashboards4Sale zzzArchive/_pre-cleanup-20260502/Dashboards4Sale-original/`
5. Verification clone + file-count diff: PASS
6. This roadmap M0 marked SHIPPED
7. Ventures Registry in `docs/roadmap/README.md` updated with live satellite URL (in same commit)

### M1: Multilingual coverage (AR + FR + EN)

**Status:** Queued. Unblocked by M0.

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

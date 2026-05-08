# Plan: Email Signature Polish

**Date:** 2026-05-08
**Branch:** `feat/email-signature-polish` (off `main`)
**Author:** Claude → Codex
**Status:** Awaiting /karpathy.

## Goal

Two corrections across all email templates:

1. **Rule 1 — First-name only.** Replace "Boubacar Barry" with "Boubacar" in body prose. Per `feedback_first_name_only.md`.
2. **Rule 2 — Studio domain fix.** Studio templates currently sign `catalystworks.consulting`. Studio = SW + Studio merged web-presence pipeline (per `feedback_sw_studio_merged.md`), product surface = `geolisted.co`. Change all 4 Studio footers to `geolisted.co`.

## Inventory (verified 2026-05-08)

### Rule 1 violations

| File | Line | Current | Replace with |
|---|---|---|---|
| `templates/email/studio_t1.py` | 34 | `I'm Boubacar Barry. I build fast, modern websites...` | `I'm Boubacar. I build fast, modern websites...` |

**Archive policy (per Boubacar 2026-05-08):** `templates/email/archive/cold_outreach_v1.py` line 14 has the same violation. **Do NOT fix.** Archive = historical reference. Leave as-is.

### Rule 2 violations

| File | Line | Current footer | New footer |
|---|---|---|---|
| `templates/email/studio_t1.py` | 43 | `catalystworks.consulting` | `geolisted.co` |
| `templates/email/studio_t2.py` | 28 | `catalystworks.consulting` | `geolisted.co` |
| `templates/email/studio_t3.py` | 31 | `catalystworks.consulting` | `geolisted.co` |
| `templates/email/studio_t4.py` | 24 | `catalystworks.consulting` | `geolisted.co` |

### Already correct (do not touch)

- `cold_outreach.py` (CW T1) → `catalystworks.consulting` ✓
- `cw_t2.py`, `cw_t3.py`, `cw_t4.py`, `cw_t5.py` → `catalystworks.consulting` ✓
- `sw_t1.py` through `sw_t5.py` → `geolisted.co` ✓

## Decision lock

**CW templates keep `catalystworks.consulting`.** CW = consulting offer, parent brand. Only Studio changes to geolisted.co.

## Patches

### Patch 1 — `studio_t1.py:34`

```python
# OLD
I'm Boubacar Barry. I build fast, modern websites and AI-ready web presences for business owners who are ready to stop being invisible online.
# NEW
I'm Boubacar. I build fast, modern websites and AI-ready web presences for business owners who are ready to stop being invisible online.
```

### Patch 2 — Studio T1-T4 footers

Each file has a sign-off block of shape:

```
Boubacar
catalystworks.consulting
```

Replace `catalystworks.consulting` → `geolisted.co` in all 4 files. Surgical single-line edit per file.

## Test plan

### Pre-edit grep (baseline)

```bash
grep -rn "Boubacar Barry" d:/Ai_Sandbox/agentsHQ/templates/email/ --include="*.py" | grep -v archive
# Expected: 1 hit (studio_t1.py:34)

grep -rn "catalystworks.consulting" d:/Ai_Sandbox/agentsHQ/templates/email/ --include="*.py" | grep -v archive | grep studio
# Expected: 4 hits (studio_t1-4)
```

### Post-edit grep (acceptance)

```bash
grep -rn "Boubacar Barry" d:/Ai_Sandbox/agentsHQ/templates/email/ --include="*.py" | grep -v archive
# Expected: 0 hits

grep -rn "catalystworks.consulting" d:/Ai_Sandbox/agentsHQ/templates/email/studio_*.py
# Expected: 0 hits

grep -rn "geolisted.co" d:/Ai_Sandbox/agentsHQ/templates/email/studio_*.py
# Expected: 4 hits (one per file)

grep -rn "—" d:/Ai_Sandbox/agentsHQ/templates/email/ --include="*.py" | grep -v archive
# Expected: 0 hits (em-dash zero-tolerance)
```

### Render check

> **Note:** This script is verification-only. Run via `python -c "<paste>"` or scratch file. **Do NOT commit as a test file.** No new tests/ folder, no pytest fixture. One-shot validation, then discard.

```python
# Render every active template against sample lead
from importlib import import_module

SAMPLE_LEAD = {
    "first_name": "Sarah",
    "first_name_confidence": "high",
    "name": "Sarah Mitchell",
    "email": "sarah@acmeroofing.com",
    "niche": "roofer",
    "industry": "roofing",
    "company": "Acme Roofing",
    "city": "Salt Lake City",
}

TEMPLATES = [
    "templates.email.cold_outreach",
    "templates.email.cw_t2", "templates.email.cw_t3", "templates.email.cw_t4", "templates.email.cw_t5",
    "templates.email.sw_t1", "templates.email.sw_t2", "templates.email.sw_t3", "templates.email.sw_t4", "templates.email.sw_t5",
    "templates.email.studio_t1", "templates.email.studio_t2", "templates.email.studio_t3", "templates.email.studio_t4",
]

for path in TEMPLATES:
    mod = import_module(path)
    body = mod.build_body(SAMPLE_LEAD) if hasattr(mod, "build_body") else mod.BODY.format(**SAMPLE_LEAD)
    assert "Boubacar Barry" not in body, f"{path} still has Boubacar Barry"
    if path.startswith("templates.email.studio"):
        assert "geolisted.co" in body, f"{path} missing geolisted.co"
        assert "catalystworks.consulting" not in body, f"{path} still has catalystworks.consulting"
    if path.startswith("templates.email.cw") or path == "templates.email.cold_outreach":
        assert "catalystworks.consulting" in body, f"{path} missing catalystworks.consulting"
    if path.startswith("templates.email.sw"):
        assert "geolisted.co" in body, f"{path} missing geolisted.co"
    assert "—" not in body, f"{path} contains em-dash"
print("All 13 active templates pass.")
```

### drive_publish audit

```bash
python -m orchestrator.drive_publish audit
# Expected: pass (no template-related changes affect drive_publish)
```

## Acceptance checklist

- [ ] Pre-edit grep matches baseline counts.
- [ ] All 5 patches applied (1 prose fix + 4 footer fixes).
- [ ] Post-edit grep: 0 "Boubacar Barry", 0 catalystworks.consulting in studio_*.py, 4 geolisted.co in studio_*.py.
- [ ] Render-check script passes for all 13 active templates.
- [ ] Em-dash count = 0.
- [ ] drive_publish audit passes.
- [ ] Final commit message contains `[READY]`.

## Rollback

`git revert <commit>`. Surgical single-line edits, low risk.

## Codex handoff

Branch: `feat/email-signature-polish`. 5 single-line edits across 4 files. After /karpathy passes, Codex implements + runs render-check + ships [READY].

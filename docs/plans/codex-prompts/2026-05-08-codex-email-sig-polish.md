# Codex prompt — Email Signature Polish

You are implementing a surgical 5-line fix across 4 email template files in the agentsHQ repo (`d:\Ai_Sandbox\agentsHQ`).

## Goal

Two corrections to outreach email templates:

1. **Rule 1 — First-name only.** Replace "Boubacar Barry" with "Boubacar" in body prose. Per memory rule `feedback_first_name_only.md`.
2. **Rule 2 — Studio domain.** Studio templates currently sign `catalystworks.consulting`. Studio = SW + Studio merged web-presence pipeline (per `feedback_sw_studio_merged.md`), product = `geolisted.co`. Change all 4 Studio footers to `geolisted.co`.

## Context

- Plan: `docs/plans/2026-05-08-email-signature-polish.md`
- Karpathy: PASS / SHIP (with note: render-check is verification-only, NOT committed)
- Reference memories:
  - `feedback_first_name_only.md`
  - `feedback_sw_studio_merged.md`
  - `reference_signal_works_site.md`

## Branch

`feat/email-signature-polish` off `main`.

## Edits (5 single-line changes across 4 files)

### Rule 1

#### `templates/email/studio_t1.py` line 34

```diff
-I'm Boubacar Barry. I build fast, modern websites and AI-ready web presences for business owners who are ready to stop being invisible online.
+I'm Boubacar. I build fast, modern websites and AI-ready web presences for business owners who are ready to stop being invisible online.
```

**Do NOT touch** `templates/email/archive/cold_outreach_v1.py`. Boubacar's call: archive = historical reference, leave as-is even if it has the same violation.

### Rule 2 — Studio footers (4 files)

Each file has a sign-off block of shape:

```
Boubacar
catalystworks.consulting
```

Replace `catalystworks.consulting` → `geolisted.co` in:

- `templates/email/studio_t1.py:43`
- `templates/email/studio_t2.py:28`
- `templates/email/studio_t3.py:31`
- `templates/email/studio_t4.py:24`

**Do NOT touch** CW templates (`cold_outreach.py`, `cw_t2.py`, `cw_t3.py`, `cw_t4.py`, `cw_t5.py`). They correctly sign `catalystworks.consulting`.

**Do NOT touch** SW templates (`sw_t1.py` through `sw_t5.py`). They correctly sign `geolisted.co`.

## Constraints

- 5 single-line edits total. Do not refactor anything.
- Do not introduce new tests.
- Do not commit the render-check script (it's a one-shot validator).
- Preserve em-dash zero-tolerance (do not introduce any `—` characters).

## Verification (run before final commit)

### 1. Pre-edit grep baseline

```bash
grep -rn "Boubacar Barry" templates/email/ --include="*.py" | grep -v archive
# Expected: 1 hit (studio_t1.py:34)

grep -rn "catalystworks.consulting" templates/email/studio_*.py
# Expected: 4 hits (studio_t1-4)
```

### 2. Post-edit grep acceptance

```bash
grep -rn "Boubacar Barry" templates/email/ --include="*.py" | grep -v archive
# Expected: 0 hits

grep -rn "catalystworks.consulting" templates/email/studio_*.py
# Expected: 0 hits

grep -rn "geolisted.co" templates/email/studio_*.py
# Expected: 4 hits

grep -rn "—" templates/email/ --include="*.py" | grep -v archive
# Expected: 0 hits
```

### 3. Render-check (one-shot, do NOT commit)

Run inline via `python -c` or scratch file:

```python
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
    if hasattr(mod, "build_body"):
        body = mod.build_body(SAMPLE_LEAD)
    else:
        body = mod.BODY.format(**SAMPLE_LEAD) if hasattr(mod, "BODY") else ""
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

### 4. drive_publish audit

```bash
python -m orchestrator.drive_publish audit
# Expected: pass
```

## Coordination protocol (REQUIRED)

```python
from skills.coordination import claim, complete

branch_task = claim('branch:feat/email-signature-polish', '<your-agent-id>', ttl_seconds=3600)

for fpath in [
    'templates/email/studio_t1.py',
    'templates/email/studio_t2.py',
    'templates/email/studio_t3.py',
    'templates/email/studio_t4.py',
]:
    ftask = claim(f'file:{fpath}', '<your-agent-id>', ttl_seconds=900)
    # edit, commit
    complete(ftask['id'])

complete(branch_task['id'])
```

## Pre-commit hooks

Run pre-commit. Must pass clean. Do not skip with `--no-verify`.

## Final commit + push

Final commit message MUST contain `[READY]`:

```
git commit -m "fix(email-templates): first-name only + Studio footers to geolisted.co [READY]"
git push origin feat/email-signature-polish
```

## Output

Reply with: branch pushed + final commit hash + the diffs for all 4 files + render-check output (`All 13 active templates pass.`).

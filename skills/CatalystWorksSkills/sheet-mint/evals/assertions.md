# sheet-mint Eval Assertions

## What a PASSING with-skill run looks like

### Phase 2 — BUILD_PROMPT.md
- [ ] BUILD_PROMPT.md was saved to the testingSandbox output path
- [ ] Contains tab structure table with sheetId numbers
- [ ] Contains color palette with hex codes
- [ ] Contains column definitions for every tab
- [ ] Contains at least one actual formula (not just a description)
- [ ] Contains sample data specification (25+ rows)
- [ ] Contains chart specs
- [ ] Contains conditional formatting rules

### Phase 3 — Spreadsheet Created
- [ ] gws sheets spreadsheets create was called
- [ ] A spreadsheetId was captured from the response
- [ ] Values were written to at least one tab
- [ ] A batchUpdate formatting call was made
- [ ] Shareable link (docs.google.com/spreadsheets/d/ID) was output in result.md

### result.md
- [ ] Exists in the outputs folder
- [ ] Contains spreadsheet ID
- [ ] Contains shareable link
- [ ] Reports all 3 phases as completed

---

## What a PASSING baseline (no-skill) run looks like

A baseline run passes if it at least:
- Attempts to create the spreadsheet via gws CLI
- Outputs some kind of planning doc or explanation

A baseline run that ONLY talks about how to build it (no actual gws calls) = FAIL for Phase 3.

---

## Scoring

| Criterion | Points |
|---|---|
| BUILD_PROMPT.md saved | 10 |
| BUILD_PROMPT.md has formulas | 10 |
| BUILD_PROMPT.md has sample data | 10 |
| Spreadsheet created (gws call made) | 20 |
| Values written to tabs | 20 |
| Formatting applied | 10 |
| Shareable link output | 10 |
| result.md present | 10 |
| **Total** | **100** |

---

## Expected Differentials

| Metric | With Skill | Baseline |
|---|---|---|
| BUILD_PROMPT.md present | Yes | No |
| Spreadsheet created | Yes | Maybe |
| All 3 phases completed | Yes | No |
| Score | 80–100 | 20–40 |

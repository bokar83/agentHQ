# Markdown Style Guide — Catalyst Works Consulting

**Version:** 2.0
**Last updated:** 2026-03-29
**Palette:** Coastal Clarity
**For:** Boubacar Barry, Founder — Catalyst Works Consulting

---

## PART 1 — FRONTMATTER

Every agent-generated or formal markdown document begins with YAML frontmatter. Internal scratch notes and quick-capture files are exempt.

```yaml
---
title: Document Title
date: YYYY-MM-DD
type: report | brief | proposal | analysis | reference
status: draft | review | final
owner: Boubacar Barry
project: Project Name
---
```

Rules for frontmatter:

- `title`: matches the H1 exactly
- `date`: ISO 8601 format — `2026-03-29`, not "March 29" or "03/29/26"
- `type`: one of the five listed values only
- `status`: update on every meaningful revision — never leave `draft` on a delivered document
- `owner`: always "Boubacar Barry" unless explicitly delegated
- `project`: the engagement or initiative name, not a code

---

## PART 2 — HEADING STRUCTURE

### Rules

- **H1 (`#`):** Document title only. One per document. No period at end. Title Case.
- **H2 (`##`):** Major sections. Title Case. No period. Two blank lines before every H2.
- **H3 (`###`):** Subsections within an H2. Sentence case (first word capitalised only, unless proper noun). No period. One blank line before.
- **H4 (`####`):** Labels, field identifiers, metadata markers. ALL CAPS with colon. e.g. `STATUS:` `OWNER:` `DECISION:`. One blank line before.
- **Never skip levels.** No jumping from H1 to H3. No jumping from H2 to H4.
- **Never use H5 or H6.** If you need a fifth level, the document structure is wrong.

### Heading Examples

```markdown
# Organizational Decision Architecture Review

## Executive Summary

### Current State Assessment

#### STATUS: DRAFT
```

### Blank Line Spacing (exact rules)

```text
[Two blank lines]
## Major Section Heading
[One blank line]
Body text begins here.
[One blank line]
### Subsection
[One blank line]
Body text.
[One blank line]
#### LABEL:
[One blank line]
Content under label.
```

---

## PART 3 — BODY TEXT RULES

- One blank line between paragraphs
- No trailing spaces on any line
- 80-character soft wrap recommended (not enforced, but preferred for diff readability)
- Em dash (—) not double hyphen (--). Use `—` directly or the HTML entity `&mdash;`
- Ellipsis (…) not three periods (...). Use `…` directly or `&hellip;`
- Apostrophes: curly (`'`) preferred over straight (`'`) in final documents
- Numbers: spell out one through nine; use numerals for 10 and above
- Percentages: use the % symbol with a numeral — `47%` not "47 percent"
- Dates: ISO format in frontmatter (`2026-03-29`); prose format in body (`29 March 2026` or `March 29, 2026`)

---

## PART 4 — EMPHASIS

| Usage | Syntax | When to use |
| --- | --- | --- |
| Bold | `**text**` | Key terms on first use, proper nouns on first use, critical warnings, the most important phrase per paragraph |
| Italic | `*text*` | Titles of works, technical terms being defined, very light emphasis where bold would be too heavy |
| Code | `` `text` `` | Filenames, paths, commands, variables, hex codes, URLs inline in body text |
| Blockquote | `> text` | Pull quotes, client statements, important callouts — not for indentation |

**Rules:**

- Never use ALL CAPS for emphasis — use bold
- Never bold an entire sentence — bold the load-bearing phrase within it
- Never italicise for decoration — only for the semantic purposes listed above
- Never nest bold inside italic or vice versa unless the dual meaning is intentional

---

## PART 5 — LISTS

### Bullet Lists

```markdown
- First item (no period if a fragment)
- Second item
- Third item with a full sentence. Use a period.
```

- Marker: `-` (hyphen), not `*` or `+`
- Max 2 levels of nesting. No third level.
- Consistent ending punctuation within a list — all periods or none
- No bullets for lists of 2 items — write them as prose with "and"
- No bullets for sequential steps — use numbered lists

### Numbered Lists

```markdown
1. First step, written as a complete action.
2. Second step.
3. Third step.
```

- Use for sequential steps, ranked items, or ordered processes
- Always use `1.` numbering — let the renderer handle the count
- Each item ends with a period (numbered lists are full sentences)

### Sub-lists (max 2 levels)

```markdown
- Parent item
  - Child item
  - Child item
- Parent item
```

- Indent with 2 spaces (not 4, not tab)
- Never nest numbered inside numbered (use H3 instead)
- Never use sub-lists to replace clear writing — if a sub-list appears, ask whether a new section would be clearer

---

## PART 6 — CALLOUTS (BLOCKQUOTE SYNTAX)

Standard callout format — used for notes, tips, warnings, and examples:

```markdown
> **NOTE:** For general information the reader should not miss.

> **TIP:** A recommendation or shortcut worth knowing.

> **WARNING:** A critical issue, risk, or blocker. Use sparingly — max once per section.

> **EXAMPLE:** An illustration of a concept just explained.

> **DECISION:** A choice that was made and needs to be recorded as settled.
```

Rules:

- The label (`NOTE:`, `TIP:`, etc.) is always bold and uppercase
- One blank line before and after every callout block
- Never use blockquotes as a general indentation tool
- Never stack two callouts consecutively without body text between them

---

## PART 7 — TABLES

### Format

```markdown
| Column A | Column B | Column C |
| --- | --- | --- |
| Value | Value | Value |
| Value | Value | Value |
```

### Alignment

- Left-align: all text columns
- Right-align: all number columns (add `:` to right side of separator: `| ---: |`)
- Center-align: status fields, icons, boolean columns (colons on both sides: `| :---: |`)

### Rules

- Always include a header row
- Keep cells concise — if a cell needs more than 2 sentences, use a section with a heading instead
- Never use a table for 2-column key/value pairs with fewer than 4 rows — use a definition list or plain prose
- Never merge cells (not supported in standard Markdown; use HTML only if absolutely required)

---

## PART 8 — CODE BLOCKS

Always specify the language. No bare triple-backtick blocks.

```markdown
    ```python
    # Comment every non-obvious line
    result = calculate_score(data)
    ```
```

```markdown
    ```bash
    # Install dependencies
    pip install -r requirements.txt
    ```
```

```markdown
    ```json
    {
      "key": "value"
    }
    ```
```

### Language tags to use

| Content type | Tag |
| --- | --- |
| Python | `python` |
| Shell / terminal | `bash` |
| JSON data | `json` |
| YAML config | `yaml` |
| CSS styles | `css` |
| HTML markup | `html` |
| JavaScript | `javascript` |
| Plain text / diagrams / specs | `text` |
| SQL | `sql` |

### Code block rules

- Max 40 lines per block. Split longer code at logical breaks.
- Comment every non-obvious line — not every line, but every line where the intent isn't immediately clear
- Do not use code blocks for inline values — use backtick inline code instead
- Always use `text` for spec blocks, ASCII diagrams, and file-naming patterns

---

## PART 9 — LINKS AND REFERENCES

```markdown
[Link text](https://example.com)
[Link text](https://example.com "Optional title")
[Reference-style link][ref-id]

[ref-id]: https://example.com
```

Rules:

- Link text must describe the destination — never use "click here" or "this link"
- URLs in body text: always wrap in backticks — `` `https://example.com` ``
- External links in formal deliverables: use reference-style links at the bottom of the section
- Never bare-paste a URL in running prose — always wrap in `[]()` or backticks

---

## PART 10 — DOCUMENT STRUCTURE TEMPLATES

### Report / Analysis

```markdown
---
title: [Report Title]
date: YYYY-MM-DD
type: report
status: draft
owner: Boubacar Barry
project: [Project Name]
---

# [Report Title]

## Executive Summary

[2–4 sentences. The diagnosis first, then what the document covers.]

## Context

[Background. What question is this document answering, and why now.]

## Findings

### [Finding 1 — specific label]

### [Finding 2]

## Recommendations

### [Recommendation 1]

### [Recommendation 2]

## Next Steps

| Action | Owner | Due date |
| --- | --- | --- |
| | | |
```

### Reference Document

```markdown
---
title: [Reference Title]
date: YYYY-MM-DD
type: reference
status: final
owner: Boubacar Barry
project: [Project Name]
---

# [Reference Title]

## Overview

[One paragraph. What this reference covers and who uses it.]

## [Section 1]

## [Section 2]

## Quick Reference

[Table or list of the most-used values/rules from this document.]
```

### Brief / Situation Summary

```markdown
---
title: [Brief Title]
date: YYYY-MM-DD
type: brief
status: final
owner: Boubacar Barry
project: [Project Name]
---

# [Brief Title]

#### SITUATION:

[1–3 sentences. What is happening and why it matters now.]

#### DECISION REQUIRED:

[The specific choice that needs to be made.]

#### OPTIONS:

1. [Option A] — [one-sentence consequence]
2. [Option B] — [one-sentence consequence]

#### RECOMMENDATION:

[The recommended option and the primary reason.]

#### NEXT ACTION:

[Who does what, by when.]
```

---

## PART 11 — ANTI-PATTERNS

| Anti-pattern | Why it fails | Correct approach |
| --- | --- | --- |
| Using `#` multiple times per document | Breaks document hierarchy | One H1 per document — always |
| Skipping from `##` to `####` | Reader loses orientation | Always use sequential levels |
| Using `---` as a section divider mid-document | Creates visual noise; renders as H2 | Use `##` heading instead |
| Three-dot ellipsis `...` | Typographically incorrect | Use `…` |
| Double hyphen `--` for em dash | Incorrect | Use `—` |
| Nested sub-lists 3 levels deep | Signals unclear thinking | Restructure as sections |
| ALL CAPS for emphasis | Aggressive, inaccessible | Use `**bold**` |
| Blockquote used for visual indentation | Semantic abuse | Use prose or lists |
| Bare URL pasted in body | Ugly, breaks on some renderers | Wrap in `[text](url)` |
| Missing language tag on code block | Fails syntax highlighting | Always specify language |

# Cold Outreach -- Catalyst Works Consulting

**Name:** Cold Outreach
**Description:** Single cold email template for Catalyst Works Consulting. Universal -- no industry branching. Reply-first model -- no Calendly in the initial email.

---

## IMPORTANT -- Single Source of Truth

The template lives in one place only:

```
templates/email/cold_outreach.py
```

To update the template, edit ONLY that file. All tools import from it automatically.
Do NOT copy the template text into this file, crews.py, or anywhere else.

---

## Strategy Notes

- **Reply-first model:** Optimize for the micro-commitment (a reply), not the booking. Calendly goes in the follow-up, never the cold email.
- **One template:** Universal copy that works for any prospect regardless of industry or size.
- **Plain text only:** No HTML, no signature blocks.

---

## Subject Line

See `templates/email/cold_outreach.py` -- variable `SUBJECT`

---

## Follow-Up Sequence

Calendly goes here, not in the cold email.

Follow-up 1 (3 days after no reply): short bump.
Follow-up 2 (5 days after that): value add or breakup line.

---

## Version History

- **v1.0 (2026-04-06):** Initial version.
- **v2.0 (2026-04-07):** Consolidated to single universal template.
- **v3.0 (2026-04-09):** New copy approved. Plain text only, no HTML signature.
- **v4.0 (2026-04-09):** Template moved to templates/email/cold_outreach.py as single source of truth.

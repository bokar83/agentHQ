# Inbound Lead Routine: Field Map Addendum

Pipeline DB ID: 249bcf1a-3029-80f5-8d84-cbbf4fa4dbdb
Title: Consulting Pipeline
Read on: 2026-04-20

## Actual properties (live-read via Notion API)

| Logical concept | Property name | Type |
|---|---|---|
| name          | Lead/Company                    | title |
| email         | Email                           | email |
| company       | Contact Name                    | rich_text (semantic mismatch, see notes) |
| meeting_time  | Next Action Date                | date (repurposed for booking time) |
| source        | Source                          | select |
| status        | Status                          | select |
| research      | Notes                           | rich_text (truncate to 2000 chars) |
| gmail_draft   | MISSING                         | (write URL into Next Action text) |
| booking_id    | MISSING                         | (append to Notes block) |
| company_url   | URL (To link and rollup later)  | rich_text |
| next_action   | Next Action                     | rich_text |

## Missing concepts (no matching property)

- `gmail_draft` : no URL-typed property exists. Plan: write `"Gmail draft: <url>"` into the `Next Action` rich_text, and include the URL in the Telegram notification. Report as `fields_skipped=["gmail_draft"]`.
- `booking_id` : no property. Plan: include booking_id in the appended Notes block (prefix `[booking:<id>]`). Report as `fields_skipped=["booking_id_property"]` (still captured in body).

## Semantic mismatches (use with care)

- `Contact Name` is rich_text. The DB uses `Lead/Company` as the title. Convention for inbound: write the person's full name into `Lead/Company` (title) and leave `Contact Name` empty, OR write the company into `Lead/Company` and the person into `Contact Name`. **Decision: write person name into title `Lead/Company` (matches existing row convention where title = who we are talking to), write company into `Contact Name`.**
- `Next Action Date` is the only date property. Repurpose for the Calendly meeting start time. If a future task needs a separate "next action date" vs "meeting time", add a second date property.
- `Notes` rich_text cap: Notion rich_text limit is 2000 chars per block chunk. Research summary goes into `Notes` trimmed to 2000 chars; full research goes into page body as appended blocks.

## Select option values observed

| Property | Options |
|---|---|
| Status   | New, Reached Out, Call Booked, Proposal Sent, Won, Lost |
| Source   | LinkedIn, X, Referral, Speaking, Other |
| Offer Type | Sprint, Advisory, Pilot, Roundtable, Agency |
| Project  | MASTER RESET |

### Select values the inbound routine will write

- `Status` : `Call Booked` on first enrichment (a Calendly booking exists). On rebook, leave unchanged unless currently `New` or `Reached Out`, in which case bump to `Call Booked`.
- `Source` : **`Other` for now.** The existing options do not include `Calendly` or `Formspree`. Do not auto-create new select options (Notion API requires the option to exist or will reject the write). Flag in LogResult.warnings: `"Source set to Other; add Calendly + Formspree options to Source select to track channel."`

## Decisions locked

1. Title (`Lead/Company`) = person name on inbound rows.
2. `Contact Name` rich_text = company name.
3. `Next Action Date` = meeting_time.
4. `Notes` rich_text (<=2000 chars) = research summary; full research in appended page blocks.
5. `URL (To link and rollup later)` rich_text = company website URL.
6. `Next Action` rich_text = `"Review Gmail draft: <draft_url>"` or `"Send welcome email"` when draft missing.
7. `Source` = `Other` until user adds `Calendly` and `Formspree` options to that select.
8. `Status` = `Call Booked` on first enrichment.

## Open items for user

- Add `Calendly` and `Formspree` options to `Source` select (manual, 30 sec in Notion).
- Optional future: add `Gmail Draft` URL property, `Booking ID` rich_text property, separate `Meeting Time` date property. Not blocking.

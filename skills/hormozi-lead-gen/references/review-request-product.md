# Review Request System — SW Deliverable Spec

Standalone add-on. Sell to any SW lead with low review count (score_gmb_lead fires "low_reviews").
Price: $297-497 one-time setup + $97/mo optional monitoring.
Build time: 2-3 hours (n8n + Twilio + Google review link).

---

## What it does

After every job completion, owner receives a one-tap prompt to send the customer
a review request SMS. Customer gets a direct link to their Google review page.
No friction. No app. No "leave us a review" at the end of a call.

Result: review count doubles in 60-90 days on average (article benchmark).

---

## Why it sells itself

When you pitch this to a business with 8 reviews:
> "The top HVAC company in Salt Lake has 340 reviews. You have 8.
> That gap is the reason they get the call before you.
> I can close that gap in 60 days with a system that runs itself —
> you just tap a button after each job."

It's not AI hype. It's a visible, fixable gap they already feel.

---

## How to build it (n8n + Twilio)

### Step 1: Get the Google review link

Every Google Business profile has a direct review URL:
`https://search.google.com/local/writereview?placeid=<PLACE_ID>`

Find PLACE_ID: Google Maps → share → copy link → extract `place_id` param.
Or use Serper Maps API — `_serper_maps_search` already returns place data.

### Step 2: n8n workflow

```
Trigger: Webhook (owner hits button in simple web form OR SMS reply)
  ↓
Node: HTTP Request → Twilio Send SMS
  To:      customer phone
  From:    owner's Twilio number
  Body:    "Hi [customer name], thanks for choosing [business]!
            Would you mind leaving us a quick review?
            It takes 30 seconds and helps us a lot:
            [Google review link]"
  ↓
Node: Postgres/Airtable → log send (customer, date, status)
```

### Step 3: Owner interface (minimal)

Option A (simplest): owner bookmarks a URL like
`https://your-n8n.com/webhook/review?biz=joes-hvac&customer=John&phone=8015551234`
— fills in customer name + phone, hits send. Done.

Option B (slightly better): one-page HTML form served from VPS.
Fields: customer first name, customer phone. Submit fires the webhook.

### Step 4: Monthly report (optional $97/mo add-on)

Cron: pull current review count from Serper Maps → compare to baseline
stored at onboarding → send owner a Telegram or email:
"This month: 8 → 23 reviews (+15). You are now ranked #4 in Salt Lake for HVAC."

---

## Pricing logic (Hormozi framing)

| Tier | What's included | Price |
|------|----------------|-------|
| Starter | n8n workflow + Google link + owner training | $297 one-time |
| Growth | Starter + custom SMS copy + 90-day monitoring report | $497 one-time |
| Retainer | Growth + monthly review count report + refresh SMS copy | +$97/mo |

Lead with Starter. Upsell Retainer after they see the first 15 reviews come in.

---

## When to pitch it

Trigger: any SW qualified lead where `score_gmb_lead` fires `low_reviews` signal.
In cold call: after they engage on the review gap, before you pitch the website.
In T5 (SaaS audit upsell): include review automation as the "quick win" line item.

---

## Integration with SW pipeline

- `score_gmb_lead` already flags `low_reviews` leads
- Cold call scripts reference this offer in the offer menu
- Future: auto-attach review-request upsell section to T3/T4 for low-review leads

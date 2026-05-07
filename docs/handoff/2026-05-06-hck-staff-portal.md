# Session Handoff - HCK Staff Portal Full Build - 2026-05-06

## TL;DR

Full end-to-end build of Hotel Club de Kipé staff portal. Fixed ES6→ES5 violations across all pages, standardized navigation active state (gold fill), fixed calendar auto-render, standardized date format to "Mer 07 Mai 2026", diagnosed and fixed three-layer data failure (wrong Supabase client + async race + RLS), rewrote invoice print format to match real HCK PDF, implemented invoice business rules (cancel/archive with mandatory note, admin-only, history = read-only), wired admin settings + pricing tabs to correct DB schema, seeded real hotel data, committed + pushed to GitHub.

## What was built / changed

- `staff/js/api.js` — getClient() reuses supabaseClient from auth.js; getInvoices() orders by invoice_date; getSystemSettings() reads single row id=1 named columns; getPricing() queries rooms table; getTodayStats() counts draft+sent invoices; getReservationsForWeek() wrapped in try/catch
- `staff/js/auth.js` — requireAuth(onSuccess) callback pattern wired; all data loads inside callback
- `staff/js/config.js` — formatDate() → "Dim 07 Mai 2026" format; _MONTHS_FR array with correct French accents
- `staff/calendar.html` — all CSS classes renamed to mc-* prefix; renderCalendar() called immediately on DOMContentLoaded; reservationFor() fallback to room_id; notes field + saveNotes()
- `staff/dashboard.html` — quick-action row above calendar; nav active gold fill; formatDateObj column headers; loadStats counts draft+sent invoices
- `staff/invoices.html` — filterInvoices history/active split; cancelInvoice + archiveWithNote with mandatory window.prompt notes; history view zero action buttons; printInvoice() full HCK format rewrite; viewInvoice modal + Réimprimer; statusLabel/statusClass for 'cancelled'
- `staff/admin.html` — renderPricing shows all 12 rooms individually; editRate/saveRate by room.id; fillSettingsForm reads mapped settings keys; requireAdmin inside DOMContentLoaded
- `staff/css/staff.css` — sidebar 260px; .nav-item.active gold gradient; .admin-only display:flex; mobile breakpoint 820px
- `supabase/migrations/002_alias_columns.sql` — alias columns on reservations + invoices for JS name matching
- `supabase/migrations/003_rls_policies.sql` — FOR ALL TO authenticated USING (true) on all 8 tables
- Manual SQL run: system_settings RLS — dropped conflicting policies from 001, recreated clean

## Decisions made

- **ES5 only** — no bundler, must work on all browsers without transpilation
- **mc-* CSS prefix** for calendar grid — avoids staff.css .cal-grid collision
- **requireAuth(onSuccess) callback** — all data loads inside callback, never after synchronously
- **getClient() reuses supabaseClient** — no second unauthenticated client ever
- **system_settings = single row id=1 named columns** — NOT key/value pairs
- **getPricing() = rooms table** — no room_rates table exists
- **Invoice history = read-only** — no action buttons, nothing disappears, cancelled/archived stay forever
- **Cancel + archive = admin only + mandatory typed note** — saved to internal_notes + cancellation_reason
- **Real hotel data seeded**: Hôtel Club de Kipé, Kipé Dadia, Conakry, +224 669 69 99 99, hotelclubdekipe@gmail.com, RCCM/GN.TCC.2019.0 5769

## What is NOT done (explicit)

- TEST_ data not deleted yet — must run: `DELETE FROM clients WHERE full_name LIKE 'TEST_%'` + same for reservations + invoices
- Not deployed to Hostinger (staff.hotelclubkipe.com or /staff/ subdirectory)
- Public booking form still goes to WhatsApp (not wired to Supabase)
- Financial report page not built (admin only — sum paid/outstanding by month)
- agentsHQ NOT pushed to main (Boubacar's instruction)

## Open questions

- Which subdomain/path for Hostinger deploy: `staff.hotelclubkipe.com` or `hotelclubkipe.com/staff/`?
- Should public booking form be a separate page or inline on index.html?
- Financial report: by calendar month or by booking period?

## Next session must start here

1. Delete TEST_ data: run in Supabase SQL editor:
   ```sql
   DELETE FROM invoices WHERE invoice_number LIKE 'HCK-2026-000%' AND internal_notes LIKE '%TEST%';
   DELETE FROM reservations WHERE id IN (SELECT r.id FROM reservations r JOIN clients c ON r.client_id = c.id WHERE c.full_name LIKE 'TEST_%');
   DELETE FROM clients WHERE full_name LIKE 'TEST_%';
   ```
2. Deploy to Hostinger — upload `output/websites/hotelclubkipe-site/` to target subdomain/path
3. Confirm `.htaccess` clean URL rules if using subdirectory (see `feedback_hostinger_clean_urls.md`)
4. Push agentsHQ to main if Boubacar approves

## Files changed this session

```
output/websites/hotelclubkipe-site/
  staff/
    js/
      api.js
      auth.js
      config.js
    calendar.html
    dashboard.html
    invoices.html
    clients.html
    admin.html
    css/staff.css
  supabase/
    migrations/
      002_alias_columns.sql
      003_rls_policies.sql
docs/roadmap/harvest.md
memory/reference_hotelclubkipe_rebuild.md
```

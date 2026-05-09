# Hotel Club de Kipe -- Full Rebuild Brief

## BEFORE ANYTHING ELSE

Run these two skills on the live site and the repo before writing a single line of code:

1. `/website-teardown` on https://hotelclubkipe-site (GitHub repo: bokar83/hotelclubkipe-site) -- produce the internal viability report and identify all structural, UX, and content gaps
2. `/design-audit` on the current site -- score it and surface specific visual deficiencies to address in the rebuild

Do not proceed to architecture or implementation until both audits are complete and findings are incorporated into the build plan.

---

## PROJECT OVERVIEW

Full rebuild of Hotel Club de Kipe -- a real hotel in Conakry, Guinea. This is not a refresh. The current site is ~40% complete static HTML with stub content, a broken WhatsApp booking button, no backend, and placeholder copy. The rebuild replaces it entirely.

**Live repo:** bokar83/hotelclubkipe-site
**Current local path:** d:\Ai_Sandbox\agentsHQ\output\websites\hotelclubkipe-site\
**Current stack:** Pure HTML/CSS/vanilla JS, bilingual EN/FR via JS object swap
**Hostinger deployed:** Yes (static)

---

## WHAT EXISTS (use, do not discard)

- Bilingual EN/FR logic -- auto-detects Guinea and Francophone countries via ipapi.co, falls back to navigator.language. Keep and extend this.
- 21 actual hotel room photos at `public/Photos du Hotel et Club/HCKroom_01-21.jpg` -- use all 21
- Hotel logo at `public/images/` -- use in both frontend and backend/invoices
- Room structure already defined (see Rooms section below)

---

## TARGET: TWO DELIVERABLES

### Deliverable 1 -- Public-facing website (frontend)

Super professional, modern, mobile-first. French primary, English toggle. Comparable to a boutique 4-star hotel site in Europe or West Africa.

**Required sections:**
- Hero -- full-bleed, cinematic. Hotel name, tagline, CTA to booking
- About -- real copy about Hotel Club de Kipe (placeholder until client provides; write plausible FR/EN copy based on a Conakry Guinea boutique hotel)
- Rooms -- individual room cards for all rooms (102-104, 201-204, 301-305). Mini suites: 201, 301. Suites: 204, 304. Standard rooms: all others. Pricing TBD (leave as placeholder, structured to accept pricing data). Each card: photo from the 21 available, room type badge, amenities list, availability status (pulled from backend -- if booked, show "Non disponible / Unavailable"), Book button
- Gallery -- all 21 photos, masonry or lightbox grid
- Amenities -- restaurant, bar, pool, Wi-Fi, parking (expand based on teardown findings)
- Booking flow -- calendar date picker (check-in / check-out), room selector, guest name + contact fields. Real-time availability: if room is booked in backend for selected dates, it is greyed out and unselectable. On submit: reservation stored in Supabase, confirmation shown to guest
- Map -- Google Maps embed with precise Place ID for Hotel Club de Kipe, Conakry
- Contact -- working contact form (email via form submission service or Supabase edge function)
- Footer -- logo, address, phone, social links (placeholders)

**Design standard:** Premium. No stock-photo-hotel look. Use the actual room photos. Dark elegant palette acceptable (navy, gold, white) OR a warm West African palette -- run design-audit findings to decide. Typography: serif display + clean sans body. Micro-animations on scroll. No generic Bootstrap look.

---

### Deliverable 2 -- Staff backend (hotel management system)

**Hosting:** Supabase (auth, database, real-time). Frontend of backend: static HTML/JS hosted on Hostinger in a password-protected subdirectory, OR a separate Hostinger subdomain (e.g. staff.hotelclubkipe.com). Use whichever is more robust and maintainable.

**Authentication:**
- Two roles: Admin and Staff
- Admin: full access, FR/EN toggle available
- Staff: FR primary only, limited access (no invoice deletion, no pricing edits, no user management)
- Login page: hotel logo, clean form, role auto-detected from Supabase auth

**Core modules:**

1. **Room Schedule / Calendar**
   - Visual calendar view of all rooms (102-104, 201-204, 301-305)
   - Color-coded by status: Available (green), Booked (red), Checked-in (amber), Maintenance (gray)
   - Click any cell: see reservation details or create new booking
   - New booking form: room selector, guest name, contact (phone + email), check-in date, check-out date, number of guests, notes, payment status (Paid / Partial / Pending)
   - Booking saved to Supabase -- instantly reflected on the public frontend calendar (real-time sync)
   - Admin can edit or cancel any booking. Staff can create and view only.

2. **Client Management**
   - Client list: name, contact, stay history, total revenue from client
   - Add new client manually or auto-created from frontend booking form
   - Client detail page: all past and upcoming reservations, invoices

3. **Invoice Generator**
   - Create invoice from any reservation
   - Invoice fields: client name, room number, room type, check-in/out dates, number of nights (auto-calculated), nightly rate (entered manually until pricing API is built), subtotal, taxes (configurable %), total
   - Hotel logo on invoice
   - Invoice language: FR primary (amounts in GNF or EUR -- add currency selector)
   - PDF export: primary output. Clean, professional layout. Print-ready.
   - Admin only: edit, delete, resend. Staff: create and view only.
   - Invoice numbering: auto-increment with prefix HCK-YYYY-NNNN

4. **Admin panel (admin only)**
   - User management: add/remove staff accounts, reset passwords
   - Pricing editor: set nightly rate per room type (Standard / Mini Suite / Suite). These rates auto-populate invoice fields.
   - System settings: hotel name, address, tax rate, currency, contact email

**Rooms in system:**
- 102, 103, 104 -- Standard
- 201, 202, 203 -- Standard (201 = Mini Suite)
- 204 -- Suite
- 301, 302, 303, 304, 305 -- Standard (301 = Mini Suite, 304 = Suite)

Total: 13 rooms across 3 floors.

---

## TECH STACK DECISION

**Frontend (public site):** Vanilla HTML/CSS/JS or lightweight Vite + vanilla TS -- no heavy framework. Must stay static-deployable to Hostinger.

**Backend database + auth:** Supabase (free tier sufficient for this scale). Tables: rooms, reservations, clients, invoices, users. Real-time subscriptions for availability sync.

**PDF generation:** Use a client-side PDF library (jsPDF + autoTable, or similar) to generate invoices in-browser -- no server needed.

**Backend UI:** Can be a separate HTML/JS app in a `/staff/` subdirectory or subdomain on Hostinger.

---

## CONSTRAINTS

- All room photos and logo already exist in the repo -- use them, do not source new images
- Pricing is TBD -- build all pricing fields as editable via admin panel, not hardcoded
- Orange Money payment integration is a future phase -- architect so it can be added later without restructuring
- Stripe is also a future phase -- same note
- No em dashes anywhere in code or copy
- French copy is primary; English is secondary toggle
- Backend French primary for staff; FR/EN toggle for admin only

---

## SEQUENCE

1. Run /website-teardown on current site
2. Run /design-audit on current site
3. Incorporate audit findings into final design direction
4. Architect Supabase schema (rooms, reservations, clients, invoices, users)
5. Build frontend public site
6. Build backend staff system
7. Wire real-time availability sync between frontend and backend
8. Test booking flow end-to-end: guest books on frontend -> appears in staff calendar -> invoice can be generated
9. Deploy frontend to Hostinger (bokar83/hotelclubkipe-site repo)
10. Deploy backend to Hostinger subdirectory or subdomain

---

## INPUTS STILL NEEDED FROM BOUBACAR (collect before build, not a blocker for architecture)

- Room pricing per type (Standard / Mini Suite / Suite) in GNF and/or EUR
- Real about text for the hotel
- WhatsApp number
- Preferred currency display (GNF, EUR, or both)
- Google Maps Place ID for Hotel Club de Kipe Conakry (or confirm address for lookup)
- Staff email addresses for initial backend accounts
- Preferred subdomain for backend (e.g. staff.hotelclubkipe.com) or subdirectory (/staff/)

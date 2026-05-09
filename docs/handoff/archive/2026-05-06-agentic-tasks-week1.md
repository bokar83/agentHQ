# Week 1 Agentic Tasks — May 6-12, 2026

Three tasks runnable in parallel as independent agents. Each is self-contained.
All three should be done before May 12. Launch in one session or separately.

---

## Task 1: Content Board Cleanup

**Goal:** Remove noise from the Notion Content Board so it is a clean, usable queue.

**Working directory:** d:\Ai_Sandbox\agentsHQ
**Today's date:** 2026-05-06

**What to do:**

1. Query the Notion Content Board database. The database is in The Forge 2.0 workspace.
   Find it by searching for "Content Board" in Notion via MCP tools.

2. **Delete (archive) 15 junk records** — criteria for junk:
   - Status = Idea with no body/content filled in AND no scheduled date
   - Duplicate titles (same post concept, different records)
   - Records with placeholder text only ("TBD", "draft", blank body)
   Archive them (archived: true), never hard delete.

3. **Route 35+ worker/fear posts** — identify all posts with topics about:
   - Job displacement, AI taking jobs, layoffs, automation fear, worker anxiety
   - Current platform routing: likely LinkedIn or unassigned
   - Correct routing:
     - humanatwork.ai: PRIMARY home for all worker/fear content
     - X (Twitter): also fine — update Platform field
     - LinkedIn: max 1/month, only if reframed for business leaders
     - Studio (AI Catalyst, First Gen Money): if angle fits those channels
   - Update the Platform field on each record to match correct routing.

4. **Collapse duplicates** — if 30+ records share the same draft/topic:
   - Keep the most complete version
   - Archive the rest with a note: "Duplicate of [kept record title]"

5. Report: how many archived, how many re-routed, how many collapsed. List any ambiguous cases.

---

## Task 2: geolisted.co Trade Pages (/hvac, /roofing, /dental)

**Goal:** Build three new landing pages on geolisted.co targeting trade contractors.

**Working directory:** d:\Ai_Sandbox\agentsHQ
**Repo:** d:\Ai_Sandbox\agentsHQ\output\websites\geolisted-site\
**Live site:** geolisted.co (Hostinger, auto-deploys on push to main)
**Dev server:** python3 -m http.server 8080 from output\ — preview at localhost:8080

**What to build:**

Three pages: `hvac.html`, `roofing.html`, `dental.html` in the geolisted-site repo root.

**Page formula (same structure for all three, swap [Trade]):**

- Title: "Why ChatGPT Won't Recommend Your [Trade] Business"
- H1: same as title
- Key stat (large, prominent): "ChatGPT recommends only 1.2% of local businesses"
- Body: 3 short paragraphs — (1) the problem (AI invisibility), (2) what it costs (leads going to competitors who ARE cited), (3) what Signal Works fixes
- CTA: Two options — "Get a Free AI Visibility Audit" (links to Calendly: https://calendly.com/boubacarbarry/signal-works-discovery-call) and "See the $997 Fix" (links to /997)
- Design: match existing geolisted.co site style exactly (same colors, fonts, nav, footer)
- Schema: LocalBusiness + Service JSON-LD on each page

**Trade-specific copy hints:**
- HVAC: "When a homeowner asks ChatGPT for a trusted HVAC company in [city], is your name there?"
- Roofing: "Storm season is here. Homeowners are asking AI for roofers. Are you showing up?"
- Dental: "Patients search differently now. They ask ChatGPT. Your competitors are already there."

**After building:**
1. Run design audit (check localhost:8080/hvac.html etc.)
2. Add .htaccess RewriteRule entries for /hvac, /roofing, /dental clean URLs (already has .htaccess — just add lines)
3. Get approval before pushing to Hostinger

**Do NOT push without showing localhost preview first.**

---

## Task 3: calculatorz.tools Schema Fix

**Goal:** Add structured data to all 46 calculator pages to improve Google indexing and AI citation.

**Working directory:** d:\Ai_Sandbox\agentsHQ
**Site repo:** find the calculatorz.tools repo or files in output/websites/ or ask Boubacar for location if not found.

**What to do (Month 1 only — 4 hours max, then hands-off for 6 months):**

1. **SoftwareApplication + FAQPage JSON-LD on all 46 pages (highest ROI action)**
   - SoftwareApplication schema: applicationCategory="UtilityApplication", operatingSystem="Web", offers free
   - FAQPage schema: 3-5 Q&A pairs per calculator relevant to what it calculates
   - Inject into `<head>` of each page

2. **State variant pages** — "Take-home pay calculator [state]" x 50 states = 150 new pages
   - Template: clone the main take-home pay calculator page
   - Change title, H1, and add state-specific note ("Based on [State] state tax rates")
   - Add to sitemap

3. **Add Date/Time category** — "hours worked calculator" (90K/mo search volume, low KD)
   - Build one page: hours-worked-calculator.html
   - Simple form: start time + end time = hours worked, with break deduction option

4. **Add Conversion category** — two pages:
   - hex-to-rgb.html ("hex to RGB" — 200K+/mo)
   - cm-to-inches.html ("cm to inches" — 500K+/mo)
   - Simple converters, clean UI matching site style

5. **Submit to directories:**
   - Product Hunt (Boubacar action — flag this, don't submit autonomously)
   - 5 tool directories: alternativeto.net, toolify.ai, theresanaiforthat.com, saashub.com, futurepedia.io — research submission process and report back

6. After all changes: run design audit on updated pages.

**After Month 1: STOP. Do not add more features. Google sandbox runs regardless. Next review = November 2026.**

---

## Notes for all three tasks

- Working directory: d:\Ai_Sandbox\agentsHQ
- Commit changes per the project's git workflow (claim file before edit, atomic commit)
- Do NOT push to production without showing output for approval first (geolisted.co and calculatorz.tools)
- Content Board changes go direct — no approval needed (it's internal data cleanup)
- Update Execution Cycle database in Notion (database ID: 358bcf1a-3029-81ad-ace1-fd12c452ea11): mark each task Done when complete

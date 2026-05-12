---
name: hostinger-deploy
description: "THE production deploy path for all websites. Use for every live/production website deployment — always the right choice when a site needs to go live. Vercel is for previews only; Hostinger is where real sites live. Full workflow: repo setup, local folder in agentsHQ, GitHub push, Hostinger Git auto-deploy. Triggers on \"hostinger\", \"deploy to hostinger\", \"hostinger deploy\", \"publish to hostinger\", \"live deploy\", \"go live\", \"push to production\"."
user-invocable: true
---

# Hostinger Website Deploy Skill

> **This is the production deploy path.** All live websites go here. Vercel is for preview/testing only.

Use this skill whenever:
- Creating a new static website for a client or project
- Updating an existing site and pushing live
- Setting up Hostinger ↔ GitHub auto-deploy for a new domain

---

## Folder Structure (agentsHQ)

All websites live here — work and test locally, push to GitHub when ready to go live:

```
d:\Ai_Sandbox\agentsHQ\output\websites\
  └── {repo-name}\          ← git repo root, connected to GitHub
        ├── index.html
        ├── og-image.jpg
        ├── {photo}.jpg
        └── {logo}.jpg
```

Working/preview files stay in:
```
d:\Ai_Sandbox\agentsHQ\output\
  └── {sitename}.html       ← active dev file (e.g. v2.html)
```

Dev server: `python3 -m http.server 8080` from `d:\Ai_Sandbox\agentsHQ\output\`
Preview at: `http://localhost:8080/{filename}.html`

---

## HARD RULES (learned in production)

**Clean URLs require `.htaccess`:** Hostinger Apache serves static files by exact filename only. `/997` returns 404; `/997.html` returns 200. Every site with clean URL paths needs this in repo root:
```apache
Options -Indexes
DirectorySlash Off
RewriteEngine On

# For each <name>.html that has a sibling <name>/ directory (e.g. signal.html + signal/),
# add an explicit early rewrite BEFORE the generic rule. Without this, Apache/LiteSpeed
# auto-trailing-slashes /name → /name/ → 403 (Options -Indexes blocks listing).
# REPLACE the example with the real names from your site's `*.html + same-name dir/` audit:
RewriteRule ^signal/?$ signal.html [NC,L]

# Generic clean-URL rule — depth-agnostic, matches across "/"
RewriteCond %{REQUEST_FILENAME} !-f
RewriteCond %{REQUEST_FILENAME} !-d
RewriteRule ^([^\.]+)$ $1.html [NC,L]

# Force browsers to revalidate HTML so future 403 fixes propagate immediately
# rather than living in client caches for hours.
<FilesMatch "\.(html|htm)$">
  Header set Cache-Control "no-cache, must-revalidate, max-age=0"
</FilesMatch>
```
Commit this with the site. Do not wait for the 404 to discover it.

**PRE-DEPLOY AUDIT: `.html` + same-name dir collision causes silent 403.** Before every deploy, run this audit at the site root:
```bash
for f in *.html; do
  name="${f%.html}"
  if [ -d "$name" ]; then
    echo "COLLISION: /$name will 403 — both $f and $name/ exist; add 'RewriteRule ^$name/?$ $f [NC,L]' to .htaccess BEFORE the generic clean-URL rule"
  fi
done
```
If the audit reports any collision, the `.htaccess` MUST have a matching `RewriteRule ^<name>/?$ <name>.html [NC,L]` rule before deploy. Verified 2026-05-11 on catalystworks.consulting — `/signal` returned 403 for hours after the first deploy because `signal.html` + `signal/` collided and the `.htaccess` only handled `^signal$` (no trailing slash). Fix needed both no-slash AND with-slash forms. See `feedback_directory_vs_html_collision_403.md`.

**Local sandbox = no push without approval:** Test changes locally → show result to Boubacar → push only if approved. Never push to "sync" a revert of your own local test. The live site was never touched.

**Vercel = preview/mobile test only. NEVER production.** The deploy-to-vercel skill description now reflects this. All live sites → Hostinger.

**Next.js 15 partial dynamic segments cause site-wide 404.** A folder named `prefix-[slug]/` (mixing literal text + dynamic param in the same segment) is silently ignored by the App Router. Symptoms: build prerenders the routes locally but production returns 404. Fix: rename to nested `prefix/[slug]/` and add a `rewrites()` block to `next.config.ts` so the public flat URL keeps working:
```ts
async rewrites() {
  return [
    { source: '/foo/prefix-:slug/', destination: '/foo/prefix/:slug/' },
  ]
},
```
Caught on calculatorz.tools 2026-05-07 (51 state-paycheck pages). See `feedback_nextjs15_partial_dynamic_segments.md`.

**Next.js `rewrites()` DOES survive Hostinger deploy (confirmed 2026-05-07 on calculatorz.tools).** Both flat (`/finance/take-home-pay-calculator-california/`) and nested (`/finance/take-home-pay-calculator/california/`) returned 200 in production. No `.htaccess` Apache mirror needed when `rewrites()` is set in `next.config.ts`. Hostinger's Git auto-deploy preserves the Next.js routing layer. Still verify after every deploy: hit both flat + nested URLs — if flat 404s, fall back to mirroring rewrite in `.htaccess`.

**Repo-local SSL cert config can break GitHub push/pull.** Some calculatorz-app and similar Next.js repos ship with `http.sslCAInfo` pointing at `C:/Program Files/Git/mingw64/etc/ssl/certs/ca-bundle.crt` which doesn't exist on this machine. Symptom: `unable to get local issuer certificate (20)` on every git push/pull. **Do NOT edit the repo config** (CLAUDE.md hard rule). Bypass per-command:
```bash
git -c http.sslBackend=schannel -c http.sslCAInfo= push origin main
git -c http.sslBackend=schannel -c http.sslCAInfo= pull origin main
```
See `feedback_git_ssl_bypass_one_shot.md`.

---

## Workflow: New Website

### 1. Build & test
- Build in `output/{sitename}.html`
- Preview at localhost:8080
- Run design + SEO + conversion audits before going live

### 2. Pre-launch checklist
- [ ] Favicon wired (`<link rel="icon">`)
- [ ] OG image exists at 1200×630px (use headless Chrome screenshot)
- [ ] All form submissions wired (Formspree for static sites)
- [ ] No placeholder text or broken links
- [ ] Canonical URL correct
- [ ] Schema.org JSON-LD present
- [ ] Photo filenames clean (not IMG_XXXX)
- [ ] No redundant URLs in footer (you're already on the site)

### 3. Generate OG image
Create `output/og-image.html` with exact 1200×630 layout, then:
```bash
"C:/Program Files/Google/Chrome/Application/chrome.exe" \
  --headless=new \
  --screenshot="C:/tmp/og-image.jpg" \
  --window-size=1200,630 \
  --hide-scrollbars \
  "http://localhost:8080/og-image.html"

cp "C:/tmp/og-image.jpg" "d:/Ai_Sandbox/agentsHQ/output/og-image.jpg"
```

### 4. Set up local repo folder
```bash
mkdir -p "d:/Ai_Sandbox/agentsHQ/output/websites/{repo-name}"
cd "d:/Ai_Sandbox/agentsHQ/output/websites/{repo-name}"
git init
git remote add origin https://github.com/bokar83/{repo-name}.git
git fetch origin
git checkout -b main origin/main   # or just: git checkout -b main
```

### 5. Copy files in
```bash
cp output/{sitename}.html output/websites/{repo-name}/index.html
cp output/{photo}.jpg     output/websites/{repo-name}/
cp output/{logo}.jpg      output/websites/{repo-name}/
cp output/og-image.jpg    output/websites/{repo-name}/
```

### 6. Create GitHub repo (if new)
Use `mcp__plugin_github_github__create_repository`:
- name: `{repo-name}`
- description: "Production site for {domain}"
- private: false
- autoInit: false

### 7. Commit and push
```bash
cd "d:/Ai_Sandbox/agentsHQ/output/websites/{repo-name}"
git add index.html {photo}.jpg {logo}.jpg og-image.jpg
git commit -m "feat: launch {domain} v1"
git push origin main
# If rejected (non-fast-forward on existing repo): git push origin main --force
```

### 8. Connect Hostinger (one-time per domain)
1. Hostinger Control Panel → Hosting → select the domain
2. Git → Connect repository
3. Repository URL: `https://github.com/bokar83/{repo-name}`
4. Branch: `main`
5. Save → auto-deploy triggers on every push to `main`

After this, every `git push origin main` = live on the domain. No FTP needed.

---

## Workflow: Updating an Existing Site

1. Edit `output/{sitename}.html` (e.g. `v2.html`) — test at localhost:8080
2. When ready:
```bash
cp "d:/Ai_Sandbox/agentsHQ/output/{sitename}.html" \
   "d:/Ai_Sandbox/agentsHQ/output/websites/{repo-name}/index.html"

cd "d:/Ai_Sandbox/agentsHQ/output/websites/{repo-name}"
git add index.html
git commit -m "feat: {description of change}"
git push origin main
```
Hostinger auto-deploys within ~30 seconds.

---

## Formspree (contact/booking forms on static sites)

1. Go to formspree.io → create free account → New Form → paste email
2. Copy the form ID (e.g. `xykbdrqa`)
3. Wire into JS:
```js
const res = await fetch('https://formspree.io/f/{FORM_ID}', {
  method: 'POST',
  headers: { 'Content-Type': 'application/json', 'Accept': 'application/json' },
  body: JSON.stringify({ name, email, company })
});
```
Free tier: 50 submissions/month. Upgrade when needed.

---

## Active Sites

| Domain | Repo | Local path | Status |
|--------|------|------------|--------|
| catalystworks.consulting | bokar83/catalystworks-site | output/websites/catalystworks-site/ | live — webhook: https://webhooks.hostinger.com/deploy/6e7b77927d3ac47b526e707d0f67425b |

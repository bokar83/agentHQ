---
name: hostinger-deploy
description: Full workflow for creating, updating, and deploying static websites on Hostinger via GitHub. Covers repo setup, local folder structure in agentsHQ, GitHub push, and Hostinger Git integration. Triggers on "hostinger", "deploy to hostinger", "hostinger deploy", "publish to hostinger", "live deploy".
user-invocable: true
---

# Hostinger Website Deploy Skill

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

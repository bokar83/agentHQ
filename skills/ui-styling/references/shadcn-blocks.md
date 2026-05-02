# shadcn/ui Blocks (starter index)

The 27 production-ready v4 blocks from the upstream registry. Each is a complete, accessible, opinionated layout (dashboard / login / signup / sidebar) you can install with one CLI call and customize.

**Authoritative source:** `cache/llms-<date>.txt` + the upstream registry at `https://ui.shadcn.com`. Refresh via `scripts/refresh-shadcn-cache.sh`.

## Why this index exists

Blocks are 80% of the layout work for SW client previews and CW client portals. Don't hand-roll a dashboard or login page; install the closest block and override styling. `vercel-launch` and `frontend-design` can grep the `starter:` tag below to find a match.

## How to install any block

```bash
npx shadcn@latest add <block-name>
```

Components install into your `components/ui/` and `app/` paths per `components.json`. Every block already pulls in its underlying primitives (sidebar, breadcrumb, button, etc.) via `registryDependencies`.

## Block index

Format: `block-name | category | starter:tag | one-line | install`

### Dashboard (1)

- `dashboard-01 | dashboard | starter:admin-dashboard | A dashboard with sidebar, charts and data table. | npx shadcn@latest add dashboard-01`

### Login (5)

- `login-01 | auth | starter:login-simple | A simple login form. | npx shadcn@latest add login-01`
- `login-02 | auth | starter:login-split-cover | A two column login page with a cover image. | npx shadcn@latest add login-02`
- `login-03 | auth | starter:login-muted-bg | A login page with a muted background color. | npx shadcn@latest add login-03`
- `login-04 | auth | starter:login-form-and-image | A login page with form and image. | npx shadcn@latest add login-04`
- `login-05 | auth | starter:login-magic-link | A simple email-only login page. | npx shadcn@latest add login-05`

### Signup (5)

- `signup-01 | auth | starter:signup-simple | A simple signup form. | npx shadcn@latest add signup-01`
- `signup-02 | auth | starter:signup-split-cover | A two column signup page with a cover image. | npx shadcn@latest add signup-02`
- `signup-03 | auth | starter:signup-muted-bg | A signup page with a muted background color. | npx shadcn@latest add signup-03`
- `signup-04 | auth | starter:signup-form-and-image | A signup page with form and image. | npx shadcn@latest add signup-04`
- `signup-05 | auth | starter:signup-social-providers | A simple signup form with social providers. | npx shadcn@latest add signup-05`

### Sidebar (16)

- `sidebar-01 | sidebar | starter:sidebar-section-grouped | A simple sidebar with navigation grouped by section. | npx shadcn@latest add sidebar-01`
- `sidebar-02 | sidebar | starter:sidebar-collapsible-sections | A sidebar with collapsible sections. | npx shadcn@latest add sidebar-02`
- `sidebar-03 | sidebar | starter:sidebar-submenus | A sidebar with submenus. | npx shadcn@latest add sidebar-03`
- `sidebar-04 | sidebar | starter:sidebar-floating-submenus | A floating sidebar with submenus. | npx shadcn@latest add sidebar-04`
- `sidebar-05 | sidebar | starter:sidebar-collapsible-submenus | A sidebar with collapsible submenus. | npx shadcn@latest add sidebar-05`
- `sidebar-06 | sidebar | starter:sidebar-dropdown-submenus | A sidebar with submenus as dropdowns. | npx shadcn@latest add sidebar-06`
- `sidebar-07 | sidebar | starter:sidebar-icon-collapse | A sidebar that collapses to icons. | npx shadcn@latest add sidebar-07`
- `sidebar-08 | sidebar | starter:sidebar-inset-secondary-nav | An inset sidebar with secondary navigation. | npx shadcn@latest add sidebar-08`
- `sidebar-09 | sidebar | starter:sidebar-collapsible-nested | Collapsible nested sidebars. | npx shadcn@latest add sidebar-09`
- `sidebar-10 | sidebar | starter:sidebar-popover | A sidebar in a popover. | npx shadcn@latest add sidebar-10`
- `sidebar-11 | sidebar | starter:sidebar-file-tree | A sidebar with a collapsible file tree. | npx shadcn@latest add sidebar-11`
- `sidebar-12 | sidebar | starter:sidebar-calendar | A sidebar with a calendar. | npx shadcn@latest add sidebar-12`
- `sidebar-13 | sidebar | starter:sidebar-dialog | A sidebar in a dialog. | npx shadcn@latest add sidebar-13`
- `sidebar-14 | sidebar | starter:sidebar-right | A sidebar on the right. | npx shadcn@latest add sidebar-14`
- `sidebar-15 | sidebar | starter:sidebar-left-and-right | A left and right sidebar. | npx shadcn@latest add sidebar-15`
- `sidebar-16 | sidebar | starter:sidebar-sticky-header | A sidebar with a sticky site header. | npx shadcn@latest add sidebar-16`

## Routing for downstream skills

`vercel-launch`, `frontend-design`, `hostinger-deploy`, and `clone-builder` should grep this file by `starter:<tag>` rather than re-deriving block choices from scratch. Example:

```bash
# Find an admin dashboard starter
grep "starter:admin-dashboard" skills/ui-styling/references/shadcn-blocks.md
```

## When NOT to use a block

- The brand standard is editorial / cinematic / scrollytelling (Volta tier) - blocks are utilitarian and need significant restyling. Reach for `frontend-design` first.
- The site is a marketing landing page (no auth, no dashboard, no nav-heavy app shell) - blocks won't fit; use `frontend-design` patterns.
- The client requires a non-React stack - blocks are React-only.

## Refresh discipline

When `scripts/refresh-shadcn-cache.sh` runs, this file does **not** auto-update. If the upstream registry adds blocks (e.g., `dashboard-02`, `login-06`), update this index by hand and bump the date in the cache header. The 27-block count above is a snapshot of upstream as of 2026-05-02.

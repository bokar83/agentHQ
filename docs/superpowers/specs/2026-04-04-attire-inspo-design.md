# Attire Inspo — Design Spec
**Date:** 2026-04-04
**App name:** Aminöa's AI — Attire Inspo
**Repo/folder:** `attire-inspo`
**Local build path:** `D:\Ai_Sandbox\agentsHQ\output\apps\attire-inspo-app`
**Deploy target:** Vercel (PWA — installable on iOS/Android home screen)
**Backend:** FastAPI at `http://72.60.209.109:8080` (existing, unchanged)

---

## 1. Stack

| Layer | Choice | Reason |
|-------|--------|--------|
| Framework | Next.js 14 App Router | Best Vercel integration, zero-config PWA, SSR for fast first paint |
| PWA | next-pwa (ducanh-next-pwa) | Battle-tested Workbox integration, works on Vercel out of the box |
| Styling | Tailwind CSS v3 | Utility-first, easy to match custom palette |
| Components | shadcn/ui (Radix primitives) | Copy-paste, fully customisable, accessible |
| Animations | Framer Motion | React-native, gesture support, AnimatePresence for page transitions |
| Language | TypeScript | Type safety on API responses |
| Package manager | npm |

---

## 2. Design System

### Colour palette
```css
--bg:        #080610   /* deep space background */
--surface:   rgba(255,255,255,0.04)
--border:    rgba(255,255,255,0.10)
--accent:    #c77dff   /* lavender */
--lilac:     #e0aaff
--rose:      #ff85a1
--champagne: #ffd6a5
--text:      #f0eaff
--muted:     rgba(240,234,255,0.50)
```

### Typography
- **Headings:** Syne (700/800) — Google Fonts
- **Body:** Inter (300–600) — Google Fonts
- Base size: 16px, scale: 0.75rem → 1.5rem

### Visual language (Aurora Feed direction)
- Full-bleed aurora radial gradients as fixed background (purple top-left, rose bottom-right, lilac mid)
- Glassmorphism cards: `backdrop-filter: blur(20px)`, `background: rgba(255,255,255,0.04)`, 1px border
- Pill buttons with gradient fill for primary CTAs
- Framer Motion page transitions: slide-in from right on forward nav, slide from left on back
- `whileTap={{ scale: 0.97 }}` on all interactive elements for native feel

---

## 3. App Structure

### Folder layout
```
attire-inspo/
├── app/
│   ├── layout.tsx          # root layout: fonts, PWA meta, aurora bg, bottom nav
│   ├── page.tsx            # Home — aurora feed, greeting, vibe chips, wardrobe preview
│   ├── closet/
│   │   └── page.tsx        # Closet — category filters + 2-col grid + FAB to add
│   ├── add/
│   │   └── page.tsx        # Add a Piece — camera upload + AI analysis
│   ├── ideas/
│   │   └── page.tsx        # Outfit Ideas — visual mood cards + generate
│   ├── rate/
│   │   └── page.tsx        # Rate My Fit — photo upload + AI rating
│   └── api/
│       └── proxy/
│           └── route.ts    # Vercel Edge proxy → FastAPI backend
├── components/
│   ├── BottomNav.tsx       # fixed bottom tab bar
│   ├── AuroraBackground.tsx # fixed radial gradient layer
│   ├── GlassCard.tsx       # reusable glassy card wrapper
│   ├── MoodCard.tsx        # visual mood card (Ideas screen)
│   ├── CategoryFilter.tsx  # scrollable pill filter bar (Closet)
│   ├── WardrobeGrid.tsx    # 2-col responsive grid
│   ├── WardrobeItem.tsx    # individual item card with delete
│   ├── UploadZone.tsx      # drag/tap upload with preview
│   └── ResultBox.tsx       # AI response display with loading state
├── lib/
│   ├── api.ts              # typed fetch wrapper → /api/proxy
│   └── types.ts            # WardrobeItem, OutfitSuggestion, etc.
├── public/
│   ├── manifest.json       # PWA manifest
│   ├── icon-192.png        # PWA icon
│   └── icon-512.png        # PWA icon
├── next.config.js          # next-pwa config
├── tailwind.config.ts      # custom palette + Syne/Inter fonts
└── package.json
```

---

## 4. Screens

### Home (`/`)
- Fixed aurora background (persistent across all pages)
- Greeting: "Hey Aminöa 👋 / What's the vibe today?"
- Horizontal scrollable vibe chip row (10 vibes, tappable, stores selection in localStorage)
- "Your Closet" section: first 4 items as horizontal scroll preview cards
- "Get Outfit Ideas" CTA button → navigates to `/ideas` with selected vibes pre-filled
- If closet is empty: empty state with "Add your first piece →" CTA

### Closet (`/closet`)
- Page header: "My Closet" + count badge
- Category filter bar (scrollable pills): All / Tops / Bottoms / Dresses / Outerwear / Shoes / Bags / Accessories
- 2-col responsive grid, portrait aspect ratio cards
- Each card: photo (or emoji placeholder), name, category tag, delete button (appears on long-press)
- Floating action button (glowing lavender ➕) bottom-right → navigates to `/add`
- Framer Motion: `AnimatePresence` for item removal animation, stagger on grid mount

### Add a Piece (`/add`)
- Upload zone: tap to open camera/gallery (iOS camera capture), drag-drop on desktop
- Image preview after selection
- After upload: POST to `/api/proxy?endpoint=/upload-item`
- Claude AI auto-fills: name, category, color, style, season, tags
- User can edit any field before saving
- Save → adds to closet, Framer Motion success animation, navigate back to `/closet`

### Outfit Ideas (`/ideas`)
- "Pick your mood" section: 2-col grid of visual mood cards
  - Each card has colour personality, icon, name
  - Moods: 🎀 Coquette (pink), 🕯 Dark Academia (deep purple), 💜 Y2K Glam (lilac), 🌿 Cottagecore (sage), 🤍 Clean Girl (white/grey), 🏋 Sporty Chic (electric blue), 🌙 Night Out (deep rose), 📚 School Day (warm amber)
  - Multi-select with toggle
- Occasion text field ("e.g. Birthday dinner, first day of school")
- Weather/season field
- "Generate Outfit Ideas ✨" gradient CTA button
- POST to `/api/proxy?endpoint=/suggest-outfits`
- Loading state: animated spinner card "Your AI stylist is working her magic…"
- Result: formatted markdown-style output in a glassy result card
- "Try another vibe" button resets chips only

### Rate My Fit (`/rate`)
- Upload zone for outfit photo
- Occasion field
- "Get My Rating ✨" button
- POST to `/api/proxy?endpoint=/analyze-outfit`
- Loading state with spinner
- Result displayed in glassy card with sections: Breakdown / Rating / What Works / Tips / Occasions

---

## 5. Backend Proxy

All frontend API calls go to `/api/proxy` (Vercel Edge Function), which forwards to the FastAPI VPS. This solves the HTTPS→HTTP mixed-content problem.

```typescript
// app/api/proxy/route.ts
export const runtime = 'edge'

export async function POST(request: Request) {
  const url = new URL(request.url)
  const endpoint = url.searchParams.get('endpoint') ?? ''
  const contentType = request.headers.get('content-type') ?? ''
  const body = await request.arrayBuffer()

  const vpsRes = await fetch(`http://72.60.209.109:8080${endpoint}`, {
    method: 'POST',
    headers: { 'content-type': contentType },
    body,
  })
  const data = await vpsRes.arrayBuffer()
  return new Response(data, {
    status: vpsRes.status,
    headers: { 'content-type': vpsRes.headers.get('content-type') ?? 'application/json' },
  })
}

export async function GET(request: Request) {
  const url = new URL(request.url)
  const endpoint = url.searchParams.get('endpoint') ?? ''
  const vpsRes = await fetch(`http://72.60.209.109:8080${endpoint}`)
  const data = await vpsRes.arrayBuffer()
  return new Response(data, { status: vpsRes.status,
    headers: { 'content-type': vpsRes.headers.get('content-type') ?? 'application/json' } })
}
```

Note: Vercel Edge Functions support HTTP outbound calls — no mixed-content block since it's server-to-server.

---

## 6. PWA Configuration

### `public/manifest.json`
```json
{
  "name": "Aminöa's AI — Attire Inspo",
  "short_name": "Attire Inspo",
  "description": "Your AI fashion stylist",
  "start_url": "/",
  "display": "standalone",
  "background_color": "#080610",
  "theme_color": "#c77dff",
  "orientation": "portrait",
  "icons": [
    { "src": "/icon-192.png", "sizes": "192x192", "type": "image/png" },
    { "src": "/icon-512.png", "sizes": "512x512", "type": "image/png", "purpose": "any maskable" }
  ]
}
```

### iOS-specific meta tags (in `app/layout.tsx`)
```html
<meta name="apple-mobile-web-app-capable" content="yes" />
<meta name="apple-mobile-web-app-status-bar-style" content="black-translucent" />
<meta name="apple-mobile-web-app-title" content="Attire Inspo" />
<link rel="apple-touch-icon" href="/icon-192.png" />
```

### `next.config.js`
```js
const withPWA = require('@ducanh2912/next-pwa').default({ dest: 'public', cacheOnFrontendNav: true })
module.exports = withPWA({ reactStrictMode: true })
```

---

## 7. State Management

- **Wardrobe data:** fetched from API on each page load, no global store (simple enough)
- **Selected vibes:** `localStorage` via a custom `useVibes` hook — persists across sessions
- **Selected category filter:** React `useState` in Closet page — resets on navigation
- No Redux/Zustand needed at this scope

---

## 8. API Client (`lib/api.ts`)

```typescript
const BASE = '/api/proxy'

export async function getWardrobe() { ... }          // GET ?endpoint=/wardrobe
export async function uploadItem(fd: FormData) { ... } // POST ?endpoint=/upload-item
export async function suggestOutfits(body: object) { ... } // POST ?endpoint=/suggest-outfits
export async function analyzeOutfit(fd: FormData) { ... }  // POST ?endpoint=/analyze-outfit
export async function deleteItem(id: string) { ... }       // DELETE via proxy
```

---

## 9. Vercel Deployment

1. Create GitHub repo `attire-inspo` under `bokar83`
2. Connect to Vercel (new project → import repo)
3. No env vars needed — backend URL is hardcoded in the proxy route
4. Every push to `main` auto-deploys
5. Custom domain optional later

---

## 10. PWA Install UX

- On Android: browser auto-shows "Add to Home Screen" banner after 2+ visits
- On iOS: show a one-time bottom sheet prompt after 3 seconds on first visit: "Tap Share → Add to Home Screen to install Attire Inspo"
- Prompt stored in `localStorage` so it only shows once
- Component: `InstallPrompt.tsx` — conditionally rendered in `layout.tsx`

---

## 11. Out of Scope (this version)

- User accounts / authentication
- Cloud image storage (images stay on VPS)
- Push notifications
- Outfit history / saved looks
- Social sharing

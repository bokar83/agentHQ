# Design Audit Checklist

Run this against every build before declaring done. Source: `redesign-skill` Design Audit (taste-skill, MIT).

Check each item. Flag failures. Fix before ship.

---

## Typography

- [ ] Not using Inter, Roboto, Arial, Open Sans, or Helvetica for headings : use Geist, Outfit, Cabinet Grotesk, or Satoshi
- [ ] Display headlines: `text-4xl md:text-6xl tracking-tighter leading-none` or equivalent
- [ ] Body text: `text-base leading-relaxed max-w-[65ch]` : not edge-to-edge
- [ ] More than two weight levels used (not just 400 + 700 : add 500/600 for hierarchy)
- [ ] Numbers in data-heavy UI use monospace or `font-variant-numeric: tabular-nums`
- [ ] Large headers use negative tracking; small labels use positive tracking
- [ ] No all-caps subheaders as default : try lowercase italic or sentence case
- [ ] No orphaned words on last line : use `text-wrap: balance` or `text-wrap: pretty`
- [ ] No gradient text as a shortcut for "premium"
- [ ] No serif fonts on dashboards or software UI

---

## Color and Surfaces

- [ ] No pure `#000000` : use off-black, zinc-950, or charcoal
- [ ] Accent saturation < 80% : desaturate to blend with neutrals
- [ ] Max one accent color : remove extras
- [ ] Gray family consistent : not mixing warm and cool grays
- [ ] No purple/blue "AI gradient" aesthetic
- [ ] Shadows tinted to background hue : not generic `rgba(0,0,0,0.1)`
- [ ] Flat sections have texture, noise, or grain : pure flat vectors feel sterile
- [ ] Gradients break uniformity : radial, noise, or mesh instead of flat 45-degree linear
- [ ] All shadows suggest a single consistent light source
- [ ] No random dark section in an otherwise light-mode page (and vice versa)
- [ ] Sections with no visual depth have background imagery, subtle pattern, or ambient gradient

---

## Layout

- [ ] Not everything centered and symmetrical : offset margins, left-aligned headers, mixed aspect ratios
- [ ] No 3-column equal card grid as feature row : use 2-col zig-zag, asymmetric grid, or horizontal scroll
- [ ] Full-height sections use `min-height: 100dvh` not `height: 100vh`
- [ ] Complex flex % math replaced with CSS Grid
- [ ] Max-width container present (1200-1440px, auto margins)
- [ ] Variable card heights allowed where content varies : not forced equal by flex
- [ ] Border-radius varies : tighter on inner elements, softer on containers
- [ ] At least one overlapping element for depth : not everything flat side-by-side
- [ ] Bottom padding optically larger than top where needed
- [ ] Buttons bottom-aligned across card groups regardless of content length above
- [ ] Feature list items start at same vertical position across columns
- [ ] Side-by-side elements have aligned baselines
- [ ] Mathematically centered elements checked for optical centering (icons in circles, text in buttons)
- [ ] Missing whitespace : double the spacing, let the design breathe

---

## Interactivity and States

- [ ] Hover states on all buttons (background shift, scale, or translate)
- [ ] Active/press feedback on buttons : `scale(0.98)` or `translateY(1px)`
- [ ] All interactive elements have transitions (200-300ms)
- [ ] Visible focus ring : keyboard navigation accessible
- [ ] Loading states : skeleton loaders matching layout shape, not circular spinners
- [ ] Empty states : composed "getting started" view, not blank screen
- [ ] Error states : clear inline error messages, no `window.alert()`
- [ ] No dead links (`href="#"` buttons either link somewhere or are visually disabled)
- [ ] Active nav link styled differently from inactive
- [ ] Anchor clicks use `scroll-behavior: smooth`
- [ ] Animations use `transform` and `opacity` only : not `top`, `left`, `width`, `height`

---

## Content

- [ ] No generic names : no "John Doe", "Jane Smith", "Sarah Chan"
- [ ] No fake round numbers : use `47.2%` not `50%`, `$99.00` not `$100`
- [ ] No placeholder brand names : no "Acme", "Nexus", "SmartFlow", "Flowbit"
- [ ] No AI copywriting clichés : no "Elevate", "Seamless", "Unleash", "Next-Gen", "Game-changer", "Delve"
- [ ] No exclamation marks in success messages
- [ ] No "Oops!" error messages : be direct: "Connection failed. Please try again."
- [ ] Active voice throughout : "We couldn't save" not "Mistakes were made"
- [ ] Blog post dates randomized to appear real
- [ ] No duplicate avatars for different users
- [ ] No Lorem Ipsum : real draft copy only
- [ ] No Title Case On Every Header : use sentence case

---

## Component Patterns

- [ ] Cards only where elevation communicates hierarchy : remove border/shadow/white-bg card look where unnecessary
- [ ] Not always one filled + one ghost button : add text links or tertiary styles
- [ ] "New" / "Beta" badges not defaulting to pill shape : try square badge or plain text
- [ ] FAQ not using accordion as default : consider side-by-side list or inline disclosure
- [ ] Testimonials not using 3-card carousel with dots : try masonry wall or single rotating quote
- [ ] Pricing table highlights recommended tier with color and emphasis, not just extra height
- [ ] Modals not used for simple actions : try inline editing or slide-over panels
- [ ] Avatars not exclusively circles : try squircles or rounded squares
- [ ] Footer not a 4-column link farm : simplified to main paths + legal

---

## Iconography

- [ ] Not exclusively Lucide or Feather : try Phosphor, Heroicons, or custom set
- [ ] No rocket = Launch, shield = Security clichés : use less obvious icons
- [ ] All icons use consistent stroke width
- [ ] Favicon present and branded
- [ ] No stock "diverse team" photos : use real photos, candid shots, or consistent illustration style

---

## Code Quality

- [ ] Semantic HTML used : `<nav>`, `<main>`, `<article>`, `<aside>`, `<section>` not div soup
- [ ] All styling in CSS system : no inline styles mixed with classes
- [ ] No hardcoded pixel widths : use relative units (`%`, `rem`, `em`, `max-width`)
- [ ] All meaningful images have descriptive `alt` text : not `alt=""` or `alt="image"`
- [ ] No arbitrary z-index values (`z-50`, `z-[9999]`) : use a clean z-index scale
- [ ] No commented-out dead code
- [ ] All imports verified against `package.json`
- [ ] Meta tags present: `<title>`, `description`, `og:image`, social sharing

---

## Strategic Omissions (What AI Typically Forgets)

- [ ] Legal links in footer : privacy policy + terms of service
- [ ] "Back" navigation present : no dead ends in user flows
- [ ] Custom 404 page : branded, helpful
- [ ] Form validation : client-side for emails, required fields, format checks
- [ ] Skip-to-content link : hidden, for keyboard users
- [ ] Cookie consent if required by jurisdiction

---

## Anti-AI-Slop Final Check

- [ ] No purple/blue AI gradient aesthetic
- [ ] No floating orbs or glassmorphism without purpose
- [ ] No 3-column equal card grid
- [ ] No rainbow mesh gradient
- [ ] No stock-photo clichés for the specific industry
- [ ] No generic dashboard UI panels as decoration
- [ ] No gradient text on large headers
- [ ] No oversaturated accent colors
- [ ] No infinite logo marquee of 6 identical blobs
- [ ] No fake KPI stat columns (99% satisfaction, $10 saved, infinity scale) unless explicitly requested
- [ ] Spacing between sections even and controlled : not one cramped section next to one spacious one
- [ ] Design breathes : not overfilled, not visually exhausting

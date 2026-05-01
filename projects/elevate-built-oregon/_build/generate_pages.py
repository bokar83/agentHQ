"""
Page generator for the Elevate site - v2 (Industrial Editorial)
Emits all sub-pages with shared header/footer/meta.
Run from project root:  python _build/generate_pages.py
"""
import os

OUT = os.path.join(os.path.dirname(__file__), '..', 'site')

SHELL = """<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1.0">
<title>{title}</title>
<meta name="description" content="{description}">
<link rel="canonical" href="https://elevatebuiltoregon.com{canonical}">
<meta property="og:type" content="website">
<meta property="og:title" content="{og_title}">
<meta property="og:description" content="{description}">
<meta property="og:url" content="https://elevatebuiltoregon.com{canonical}">
<meta property="og:image" content="https://elevatebuiltoregon.com/assets/og-image.svg">
<meta name="twitter:card" content="summary_large_image">
<meta name="theme-color" content="#0A0E14">
<link rel="icon" href="/assets/favicon.svg" type="image/svg+xml">
<link rel="preconnect" href="https://fonts.googleapis.com">
<link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
<link rel="preconnect" href="https://cdn.jsdelivr.net" crossorigin>
<link rel="stylesheet" href="/css/elevate.css">
{schema}
</head>
<body>

<header class="site-header">
  <a href="/" class="brand"><span class="brand-mark">E</span><span class="brand-name">Elev<em>a</em>te</span></a>
  <nav class="nav">
    <ul class="nav-links">
      <li><a href="/services/">Services</a></li>
      <li><a href="/portfolio/">Work</a></li>
      <li><a href="/service-areas/">Areas</a></li>
      <li><a href="/about/">Rod</a></li>
    </ul>
    <a href="/get-a-quote/" class="nav-cta">See if we fit <span class="arr">→</span></a>
    <button class="nav-toggle" aria-label="Open menu" aria-expanded="false"><span></span><span></span><span></span></button>
  </nav>
</header>

{body}

<footer class="site-footer">
  <div class="container">
    <div class="footer-grid">
      <div class="footer-brand">
        <a href="/" class="brand"><span class="brand-mark">E</span><span class="brand-name">Elev<em>a</em>te</span></a>
        <p class="footer-tag">Roof to ADU to custom home, one builder.</p>
        <p class="mono" style="margin-top:1.75rem;color:var(--bone);opacity:0.55;font-size:0.74rem">CCB# 257092 · Licensed · Bonded · Insured</p>
      </div>
      <div class="footer-col"><h4>Services</h4><ul>
        <li><a href="/services/roofing/">Roofing</a></li>
        <li><a href="/services/remodels-adus/">Remodels &amp; ADUs</a></li>
        <li><a href="/services/new-homes/">New homes</a></li>
        <li><a href="/services/custom/">Other cool stuff</a></li>
      </ul></div>
      <div class="footer-col"><h4>Areas</h4><ul>
        <li><a href="/service-areas/medford/">Medford</a></li>
        <li><a href="/service-areas/ashland/">Ashland</a></li>
        <li><a href="/service-areas/grants-pass/">Grants Pass</a></li>
        <li><a href="/service-areas/central-point/">Central Point</a></li>
        <li><a href="/service-areas/jacksonville/">Jacksonville</a></li>
        <li><a href="/service-areas/klamath-falls/">Klamath Falls</a></li>
      </ul></div>
      <div class="footer-col"><h4>Talk to Rod</h4><ul>
        <li><a href="tel:+14584883710">458-488-3710</a></li>
        <li><a href="mailto:rod@elevatebuiltoregon.com">rod@elevatebuiltoregon.com</a></li>
        <li><a href="/get-a-quote/">Book 15 min</a></li>
      </ul></div>
    </div>
    <div class="footer-bottom">
      <div>© <span data-year>2026</span> Elevate Roofing &amp; Construction LLC · Medford, OR</div>
      <div>Built with care · <a href="/contact/" style="color:var(--signal)">Get in touch</a></div>
    </div>
  </div>
</footer>

<div class="m-cta">
  <a href="tel:+14584883710" class="call">Call Rod</a>
  <a href="/get-a-quote/" class="book">Book →</a>
</div>

<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/gsap.min.js" defer></script>
<script src="https://cdnjs.cloudflare.com/ajax/libs/gsap/3.12.5/ScrollTrigger.min.js" defer></script>
<script src="/js/elevate.js" defer></script>
</body>
</html>
"""

def write(path, title, description, canonical, body, schema='', og_title=None):
    full = os.path.join(OUT, path.lstrip('/'), 'index.html')
    os.makedirs(os.path.dirname(full), exist_ok=True)
    html = SHELL.format(title=title, description=description, canonical=canonical,
                        og_title=og_title or title, schema=schema, body=body)
    with open(full, 'w', encoding='utf-8', newline='\n') as f:
        f.write(html)
    print(f'  wrote {path}')


# ============== ABOUT ==============
ABOUT_BODY = """
<section class="page-hero">
  <div class="container">
    <div class="eyebrow">About the founder</div>
    <h1>Same name<br>on the <em>door.</em></h1>
    <p class="lede long">Rod started Elevate to do construction one way: same crew, same standards, the same person picking up the phone.</p>
  </div>
</section>

<section class="founder">
  <div class="container">
    <div class="founder-grid">
      <div class="founder-portrait" aria-label="Portrait of Rod, founder of Elevate Roofing &amp; Construction">
        <span class="badge">Rod · Founder · Medford OR</span>
      </div>
      <div class="founder-text">
        <div class="eyebrow">From the founder</div>
        <blockquote>If your roof or remodel<br>isn't right, <em>I personally<br>make it right.</em></blockquote>
        <div class="founder-sig">Rod</div>
        <div class="small">Founder · Elevate Roofing &amp; Construction · CCB# 257092</div>
      </div>
    </div>
  </div>
</section>

<section class="paper">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 2fr;gap:clamp(2rem,5vw,6rem);align-items:start">
      <div>
        <div class="eyebrow muted">The story</div>
        <h2 style="margin-top:1rem"><em>Twenty years</em><br>of jobs that<br>add up to<br>this one.</h2>
      </div>
      <div class="prose dark-on-light">
        <p>I've spent the last two decades on jobsites across Oregon - multi-million-dollar commercial projects where one missed flashing detail meant a six-figure callback, and one-off residential builds where the homeowner watched every nail go in.</p>
        <p>What I learned is that most projects don't fall apart in the work. They fall apart in the handoffs. The roofer points to the framer. The framer points to the GC. The GC says it's not their scope. The homeowner stands in the middle, paying for the gap.</p>
        <p>I started Elevate to take the handoffs out. Same crew on your roof, your remodel, your ADU, and your new build. One CCB. One warranty. One phone number that rings to me.</p>

        <h3>What we believe</h3>
        <ul>
          <li><strong>Show up when we say we will.</strong> The whole industry runs on weasel-words about timelines. We don't.</li>
          <li><strong>The crew on bid day is the crew on build day.</strong> No bait-and-switch from senior estimator to junior subcontractor.</li>
          <li><strong>Detail is the job.</strong> Drip edge, ice &amp; water, ventilation math, fastener pattern - the parts you don't see are the parts that fail first.</li>
          <li><strong>If it's wrong, we make it right.</strong> Personally. Not a 30-day arbitration form.</li>
        </ul>

        <h3>Credentials</h3>
        <p><strong>Oregon CCB# 257092</strong> · Licensed, bonded &amp; insured · 20+ years across commercial and residential · Five-star reviewed across all named clients to date.</p>
        <p class="callout"><em>Manufacturer certifications (GAF, Owens Corning, etc.) - in process. We'll publish them as they land.</em></p>
      </div>
    </div>
    <div style="text-align:center;margin-top:5rem">
      <a href="/get-a-quote/" class="btn primary">See if we fit <span class="arr">→</span></a>
    </div>
  </div>
</section>
"""

# ============== SERVICE PAGES ==============
def service_body(slug, eyebrow, h1, h1_em, lede, sections, related):
    related_html = ''.join(
        f'<a href="{href}" class="svc x4"><div class="svc-num">0{n} / {label}</div><h3>{label.split()[0]}<br><em>→</em></h3><p>{desc}</p><span class="svc-arrow">↗</span></a>'
        for n, (label, href, desc) in enumerate(related, start=1)
    )
    return f"""
<section class="page-hero">
  <div class="container">
    <div class="eyebrow">{eyebrow}</div>
    <h1>{h1}<br><em>{h1_em}</em></h1>
    <p class="lede long">{lede}</p>
    <div style="margin-top:2.5rem;display:flex;gap:1rem;flex-wrap:wrap">
      <a href="/get-a-quote/" class="btn primary">See if we fit <span class="arr">→</span></a>
      <a href="tel:+14584883710" class="btn ghost">458 · 488 · 3710</a>
    </div>
  </div>
</section>

<section class="paper">
  <div class="container">
    <div class="prose dark-on-light" style="margin-inline:auto">{sections}</div>
  </div>
</section>

<section class="dark" style="background:var(--ink)">
  <div class="container">
    <div class="split-head">
      <div>
        <div class="eyebrow">Other things we build</div>
        <h2 style="margin-top:1rem">The whole<br><em>stack.</em></h2>
      </div>
    </div>
    <div class="services-mosaic">{related_html}</div>
  </div>
</section>

<section class="cta-final">
  <div class="container">
    <h2 class="display">Got a project<br>on the <em>horizon?</em></h2>
    <p class="lede long">15 minutes with Rod. No pitch deck.</p>
    <div class="hero-cta">
      <a href="/get-a-quote/" class="btn primary">Book a 15-min call <span class="arr">→</span></a>
    </div>
  </div>
</section>
"""

SERVICES = [
    {
        'slug': 'roofing',
        'title': 'Roofing in Southern Oregon - Residential & Commercial | Elevate',
        'description': 'Residential and commercial roofing across Medford, Ashland, Grants Pass. New, re-roof, and repair. Asphalt, metal, tile, slate. CCB# 257092.',
        'eyebrow': '01 / Roofing',
        'h1': 'Roofing,',
        'h1_em': 'done right.',
        'lede': 'New, re-roof, and repair. Residential and commercial. Same crew, same standards, the same name signing the work.',
        'sections': '''
<h2>What we install</h2>
<ul>
  <li><strong>Asphalt shingle</strong> - the workhorse. 30-50 year lifespans when installed with proper ice &amp; water shield, ventilation math, and fastener pattern. Most common re-roof in the Rogue Valley.</li>
  <li><strong>Standing-seam metal</strong> - 50-year+ life, wildfire-resistant, low maintenance. The right call for hillside Ashland, exposed Medford ridges, and any Klamath Falls property where snow load matters.</li>
  <li><strong>Tile (concrete &amp; clay)</strong> - premium aesthetic, 75+ year life. Heavier - we verify framing capacity before quoting.</li>
  <li><strong>Slate</strong> - for the right property. Century-plus life. Specialty work; we walk the project before committing.</li>
  <li><strong>Flat / low-slope (TPO, EPDM, modified bitumen)</strong> - commercial buildings, ADUs, modern residential additions.</li>
</ul>

<h2>Repair vs. re-roof, how we decide</h2>
<p>Most "I have a leak" calls are repairable. We won't sell you a re-roof you don't need. The decision usually comes down to:</p>
<ul>
  <li><strong>Age:</strong> if your roof is &lt; 70% through its rated life and the leak is local, repair is the right call.</li>
  <li><strong>Damage pattern:</strong> single-source leak (vent boot, valley, flashing) → repair. Widespread granule loss, multiple leaks, or daylight in the attic → re-roof.</li>
  <li><strong>Insurance:</strong> hail, wind, or wildfire damage often qualifies for full replacement under your homeowner's policy. We help you document it correctly.</li>
</ul>

<h2>What you get with us</h2>
<ul>
  <li>A walked-through scope with photos, not a one-line "Re-roof: $X" estimate.</li>
  <li>Manufacturer-spec installation (we install to the warranty, not to "good enough").</li>
  <li>Cleanup that means cleanup, magnetic sweep for nails, tarps under work zones, debris hauled day-of.</li>
  <li>One phone number for the warranty period. Rod picks up.</li>
</ul>

<h2>Typical Medford 2026 ranges</h2>
<p class="callout">
Roof repair, $450 - $2,800<br>
Asphalt re-roof (avg 2,200 sqft home), $9,500 - $22,000<br>
Standing-seam metal, $18,000 - $42,000<br>
Tile / slate, starts around $35,000<br>
Commercial flat roof, priced by the square, call for walk-through</p>
<p class="muted" style="font-size:0.92rem">Ranges are typical. Real number comes from walking your roof.</p>
''',
        'related': [
            ('Remodels & ADUs', '/services/remodels-adus/', 'Bring your plans or design + build with us.'),
            ('New Homes', '/services/new-homes/', 'Design-build custom homes across Southern Oregon.'),
            ('Other Cool Stuff', '/services/custom/', 'The unusual jobs nobody else will quote.'),
        ],
    },
    {
        'slug': 'remodels-adus',
        'title': 'Remodels & ADU Builder - Medford & Southern Oregon | Elevate',
        'description': 'Whole-home remodels, kitchens, baths, and accessory dwelling units (ADUs) across Medford, Ashland, Grants Pass. Design + build or bring your own plans. CCB# 257092.',
        'eyebrow': '02 / Remodels & ADUs',
        'h1': 'Remodels',
        'h1_em': '& ADUs.',
        'lede': "Bring your own plans and ideas, or design + build with us from scratch. Whole-home, kitchens, baths, and Oregon-compliant accessory dwelling units.",
        'sections': '''
<h2>What we remodel</h2>
<ul>
  <li><strong>Whole-home remodels</strong> - taking a 1970s ranch to 2026. Layout changes, structural work, kitchens, baths, finishes, and the small thousand details that make a remodel feel intentional.</li>
  <li><strong>Kitchens</strong> - full gut-to-finish, layout changes, structural openings, custom cabinetry, range hood vent runs, the works.</li>
  <li><strong>Bathrooms</strong> - primary suite expansions, tile work, walk-in showers, properly-vented exhaust, slab leaks, the unsexy parts done right.</li>
  <li><strong>Additions</strong> - bumping out a room, second-story adds, garage conversions, three-season rooms.</li>
</ul>

<h2>ADUs, what Oregon's 2026 rules actually allow</h2>
<p>Oregon House Bill 2001 + 3151 made ADUs much easier across the state. In Medford, Ashland, and most Jackson County jurisdictions you can now build:</p>
<ul>
  <li><strong>Detached ADU</strong> - up to 900 sqft (some jurisdictions higher), separate entrance, full kitchen + bath. Common backyard build.</li>
  <li><strong>Attached ADU</strong> - bolted onto the main house, shared wall, separate entrance.</li>
  <li><strong>Internal / conversion ADU</strong> - basement, attic, or garage conversion. Often the fastest path to permit.</li>
</ul>
<p>We handle the design, the permit, and the build. If you want a financing or zoning conversation before you commit, we'll walk you through it on the call.</p>

<h2>Two ways we work</h2>
<ul>
  <li><strong>Bring your plans.</strong> You've already worked with an architect. We bid the build.</li>
  <li><strong>Design + build.</strong> You bring the vision and the lot. We bring the architect, the engineer, and the crew. One contract, one timeline, one accountable name.</li>
</ul>

<h2>Typical Medford 2026 ranges</h2>
<p class="callout">
Bath remodel, $28,000 - $65,000<br>
Kitchen remodel, $48,000 - $135,000<br>
Whole-home remodel, $185,000 - $480,000<br>
Detached ADU (turnkey), $185,000 - $420,000<br>
ADU conversion (basement / garage), $95,000 - $245,000</p>
<p class="muted" style="font-size:0.92rem">Wide ranges because remodels vary wildly with finish level and structural work needed. Real number comes from walking the property.</p>
''',
        'related': [
            ('Roofing', '/services/roofing/', 'Residential, commercial, repair, re-roof.'),
            ('New Homes', '/services/new-homes/', 'Custom homes from raw lot to keys.'),
            ('Other Cool Stuff', '/services/custom/', 'The unusual jobs.'),
        ],
    },
    {
        'slug': 'new-homes',
        'title': 'Custom Home Builder - Medford & Jackson County | Elevate',
        'description': 'Custom new home construction across Medford, Ashland, Jacksonville. Bring finished plans or design + build with us. We partner with engineers and architects. CCB# 257092.',
        'eyebrow': '03 / New Homes',
        'h1': 'New homes,',
        'h1_em': 'built right.',
        'lede': 'Bring us your finished plans or your big ideas. We partner with engineers and architects for a streamlined design-build experience, and the same crew who builds your roof builds your house.',
        'sections': '''
<h2>How a new build with us works</h2>
<ol>
  <li><strong>Walk the lot.</strong> Slope, soils, sun, view corridors, septic vs. sewer, HOA rules. Most lot surprises are findable in 30 minutes if someone who's done it before is looking.</li>
  <li><strong>Plans &amp; design.</strong> Bring an architect or use ours. We pull in a structural engineer for any complex framing or hillside work, a civil engineer if grading is involved.</li>
  <li><strong>Permit + budget.</strong> We submit, we manage feedback, we tell you what each line item really costs in 2026 Southern Oregon.</li>
  <li><strong>Build.</strong> Same crew you've been talking to, same project manager start to finish. We don't disappear into "the office" once the contract signs.</li>
  <li><strong>Walkthrough &amp; punch.</strong> We show up, you point, we fix. Then we show up again 30 days later for the post-move-in walk.</li>
</ol>

<h2>Where we build</h2>
<p>Across Jackson and Josephine County primarily, Medford, Ashland, Jacksonville, Grants Pass, Central Point, Eagle Point. Klamath County for the right project. We don't take work outside the region; we'd rather do five Southern Oregon homes a year well than ten anywhere poorly.</p>

<h2>Typical Medford 2026 ranges</h2>
<p class="callout">
Standard build (1,800 - 2,800 sqft), $485,000 - $920,000<br>
Custom premium build (3,000+ sqft, high finish), $920,000 - $1.4M<br>
Hillside / view lot premium, + 12-25%<br>
Net-zero / passive features, + 8-18%</p>
<p class="muted" style="font-size:0.92rem">Excludes lot, site work, septic/well where applicable. We give you the real number after we walk the lot.</p>

<h2>What we won't do</h2>
<p>We won't bid a build we don't think we can do well. If your timeline, budget, or design is fundamentally mismatched, we'll tell you on the call rather than chase the deposit.</p>
''',
        'related': [
            ('Roofing', '/services/roofing/', 'The roof on your new build, by us.'),
            ('Remodels & ADUs', '/services/remodels-adus/', 'Or maybe a remodel makes more sense.'),
            ('Other Cool Stuff', '/services/custom/', 'Unusual builds.'),
        ],
    },
    {
        'slug': 'custom',
        'title': 'Other Cool Stuff - Custom Construction in Southern Oregon | Elevate',
        'description': 'The unusual jobs. Hillside builds, accessory structures, barn conversions, restoration work. We have the expertise and the experience. CCB# 257092.',
        'eyebrow': '04 / Other Cool Stuff',
        'h1': 'Other cool',
        'h1_em': 'stuff.',
        'lede': 'Unique ideas require expertise and experience. Fortunately, we have both.',
        'sections': '''
<h2>What "custom" usually means</h2>
<p>Most of our custom work falls into one of these buckets:</p>
<ul>
  <li><strong>Hillside &amp; difficult-site builds</strong> - slope, geotech, retaining walls, complex foundations.</li>
  <li><strong>Accessory structures</strong> - barns, shops, detached studios, covered outdoor kitchens, pool houses.</li>
  <li><strong>Restoration &amp; preservation</strong> - older Medford and Jacksonville properties where original character matters and modern code applies.</li>
  <li><strong>Commercial &amp; mixed-use</strong> - small commercial builds, light tenant improvements, office-to-residential conversions.</li>
  <li><strong>The thing nobody else will quote.</strong> Yes, we'll look at it.</li>
</ul>

<h2>How we decide if we're the right fit</h2>
<p>We bring 20+ years across multi-million-dollar commercial sites and one-off residential builds. The variety helps - we've seen most of the failure modes by now. But we're not the right call for every job. The 15-minute conversation tells us, and you, fast.</p>

<h2>Typical custom project ranges</h2>
<p class="callout">
Detached shop / barn (1,200 - 2,400 sqft), $145,000 - $385,000<br>
Hillside premium on a standard build, + 15-30%<br>
Restoration / preservation, priced per scope (we walk the property first)<br>
Commercial small build, priced per scope</p>
''',
        'related': [
            ('Roofing', '/services/roofing/', 'The roof on it, by us.'),
            ('Remodels & ADUs', '/services/remodels-adus/', "Maybe it's really a remodel?"),
            ('New Homes', '/services/new-homes/', 'Or a new home from scratch.'),
        ],
    },
]

# ============== CITY PAGES ==============
CITIES = [
    {'slug': 'medford', 'name': 'Medford', 'pop': '~85,000', 'note': 'Our home base. Most of our crew lives within 20 minutes.'},
    {'slug': 'ashland', 'name': 'Ashland', 'pop': '~21,000', 'note': 'Hillside lots, view corridors, premium re-roofs. We know the city plan reviewers by name.'},
    {'slug': 'grants-pass', 'name': 'Grants Pass', 'pop': '~40,000', 'note': 'Josephine County primary. Driveway distances are long; our quotes account for it.'},
    {'slug': 'central-point', 'name': 'Central Point', 'pop': '~19,000', 'note': 'Newer construction, growing neighborhoods. Lots of asphalt re-roofs entering 20-year window.'},
    {'slug': 'jacksonville', 'name': 'Jacksonville', 'pop': '~3,000', 'note': "Historic district rules. We know what passes review and what doesn't."},
    {'slug': 'klamath-falls', 'name': 'Klamath Falls', 'pop': '~22,000', 'note': 'Snow load matters. Standing-seam metal is the right call for most properties.'},
]

def city_body(city):
    others = ' '.join(f'<a href="/service-areas/{c["slug"]}/" class="area-pill">{c["name"]}</a>' for c in CITIES if c['slug'] != city['slug'])
    return f"""
<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Service area · {city['name']}, OR</div>
    <h1>Roofing &amp;<br>building in <em>{city['name']}.</em></h1>
    <p class="lede long">{city['note']}</p>
    <div style="margin-top:2.5rem;display:flex;gap:1rem;flex-wrap:wrap">
      <a href="/get-a-quote/" class="btn primary">Get a {city['name']} quote <span class="arr">→</span></a>
      <a href="tel:+14584883710" class="btn ghost">458 · 488 · 3710</a>
    </div>
  </div>
</section>

<section class="paper">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 2fr;gap:clamp(2rem,5vw,6rem);align-items:start">
      <div>
        <div class="eyebrow muted">{city['name']} · {city['pop']}</div>
        <h2 style="margin-top:1rem">What we<br>do in<br><em>{city['name']}.</em></h2>
      </div>
      <div class="prose dark-on-light">
        <p>{city['name']} (population {city['pop']}) is part of our regular service route. Most call-outs are residential roofing, re-roofs, and remodels - but we run new builds and ADUs here too.</p>

        <ul>
          <li><a href="/services/roofing/">Roofing</a> - repair, re-roof, and new installation</li>
          <li><a href="/services/remodels-adus/">Remodels &amp; ADUs</a> - kitchens, baths, whole-home, accessory dwelling units</li>
          <li><a href="/services/new-homes/">New Homes</a> - custom design-build</li>
          <li><a href="/services/custom/">Other cool stuff</a> - the unusual jobs</li>
        </ul>

        <h3>What sets us apart in {city['name']}</h3>
        <ul>
          <li><strong>One builder for the whole job.</strong> Roof, remodel, ADU, new build - same crew, one CCB, one phone number.</li>
          <li><strong>20+ years across Southern Oregon.</strong> We've seen what fails on {city['name']} properties and we install for it.</li>
          <li><strong>Founder-led.</strong> Rod walks every project. CCB# 257092.</li>
        </ul>

        <h3>Local context we know</h3>
        <p>{city['note']} If your project has anything specific to {city['name']} - historic district, hillside, snow load, view corridor - bring it up on the call. Chances are we've worked it before.</p>

        <h3>Other cities we serve</h3>
        <div class="areas-pills" style="margin-top:1rem">{others}</div>
      </div>
    </div>
  </div>
</section>

<section class="cta-final">
  <div class="container">
    <h2 class="display">{city['name']} project<br>on the <em>horizon?</em></h2>
    <p class="lede long">15 minutes with Rod. No pitch deck.</p>
    <div class="hero-cta">
      <a href="/get-a-quote/" class="btn primary">Book a 15-min call <span class="arr">→</span></a>
      <a href="tel:+14584883710" class="btn ghost">or call 458-488-3710</a>
    </div>
  </div>
</section>
"""

# ============== HUB PAGES ==============
SERVICES_HUB = """
<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Services</div>
    <h1>Four trades.<br>One <em>signature.</em></h1>
    <p class="lede long">Roof, remodel, ADU, new home. Same crew on every job. The same name signs the warranty.</p>
  </div>
</section>

<section class="dark" style="background:var(--ink)">
  <div class="container">
    <div class="services-mosaic">
      <a href="/services/roofing/" class="svc x6">
        <div class="svc-num">01 / Roofing</div>
        <h3>Roofing,<br><em>done right.</em></h3>
        <p>Residential and commercial. New, re-roof, repair. Asphalt, metal, tile, slate, low-slope.</p>
        <span class="svc-arrow">↗</span>
      </a>
      <a href="/services/remodels-adus/" class="svc x6">
        <div class="svc-num">02 / Remodels & ADUs</div>
        <h3>Remodels<br>&amp; <em>ADUs.</em></h3>
        <p>Whole-home, kitchens, baths, additions, and Oregon-compliant accessory dwelling units.</p>
        <span class="svc-arrow">↗</span>
      </a>
      <a href="/services/new-homes/" class="svc x4">
        <div class="svc-num">03 / New Homes</div>
        <h3>New<br><em>homes.</em></h3>
        <p>Custom design-build across Jackson and Josephine County. Bring plans or design with us.</p>
        <span class="svc-arrow">↗</span>
      </a>
      <a href="/services/custom/" class="svc x8">
        <div class="svc-num">04 / Other Cool Stuff</div>
        <h3>Other <em>cool</em> stuff.</h3>
        <p>Hillside builds, accessory structures, restoration, commercial. The unusual jobs nobody else will quote.</p>
        <span class="svc-arrow">↗</span>
      </a>
    </div>
  </div>
</section>

<section class="cta-final">
  <div class="container">
    <h2 class="display">Got a project<br>on the <em>horizon?</em></h2>
    <p class="lede long">Tell us about it. 15 minutes with Rod.</p>
    <div class="hero-cta">
      <a href="/get-a-quote/" class="btn primary">Book a 15-min call <span class="arr">→</span></a>
    </div>
  </div>
</section>
"""

SERVICE_AREAS_HUB = f"""
<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Where we work</div>
    <h1>Built across<br><em>Southern Oregon.</em></h1>
    <p class="lede long">From Klamath Falls to Grants Pass, Ashland to Eagle Point. Six anchor cities, plus most of Jackson, Josephine &amp; Klamath County in between.</p>
  </div>
</section>

<section class="paper">
  <div class="container">
    <div class="areas-grid">
      <div>
        <div class="eyebrow muted">Six anchor cities</div>
        <h2 style="margin-top:1rem">Pick a<br><em>town.</em></h2>
        <p class="lede long" style="color:var(--steel);margin-top:1.5rem">Don't see your city? Most of the Rogue Valley and Klamath Basin is on the route, call Rod direct.</p>
      </div>
      <div class="areas-list-numbers">
        {''.join(f'<a href="/service-areas/{c["slug"]}/" class="area-row"><span class="num">0{i+1}</span><span class="name">{c["name"]}</span><span class="pop">{c["pop"]}</span></a>' for i, c in enumerate(CITIES))}
      </div>
    </div>
  </div>
</section>

<section class="cta-final">
  <div class="container">
    <h2 class="display">15 minutes<br>with <em>Rod.</em></h2>
    <p class="lede long">No pitch, no high-pressure visit.</p>
    <div class="hero-cta">
      <a href="/get-a-quote/" class="btn primary">Book a call <span class="arr">→</span></a>
    </div>
  </div>
</section>
"""

PORTFOLIO_BODY = """
<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Portfolio</div>
    <h1>The work,<br>on <em>display.</em></h1>
    <p class="lede long">Roofs that hold up. Remodels neighbors ask about. New builds where move-in ready means move-in ready.</p>
  </div>
</section>

<section class="portfolio">
  <div class="container">
    <div class="portfolio-grid">
      <a href="#" class="proj feature">
        <img src="/assets/media/project-2025-recent.jpg" alt="Recent Elevate residential project, Medford OR" loading="lazy">
        <div class="proj-meta">
          <div class="proj-info-l"><span class="num">2025 / 001</span><h3>Hillside re-roof, Medford</h3></div>
          <div class="proj-info-r">Asphalt re-roof<br>2,400 sqft</div>
        </div>
      </a>
      <a href="#" class="proj tall">
        <img src="/assets/media/project-2026-latest.jpg" alt="Recent Elevate project from January 2026" loading="lazy">
        <div class="proj-meta">
          <div class="proj-info-l"><span class="num">2026 / 002</span><h3>Custom build, Jacksonville</h3></div>
          <div class="proj-info-r">In progress</div>
        </div>
      </a>
      <a href="#" class="proj half">
        <img src="/assets/media/project-2017-build.jpg" alt="Elevate framing detail" loading="lazy">
        <div class="proj-meta">
          <div class="proj-info-l"><span class="num">Past / 003</span><h3>Commercial framing</h3></div>
          <div class="proj-info-r">Multi-million build</div>
        </div>
      </a>
      <a href="#" class="proj half">
        <img src="/assets/media/project-2016-roof.jpg" alt="Elevate roofing detail" loading="lazy">
        <div class="proj-meta">
          <div class="proj-info-l"><span class="num">Past / 004</span><h3>Residential roof, OR</h3></div>
          <div class="proj-info-r">Re-roof complete</div>
        </div>
      </a>
    </div>
    <p class="muted" style="margin-top:2.5rem;text-align:center;font-size:0.92rem;color:var(--steel-soft)"><em>More photos coming - Rod is shooting recent projects with a drone in May 2026. The four shown are real Elevate work.</em></p>
  </div>
</section>

<section class="cta-final">
  <div class="container">
    <h2 class="display">Want one of these<br>on <em>your</em> property?</h2>
    <div class="hero-cta">
      <a href="/get-a-quote/" class="btn primary">Book a 15-min call <span class="arr">→</span></a>
    </div>
  </div>
</section>
"""

QUOTE_BODY = """
<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Cost tool + booking</div>
    <h1>What does this<br><em>actually</em> cost?</h1>
    <p class="lede long">Pick your project type. Get a typical Medford 2026 range. Then book a 15-minute call with Rod if it makes sense.</p>
  </div>
</section>

<section class="paper">
  <div class="container">
    <div style="display:grid;grid-template-columns:1fr 1fr;gap:3rem" class="quote-grid">
      <div class="form light">
        <h3 style="margin-bottom:0.4rem;color:var(--ink)">Step 01 - pick your project</h3>
        <p class="muted" style="font-size:0.92rem;margin-bottom:0.5rem;color:var(--steel)">Range is typical. Real number comes from walking the property.</p>
        <label>Project type
          <select data-cost-select>
            <option value="">Choose a project...</option>
            <option value="roof-repair">Roof repair</option>
            <option value="roof-replace-asphalt">Asphalt re-roof</option>
            <option value="roof-replace-metal">Metal re-roof (standing seam)</option>
            <option value="remodel-bath">Bathroom remodel</option>
            <option value="remodel-kitchen">Kitchen remodel</option>
            <option value="adu">ADU (accessory dwelling unit)</option>
            <option value="new-home">New custom home</option>
            <option value="custom">Custom / something else</option>
          </select>
        </label>
        <div style="background:var(--bone-warm);padding:1.5rem;border-left:3px solid var(--signal);min-height:80px;display:flex;flex-direction:column;justify-content:center;gap:0.4rem">
          <div class="eyebrow muted">Typical Medford 2026 range</div>
          <div data-cost-result style="font-family:var(--serif);font-size:1.65rem;color:var(--ink);font-style:italic">- pick a project above -</div>
        </div>
      </div>

      <form class="form light" action="https://formspree.io/f/REPLACE_ME" method="POST">
        <h3 style="margin-bottom:0.4rem;color:var(--ink)">Step 02 - book the call</h3>
        <p class="muted" style="font-size:0.92rem;margin-bottom:0.5rem;color:var(--steel)">15 minutes with Rod. We'll talk through your project, your timeline, and whether we're the right builder. No pitch.</p>
        <div class="form-row">
          <label>First name<input type="text" name="first_name" required></label>
          <label>Phone<input type="tel" name="phone" required></label>
        </div>
        <label>Email<input type="email" name="email" required></label>
        <label>What's the project?<textarea name="message" placeholder="Tell us about the property, the timeline, and what you're trying to figure out."></textarea></label>
        <button type="submit" class="btn primary">Request the call <span class="arr">→</span></button>
        <p class="muted" style="font-size:0.78rem;color:var(--steel-soft)">By submitting, you agree to be contacted by Rod or someone on the Elevate team. We don't sell or share your info.</p>
      </form>
    </div>
  </div>
</section>

<section class="paper" style="border-top:1px solid var(--hair)">
  <div class="container">
    <div class="split-head">
      <div>
        <div class="eyebrow muted">How a project starts</div>
        <h2 style="margin-top:1rem;color:var(--ink)">How a project<br>starts with <em>us.</em></h2>
      </div>
    </div>
    <div class="steps">
      <div class="step"><div class="step-num">01 / Quick call</div><h3>Quick call</h3><p>15 minutes. We listen. We ask the questions a builder should ask. We tell you straight if we're the right fit.</p></div>
      <div class="step"><div class="step-num">02 / Walk the lot</div><h3>Walk the property</h3><p>If we're a fit, Rod walks the project on-site. Most lot or roof surprises are findable in 30 minutes.</p></div>
      <div class="step"><div class="step-num">03 / Real number</div><h3>Real number</h3><p>You get a written scope with photos and a real number, not a one-line "Roof: $X" estimate.</p></div>
      <div class="step"><div class="step-num">04 / Build</div><h3>Build</h3><p>Same crew you've been talking to. Same project manager start to finish. Show up when we say we will.</p></div>
    </div>
  </div>
</section>
"""

CONTACT_BODY = """
<section class="page-hero">
  <div class="container">
    <div class="eyebrow">Contact</div>
    <h1>Talk to <em>Rod.</em></h1>
    <p class="lede long">Three ways. Pick whichever feels right.</p>
  </div>
</section>

<section class="dark" style="background:var(--ink)">
  <div class="container">
    <div class="services-mosaic">
      <a href="tel:+14584883710" class="svc x4"><div class="svc-num">01 / Call</div><h3>458<br><em>·488·3710</em></h3><p>Direct to Rod.</p><span class="svc-arrow">↗</span></a>
      <a href="mailto:rod@elevatebuiltoregon.com" class="svc x4"><div class="svc-num">02 / Email</div><h3>Send a<br><em>note.</em></h3><p>rod@elevatebuiltoregon.com - we read everything.</p><span class="svc-arrow">↗</span></a>
      <a href="/get-a-quote/" class="svc x4"><div class="svc-num">03 / Book</div><h3>15 min<br><em>on calendar.</em></h3><p>No pitch deck. Open the form, pick a slot.</p><span class="svc-arrow">↗</span></a>
    </div>
  </div>
</section>

<section class="paper">
  <div class="container">
    <div class="prose dark-on-light" style="margin-inline:auto">
      <h2>The basics</h2>
      <ul>
        <li><strong>Phone:</strong> <a href="tel:+14584883710">458-488-3710</a></li>
        <li><strong>Email:</strong> <a href="mailto:rod@elevatebuiltoregon.com">rod@elevatebuiltoregon.com</a></li>
        <li><strong>Service area:</strong> Medford, Ashland, Grants Pass, Central Point, Jacksonville, Klamath Falls, and most of the Rogue Valley and Klamath Basin in between.</li>
        <li><strong>License:</strong> Oregon CCB# 257092 · Licensed, bonded, and insured</li>
        <li><strong>Hours:</strong> Mon-Fri 7am-6pm. Saturday by appointment. Storm calls answered evenings &amp; weekends.</li>
      </ul>
    </div>
  </div>
</section>
"""

NOT_FOUND_BODY = """
<section class="page-hero" style="min-height:80vh;display:flex;align-items:center">
  <div class="container">
    <div class="eyebrow">404</div>
    <h1>That page<br>isn't <em>built yet.</em></h1>
    <p class="lede long">The link's a dead end, but the door isn't.</p>
    <div style="margin-top:2.5rem;display:flex;gap:1rem;flex-wrap:wrap">
      <a href="/" class="btn primary">Back to home <span class="arr">→</span></a>
      <a href="/services/" class="btn ghost">See services</a>
      <a href="tel:+14584883710" class="btn ghost">Call Rod</a>
    </div>
  </div>
</section>
"""


# ============== EMIT ==============
print('Generating Elevate site v2 pages...')

write('/about/', 'About Rod & Elevate Roofing - 20+ Years Building in Southern Oregon | CCB# 257092',
      'Meet Rod, founder of Elevate Roofing & Construction. 20+ years across multi-million-dollar commercial sites and one-of-a-kind residential builds. CCB# 257092 · Medford, OR.',
      '/about/', ABOUT_BODY)

for s in SERVICES:
    body = service_body(s['slug'], s['eyebrow'], s['h1'], s['h1_em'], s['lede'], s['sections'], s['related'])
    write(f"/services/{s['slug']}/", s['title'], s['description'], f"/services/{s['slug']}/", body)

for c in CITIES:
    title = f"Roofing & Construction in {c['name']}, OR - Elevate | CCB# 257092"
    desc = f"Roofing, remodels, ADUs, and new homes in {c['name']}, Oregon. 20+ years. Same crew on every job. Founder-led. CCB# 257092."
    write(f"/service-areas/{c['slug']}/", title, desc, f"/service-areas/{c['slug']}/", city_body(c))

write('/services/', 'Services - Roofing, Remodels, ADUs, New Homes | Elevate Southern Oregon',
      'Roofing, remodels, ADUs, and custom homes across Medford and Southern Oregon. One builder, one CCB, one warranty. CCB# 257092.',
      '/services/', SERVICES_HUB)

write('/service-areas/', 'Service Areas - Medford, Ashland, Grants Pass & Southern Oregon | Elevate',
      'Elevate serves Medford, Ashland, Grants Pass, Central Point, Jacksonville, and Klamath Falls. Roofing, remodels, ADUs, and new homes across Southern Oregon.',
      '/service-areas/', SERVICE_AREAS_HUB)

write('/portfolio/', 'Portfolio - Recent Roofing & Construction Projects | Elevate Southern Oregon',
      'Recent roofs, remodels, ADUs, and new homes built by Elevate across Medford and Southern Oregon. CCB# 257092.',
      '/portfolio/', PORTFOLIO_BODY)

write('/get-a-quote/', 'Get a Quote - Cost Tool + Book a 15-Min Call with Rod | Elevate',
      'See typical Medford 2026 cost ranges for your project. Book a 15-minute call with Rod. No pitch deck, no high-pressure visit.',
      '/get-a-quote/', QUOTE_BODY)

write('/contact/', 'Contact - Talk to Rod | Elevate Roofing & Construction',
      'Three ways to reach Rod at Elevate Roofing & Construction. Call, email, or book a 15-minute call. CCB# 257092 · Medford, OR.',
      '/contact/', CONTACT_BODY)

write('/404/', 'Page not found - Elevate Roofing & Construction',
      "That page isn't built yet, but the door isn't closed. Find what you need or call Rod direct.",
      '/404/', NOT_FOUND_BODY)

print('Done.')

```html
<!DOCTYPE html>
<html lang="en">
<head>
 <meta charset="UTF-8" />
 <meta name="viewport" content="width=device-width, initial-scale=1.0" />
 <title>Tweet Comparison, leGriot Command Center</title>
 <link rel="preconnect" href="https://fonts.googleapis.com" />
 <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin />
 <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@600;700;800&family=Inter:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet" />
 <style>
 /* ─── CSS CUSTOM PROPERTIES ─────────────────────────────────────── */
 :root {
 --background-color: #071A2E;
 --primary-text-color: #FFFFFF;
 --accent-color: #FF7A00;
 --secondary-color: #00B7C2;
 --border-color: #DDE2EA;
 --card-surface: #0D2A45;
 --clay-warmth: #B47C57;
 --mist-bg: #F3F6F9;
 --carbon-body: #1E222A;
 --carbon-muted: #5A6272;
 --error-amber: #CC6600;

 --space-1: 8px;
 --space-2: 16px;
 --space-3: 24px;
 --space-4: 32px;
 --space-5: 40px;
 --space-6: 48px;
 --space-8: 64px;
 --space-10: 80px;
 --space-12: 96px;
 }

 /* ─── RESET ──────────────────────────────────────────────────────── */
 *, *::before, *::after { box-sizing: border-box; margin: 0; padding: 0; }
 html { scroll-behavior: smooth; }
 body {
 background-color: var(--background-color);
 color: var(--primary-text-color);
 font-family: 'Inter', -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif;
 font-size: 16px;
 font-weight: 400;
 line-height: 1.6;
 min-height: 100vh;
 }

 /* ─── NAV ────────────────────────────────────────────────────────── */
 .nav {
 position: sticky;
 top: 0;
 z-index: 100;
 background: var(--background-color);
 height: 72px;
 border-bottom: 1px solid rgba(0,183,194,0.12);
 display: flex;
 align-items: center;
 padding: 0 var(--space-4);
 }
 .nav-inner {
 max-width: 1200px;
 width: 100%;
 margin: 0 auto;
 display: flex;
 align-items: center;
 justify-content: space-between;
 }
 .nav-logo {
 font-family: 'Plus Jakarta Sans', sans-serif;
 font-size: 18px;
 font-weight: 700;
 color: var(--primary-text-color);
 letter-spacing: -0.015em;
 display: flex;
 align-items: center;
 gap: var(--space-1);
 }
 .nav-logo span { color: var(--secondary-color); }
 .nav-badge {
 font-family: 'Inter', sans-serif;
 font-size: 11px;
 font-weight: 500;
 letter-spacing: 0.1em;
 text-transform: uppercase;
 color: var(--carbon-muted);
 background: rgba(255,255,255,0.04);
 border: 1px solid rgba(255,255,255,0.08);
 border-radius: 4px;
 padding: 4px 10px;
 }

 /* ─── PAGE HEADER ────────────────────────────────────────────────── */
 .page-header {
 max-width: 1200px;
 margin: 0 auto;
 padding: var(--space-10) var(--space-4) var(--space-8);
 }
 .eyebrow {
 font-family: 'Inter', sans-serif;
 font-size: 12px;
 font-weight: 500;
 letter-spacing: 0.1em;
 text-transform: uppercase;
 color: var(--secondary-color);
 margin-bottom: var(--space-2);
 }
 .page-title {
 font-family: 'Plus Jakarta Sans', sans-serif;
 font-size: 40px;
 font-weight: 800;
 letter-spacing: -0.03em;
 color: var(--primary-text-color);
 line-height: 1.15;
 margin-bottom: var(--space-2);
 }
 .page-subtitle {
 font-family: 'Inter', sans-serif;
 font-size: 16px;
 font-weight: 400;
 color: rgba(255,255,255,0.55);
 max-width: 560px;
 }

 /* ─── COMPARISON PANEL ───────────────────────────────────────────── */
 .comparison-panel {
 max-width: 960px;
 margin: 0 auto;
 padding: 0 var(--space-4) var(--space-10);
 }
 .comparison-grid {
 display: grid;
 grid-template-columns: 1fr 1fr;
 gap: var(--space-3);
 align-items: start;
 }

 /* ─── TWEET CARDS ────────────────────────────────────────────────── */
 .tweet-card {
 background: var(--card-surface);
 border: 1px solid rgba(0,183,194,0.15);
 border-radius: 8px;
 padding: var(--space-4);
 transition: all 200ms ease-out;
 position: relative;
 }
 .tweet-card.winner {
 border: 2px solid var(--secondary-color);
 background: rgba(0,183,194,0.06);
 box-shadow: 0 8px 24px rgba(0,183,194,0.12);
 }
 .tweet-card.weaker {
 border: 1px solid rgba(204,102,0,0.2);
 opacity: 0.75;
 }

 .card-header {
 display: flex;
 align-items: center;
 justify-content: space-between;
 margin-bottom: var(--space-3);
 }
 .card-label {
 font-family: 'Inter', sans-serif;
 font-size: 12px;
 font-weight: 500;
 letter-spacing: 0.1em;
 text-transform: uppercase;
 }
 .card-label.option-a { color: var(--error-amber); }
 .card-label.option-b { color: var(--secondary-color); }

 .winner-badge {
 display: inline-flex;
 align-items: center;
 gap: 6px;
 font-family: 'Inter', sans-serif;
 font-size: 11px;
 font-weight: 600;
 letter-spacing: 0.08em;
 text-transform: uppercase;
 color: var(--secondary-color);
 background: rgba(0,183,194,0.12);
 border: 1px solid rgba(0,183,194,0.3);
 border-radius: 4px;
 padding: 4px 10px;
 }
 .winner-badge::before { content: '✦'; font-size: 9px; }

 .card-title {
 font-family: 'Plus Jakarta Sans', sans-serif;
 font-size: 18px;
 font-weight: 600;
 color: var(--primary-text-color);
 margin-bottom: var(--space-3);
 letter-spacing: 0;
 }

 .tweet-text {
 font-family: 'Inter', sans-serif;
 font-size: 16px;
 font-weight: 400;
 color: rgba(255,255,255,0.88);
 line-height: 1.7;
 white-space: pre-line;
 background: rgba(0,0,0,0.15);
 border-radius: 6px;
 padding: var(--space-3);
 margin-bottom: var(--space-3);
 border-left: 3px solid rgba(255,255,255,0.08);
 }
 .tweet-card.winner .tweet-text { border-left-color: var(--secondary-color); }
 .tweet-card.weaker .tweet-text { border-left-color: rgba(204,102,0,0.4); }

 .score-chips {
 display: flex;
 flex-wrap: wrap;
 gap: var(--space-1);
 margin-bottom: var(--space-3);
 }
 .chip {
 font-family: 'JetBrains Mono', 'Courier New', monospace;
 font-size: 13px;
 font-weight: 400;
 background: rgba(0,183,194,0.12);
 color: var(--secondary-color);
 border: 1px solid rgba(0,183,194,0.25);
 border-radius: 4px;
 padding: 4px 10px;
 display: inline-block;
 }
 .chip.amber {
 background: rgba(204,102,0,0.1);
 color: var(--error-amber);
 border-color: rgba(204,102,0,0.25);
 }

 .weakness-note {
 font-family: 'Inter', sans-serif;
 font-size: 14px;
 font-weight: 400;
 color: rgba(255,255,255,0.5);
 line-height: 1.6;
 padding: var(--space-2) var(--space-3);
 background: rgba(204,102,0,0.06);
 border-radius: 4px;
 border-left: 3px solid rgba(204,102,0,0.3);
 }
 .weakness-note strong { color: var(--error-amber); font-weight: 500; }

 /* CLAY VERDICT CALLOUT, mandatory */
 .verdict-callout {
 border-left: 4px solid var(--clay-warmth);
 background: rgba(180,124,87,0.08);
 padding: var(--space-2) var(--space-3);
 border-radius: 0 4px 4px 0;
 margin-top: var(--space-3);
 }
 .verdict-callout-label {
 font-family: 'Inter', sans-serif;
 font-size: 11px;
 font-weight: 500;
 letter-spacing: 0.1em;
 text-transform: uppercase;
 color: var(--clay-warmth);
 margin-bottom: 6px;
 }
 .verdict-callout-text {
 font-family: 'Inter', sans-serif;
 font-size: 14px;
 font-weight: 400;
 color: rgba(255,255,255,0.75);
 line-height: 1.6;
 }
 .verdict-callout-text strong { color: var(--primary-text-color); font-weight: 600; }

 /* ─── RECOMMENDATION ─────────────────────────────────────────────── */
 .recommendation-section {
 max-width: 960px;
 margin: 0 auto;
 padding: 0 var(--space-4) var(--space-8);
 }
 .section-divider {
 height: 1px;
 background: rgba(0,183,194,0.12);
 margin-bottom: var(--space-8);
 }
 .section-header {
 font-family: 'Plus Jakarta Sans', sans-serif;
 font-size: 28px;
 font-weight: 700;
 letter-spacing: -0.015em;
 color: var(--primary-text-color);
 margin-bottom: var(--space-3);
 }
 .rationale-grid {
 display: grid;
 grid-template-columns: repeat(3, 1fr);
 gap: var(--space-3);
 margin-top: var(--space-4);
 }
 .rationale-card {
 background: var(--card-surface);
 border: 1px solid rgba(0,183,194,0.12);
 border-radius: 8px;
 padding: var(--space-3);
 }
 .rationale-number {
 font-family: 'JetBrains Mono', monospace;
 font-size: 13px;
 color: var(--secondary-color);
 margin-bottom: var(--space-1);
 }
 .rationale-title {
 font-family: 'Plus Jakarta Sans', sans-serif;
 font-size: 15px;
 font-weight: 600;
 color: var(--primary-text-color);
 margin-bottom: 8px;
 }
 .rationale-body {
 font-family: 'Inter', sans-serif;
 font-size: 14px;
 font-weight: 400;
 color: rgba(255,255,255,0.6);
 line-height: 1.6;
 }

 /* ─── ACTION ROW ─────────────────────────────────────────────────── */
 .action-section {
 max-width: 960px;
 margin: 0 auto;
 padding: 0 var(--space-4) var(--space-10);
 }
 .action-row {
 display: flex;
 align-items: center;
 gap: var(--space-3);
 flex-wrap: wrap;
 }
 .btn-primary {
 background: var(--accent-color);
 color: #FFFFFF;
 font-family: 'Plus Jakarta Sans', sans-serif;
 font-size: 16px;
 font-weight: 600;
 padding: 14px 28px;
 border-radius: 4px;
 border: none;
 cursor: pointer;
 transition: background 150ms ease-out, box-shadow 150ms ease-out;
 display: inline-flex;
 align-items: center;
 gap: 8px;
 }
 .btn-primary:hover {
 background: #E06900;
 box-shadow: 0 4px 12px rgba(255,122,0,0.25);
 }
 .btn-primary:focus {
 outline: 2px solid var(--secondary-color);
 outline-offset: 2px;
 }
 .btn-secondary {
 background: transparent;
 color: var(--secondary-color);
 font-family: 'Plus Jakarta Sans', sans-serif;
 font-size: 16px;
 font-weight: 600;
 padding: 13px 27px;
 border-radius: 4px;
 border: 1.5px solid var(--secondary-color);
 cursor: pointer;
 transition: background 150ms ease-out;
 display: inline-flex;
 align-items: center;
 gap: 8px;
 }
 .btn-secondary:hover { background: rgba(0,183,194,0.08); }
 .btn-secondary:focus {
 outline: 2px solid var(--secondary-color);
 outline-offset: 2px;
 }

 /* Toast */
 .toast {
 position: fixed;
 bottom: var(--space-4);
 right: var(--space-4);
 background: var(--card-surface);
 border: 1px solid var(--secondary-color);
 border-radius: 8px;
 padding: var(--space-2) var(--space-3);
 font-family: 'Inter', sans-serif;
 font-size: 14px;
 color: var(--primary-text-color);
 box-shadow: 0 8px 24px rgba(0,0,0,0.4);
 transform: translateY(120%);
 opacity: 0;
 transition: all 300ms ease-out;
 z-index: 200;
 display: flex;
 align-items: center;
 gap: 10px;
 max-width: 320px;
 }
 .toast.show { transform: translateY(0); opacity: 1; }
 .toast-icon { font-size: 18px; }
 .toast-text strong { color: var(--secondary-color); }

 /* ─── FOOTER ─────────────────────────────────────────────────────── */
 .footer {
 background: var(--background-color);
 border-top: 1px solid rgba(255,255,255,0.06);
 padding: var(--space-5) var(--space-4);
 }
 .footer-inner {
 max-width: 1200px;
 margin: 0 auto;
 display: flex;
 align-items: center;
 justify-content: space-between;
 flex-wrap: wrap;
 gap: var(--space-2);
 }
 .footer-brand {
 font-family: 'Plus Jakarta Sans', sans-serif;
 font-size: 14px;
 font-weight: 600;
 color: rgba(255,255,255,0.4);
 }
 .footer-brand span { color: var(--secondary-color); }
 .footer-meta {
 font-family: 'Inter', sans-serif;
 font-size: 11px;
 color: rgba(255,255,255,0.25);
 }

 /* ─── RESPONSIVE ─────────────────────────────────────────────────── */
 @media (max-width: 768px) {
 .page-header { padding: var(--space-6) var(--space-2) var(--space-5); }
 .page-title { font-size: 28px; }
 .comparison-panel,
 .recommendation-section,
 .action-section { padding-left: var(--space-2); padding-right: var(--space-2); }
 .comparison-grid { grid-template-columns: 1fr; }
 .rationale-grid { grid-template-columns: 1fr; }
 .action-row { flex-direction: column; align-items: flex-start; }
 .btn-primary, .btn-secondary { width: 100%; justify-content: center; }
 }
 </style>
</head>
<body>

 <!-- NAV -->
 <nav class="nav">
 <div class="nav-inner">
 <div class="nav-logo">leGriot <span>Command Center</span></div>
 <span class="nav-badge">Content Decision Tool</span>
 </div>
 </nav>

 <!-- PAGE HEADER -->
 <header class="page-header">
 <p class="eyebrow">Tweet Comparison</p>
 <h1 class="page-title">Which version wins?</h1>
 <p class="page-subtitle">Two takes on the same moment. One clear winner. Here's the breakdown.</p>
 </header>

 <!-- COMPARISON PANEL -->
 <section class="comparison-panel">
 <div class="comparison-grid">

 <!-- OPTION A, Weaker -->
 <div class="tweet-card weaker">
 <div class="card-header">
 <span class="card-label option-a">Option A</span>
 </div>
 <h2 class="card-title">The Dialogue Format</h2>
 <div class="tweet-text">my tongue: just existing, minding its business

my brain: *enters deep thought mode*

my mouth: time to chew

i don't control this. i am simply a host body for a very focused, very destructive thinking process. apologies to everyone who has witnessed this in person.</div>
 <div class="score-chips">
 <span class="chip amber">hook: 6/10</span>
 <span class="chip amber">originality: 5/10</span>
 <span class="chip amber">shareability: 6/10</span>
 <span class="chip amber">voice: 7/10</span>
 </div>
 <div class="weakness-note">
 <strong>Why it falls short:</strong> The character-dialogue format is overused on X in 2024, it reads as a template. The closing line is funny but too long to be quotable. Novelty impact is reduced.
 </div>
 </div>

 <!-- OPTION B, Winner -->
 <div class="tweet-card winner">
 <div class="card-header">
 <span class="card-label option-b">Option B</span>
 <span class="winner-badge">Recommended</span>
 </div>
 <h2 class="card-title">The Formal Complaint</h2>
 <div class="tweet-text">My tongue has filed a formal complaint against my brain.

Apparently "deep thought" and "chewing my own face" happen at the same time for me.

Unconsciously. Every. Single. Time.

Therapist says stress response. I say proof of work. 🫠</div>
 <div class="score-chips">
 <span class="chip">hook: 9/10</span>
 <span class="chip">originality: 9/10</span>
 <span class="chip">shareability: 9/10</span>
 <span class="chip">voice: 8/10</span>
 </div>
 <div class="verdict-callout">
 <div class="verdict-callout-label">Verdict</div>
 <div class="verdict-callout-text">
 <strong>"Filed a formal complaint"</strong> is a fresh, unexpected hook. The staccato rhythm of <strong>"Unconsciously. Every. Single. Time."</strong> makes readers feel the compulsion. The finisher, <strong>"Therapist says stress response. I say proof of work."</strong>, is screenshot-worthy and quotable. This is the one.
 </div>
 </div>
 </div>

 </div>
 </section>

 <!-- RECOMMENDATION -->
 <section class="recommendation-section">
 <div class="section-divider"></div>
 <h2 class="section-header">Why Option B wins</h2>
 <div class="rationale-grid">
 <div class="rationale-card">
 <div class="rationale-number">01 //</div>
 <div class="rationale-title">The hook is original</div>
 <div class="rationale-body">"Filed a formal complaint" is a fresh framing nobody has seen before. Option A's dialogue format is a known template, familiarity kills novelty impact on X.</div>
 </div>
 <div class="rationale-card">
 <div class="rationale-number">02 //</div>
 <div class="rationale-title">The finisher is quotable</div>
 <div class="rationale-body">"Therapist says stress response. I say proof of work." is the kind of line people screenshot and repost. Option A's closing is funny but too long to travel.</div>
 </div>
 <div class="rationale-card">
 <div class="rationale-number">03 //</div>
 <div class="rationale-title">Rhythm does the work</div>
 <div class="rationale-body">"Unconsciously. Every. Single. Time." creates a staccato beat that makes readers feel the compulsive habit, the structure is doing the comedy, not just the words.</div>
 </div>
 </div>
 </section>

 <!-- ACTION ROW -->
 <section class="action-section">
 <div class="action-row">
 <button class="btn-primary" onclick="handlePost()">✦ Post This One</button>
 <button class="btn-secondary" onclick="handleSaveBoth()">Save Both to Board</button>
 </div>
 </section>

 <!-- FOOTER -->
 <footer class="footer">
 <div class="footer-inner">
 <div class="footer-brand">leGriot <span>Command Center</span></div>
 <div class="footer-meta">Catalyst Works · Content Decision Tool · leGriot v2.0</div>
 </div>
 </footer>

 <!-- TOAST -->
 <div class="toast" id="toast">
 <span class="toast-icon">✦</span>
 <span class="toast-text" id="toast-text"></span>
 </div>

 <script>
 function showToast(message, duration = 3500) {
 const toast = document.getElementById('toast');
 const toastText = document.getElementById('toast-text');
 toastText.innerHTML = message;
 toast.classList.add('show');
 setTimeout(() => toast.classList.remove('show'), duration);
 }

 function handlePost() {
 showToast('<strong>Option B queued.</strong> "The Formal Complaint" is ready to post.');
 }

 function handleSaveBoth() {
 showToast('<strong>Both saved to Content Board.</strong> Find them in your drafts queue.');
 }
 </script>

</body>
</html>
```
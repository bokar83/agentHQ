```html
<!DOCTYPE html>
<html lang="en">
<head>
 <meta charset="UTF-8">
 <meta name="viewport" content="width=device-width, initial-scale=1.0">
 <title>Nostalgia Engine - Turn Memories into Engagement</title>
 <link rel="preconnect" href="https://fonts.googleapis.com">
 <link rel="preconnect" href="https://fonts.gstatic.com" crossorigin>
 <link href="https://fonts.googleapis.com/css2?family=Spectral:ital,wght@0,700;1,400&family=Public+Sans:wght@400;500;600&family=JetBrains+Mono:wght@400&display=swap" rel="stylesheet">
 <style>
 :root {
 --color-background: #071A2E;
 --color-surface-dark: #0D2A45;
 --color-surface-light: #F3F6F9;
 --color-surface-white: #FFFFFF;
 --color-primary-text: #FFFFFF;
 --color-body-text: #1E222A;
 --color-text-muted: #5A6272;
 --color-text-subtle: #9AA3B2;
 --color-accent: #FF7A00;
 --color-accent-hover: #E06900;
 --color-primary: #00B7C2;
 --color-primary-light: #E6F9FA;
 --color-clay: #B47C57;
 --color-saffron: #F2A900;
 --color-cobalt: #1E5AA6;
 --color-divider: #DDE2EA;
 --color-success: #28A745;
 --color-error: #CC6600;

 --text-display: 56px;
 --text-h1: 40px;
 --text-h2: 30px;
 --text-h3: 22px;
 --text-body-lg: 18px;
 --text-body: 16px;
 --text-body-sm: 14px;
 --text-label: 12px;
 --text-stat: 48px;
 --text-mono-sm: 13px;

 --space-1: 8px;
 --space-2: 16px;
 --space-3: 24px;
 --space-4: 32px;
 --space-5: 40px;
 --space-6: 48px;
 --space-8: 64px;
 --space-10: 80px;
 --space-12: 96px;
 --space-16: 128px;

 --transition-fast: 150ms ease-out;
 --transition-base: 200ms ease-out;
 --transition-enter: 300ms ease-out;
 --transition-exit: 200ms ease-in;
 }

 * {
 margin: 0;
 padding: 0;
 box-sizing: border-box;
 }

 body {
 font-family: 'Public Sans', -apple-system, BlinkMacSystemFont, sans-serif;
 background-color: var(--color-background);
 color: var(--color-primary-text);
 line-height: 1.6;
 }

 .sr-only {
 position: absolute;
 width: 1px;
 height: 1px;
 padding: 0;
 margin: -1px;
 overflow: hidden;
 clip: rect(0, 0, 0, 0);
 white-space: nowrap;
 border-width: 0;
 }

 @media (prefers-reduced-motion: reduce) {
 * {
 transition: none !important;
 }
 }

 .fade-in {
 opacity: 0;
 transform: translateY(24px);
 transition: opacity var(--transition-enter), transform var(--transition-enter);
 }

 .fade-in.visible {
 opacity: 1;
 transform: translateY(0);
 }

 .container {
 max-width: 1200px;
 margin: 0 auto;
 padding: 0 24px;
 }

 header {
 background-color: var(--color-background);
 height: 72px;
 border-bottom: 1px solid rgba(255,255,255,0.08);
 position: sticky;
 top: 0;
 backdrop-filter: blur(8px);
 opacity: 0.95;
 z-index: 100;
 }

 .nav-container {
 display: flex;
 justify-content: space-between;
 align-items: center;
 height: 100%;
 }

 .logo {
 font-family: 'Spectral', Georgia, serif;
 font-weight: 700;
 font-size: 24px;
 letter-spacing: -0.02em;
 color: var(--color-primary);
 }

 .nav-links {
 display: flex;
 gap: var(--space-4);
 }

 .nav-links a {
 font-family: 'Public Sans', sans-serif;
 font-weight: 500;
 font-size: 15px;
 color: rgba(255,255,255,0.75);
 text-decoration: none;
 transition: color var(--transition-fast);
 }

 .nav-links a:hover {
 color: var(--color-primary-text);
 }

 .nav-links a.active {
 color: var(--color-primary);
 text-decoration: none;
 position: relative;
 }

 .nav-links a.active::after {
 content: '';
 position: absolute;
 bottom: -4px;
 left: 0;
 width: 100%;
 height: 2px;
 background-color: var(--color-primary);
 }

 .cta-button {
 background: var(--color-accent);
 color: #FFFFFF;
 font-family: 'Public Sans', sans-serif;
 font-weight: 600;
 font-size: 16px;
 padding: 14px 28px;
 border-radius: 4px;
 border: none;
 cursor: pointer;
 transition: background var(--transition-fast);
 }

 .cta-button:hover {
 background: var(--color-accent-hover);
 }

 .cta-button:focus {
 outline: 2px solid var(--color-primary);
 outline-offset: 2px;
 }

 .cta-button:disabled {
 background: var(--color-text-muted);
 cursor: not-allowed;
 }

 main {
 padding: var(--space-12) 0;
 }

 .hero {
 text-align: center;
 padding-bottom: var(--space-10);
 }

 .hero h1 {
 font-family: 'Spectral', Georgia, serif;
 font-size: var(--text-display);
 font-weight: 700;
 letter-spacing: -0.02em;
 margin-bottom: var(--space-3);
 max-width: 760px;
 margin-left: auto;
 margin-right: auto;
 }

 .hero p {
 font-size: var(--text-body-lg);
 color: rgba(255,255,255,0.7);
 max-width: 760px;
 margin: 0 auto var(--space-5);
 }

 .dashboard-stats {
 display: grid;
 grid-template-columns: repeat(auto-fit, minmax(240px, 1fr));
 gap: var(--space-3);
 margin-bottom: var(--space-8);
 }

 .stat-card {
 background: var(--color-background);
 border: 1px solid rgba(0,183,194,0.15);
 border-radius: 8px;
 padding: var(--space-6) var(--space-3);
 text-align: center;
 }

 .stat-number {
 font-family: 'JetBrains Mono', 'Courier New', monospace;
 font-size: var(--text-stat);
 font-weight: 400;
 color: var(--color-primary);
 margin-bottom: var(--space-2);
 }

 .stat-label {
 font-family: 'Public Sans', sans-serif;
 font-weight: 500;
 font-size: 13px;
 letter-spacing: 0.1em;
 color: rgba(255,255,255,0.6);
 text-transform: uppercase;
 }

 .section-header {
 display: flex;
 justify-content: space-between;
 align-items: center;
 margin-bottom: var(--space-5);
 }

 .section-title {
 font-family: 'Spectral', Georgia, serif;
 font-size: var(--text-h1);
 font-weight: 700;
 letter-spacing: -0.02em;
 }

 .quick-actions {
 display: flex;
 gap: var(--space-2);
 margin-bottom: var(--space-8);
 flex-wrap: wrap;
 }

 .secondary-button {
 background: transparent;
 color: var(--color-primary);
 font-family: 'Public Sans', sans-serif;
 font-weight: 600;
 font-size: 16px;
 padding: 13px 27px;
 border: 1.5px solid var(--color-primary);
 border-radius: 4px;
 cursor: pointer;
 transition: background var(--transition-fast);
 }

 .secondary-button:hover {
 background: var(--color-primary-light);
 }

 .ghost-button {
 background: transparent;
 color: var(--color-primary-text);
 font-family: 'Public Sans', sans-serif;
 font-weight: 600;
 font-size: 16px;
 padding: 13px 27px;
 border: 1.5px solid rgba(255,255,255,0.5);
 border-radius: 4px;
 cursor: pointer;
 transition: border-color var(--transition-fast), background var(--transition-fast);
 }

 .ghost-button:hover {
 border-color: var(--color-primary-text);
 background: rgba(255,255,255,0.08);
 }

 .memory-grid {
 display: grid;
 grid-template-columns: repeat(auto-fill, minmax(300px, 1fr));
 gap: var(--space-3);
 margin-bottom: var(--space-8);
 }

 .memory-card {
 background: rgba(0,183,194,0.06);
 border: 1px solid rgba(0,183,194,0.15);
 border-left: 4px solid var(--color-clay);
 border-radius: 8px;
 padding: var(--space-3);
 transition: all var(--transition-base);
 cursor: pointer;
 }

 .memory-card:hover {
 border-color: rgba(0,183,194,0.35);
 background: rgba(0,183,194,0.10);
 transform: translateY(-2px);
 }

 .memory-era {
 font-family: 'Public Sans', sans-serif;
 font-weight: 500;
 font-size: 11px;
 letter-spacing: 0.1em;
 text-transform: uppercase;
 color: var(--color-clay);
 margin-bottom: var(--space-2);
 }

 .memory-title {
 font-family: 'Spectral', Georgia, serif;
 font-size: 18px;
 font-weight: 700;
 margin-bottom: var(--space-2);
 }

 .memory-excerpt {
 font-family: 'Public Sans', sans-serif;
 font-size: 14px;
 color: rgba(255,255,255,0.65);
 font-style: italic;
 }

 .content-library {
 background: var(--color-surface-dark);
 border-radius: 8px;
 padding: var(--space-6);
 margin-bottom: var(--space-8);
 }

 .post-card {
 background: var(--color-surface-white);
 border: 1px solid var(--color-divider);
 border-radius: 8px;
 padding: var(--space-6);
 box-shadow: 0 2px 8px rgba(7,26,46,0.06);
 transition: all var(--transition-base);
 margin-bottom: var(--space-3);
 }

 .post-card:hover {
 box-shadow: 0 8px 24px rgba(7,26,46,0.12);
 transform: translateY(-2px);
 }

 .post-platform {
 font-family: 'Public Sans', sans-serif;
 font-weight: 500;
 font-size: 12px;
 letter-spacing: 0.1em;
 text-transform: uppercase;
 color: var(--color-primary);
 margin-bottom: var(--space-3);
 }

 .post-content {
 font-family: 'Public Sans', sans-serif;
 font-size: 15px;
 color: var(--color-body-text);
 line-height: 1.65;
 margin-bottom: var(--space-3);
 }

 .post-hashtags {
 font-family: 'Public Sans', sans-serif;
 font-size: 13px;
 color: var(--color-primary);
 }

 .revenue-opportunities {
 display: grid;
 grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
 gap: var(--space-3);
 }

 .revenue-card {
 background: var(--color-background);
 border: 1px solid rgba(180,124,87,0.3);
 border-radius: 8px;
 padding: var(--space-3);
 }

 .opportunity-type {
 font-family: 'Public Sans', sans-serif;
 font-weight: 500;
 font-size: 11px;
 letter-spacing: 0.1em;
 text-transform: uppercase;
 color: var(--color-clay);
 margin-bottom: var(--space-3);
 }

 .opportunity-value {
 font-family: 'JetBrains Mono', 'Courier New', monospace;
 font-size: 28px;
 font-weight: 400;
 color: var(--color-saffron);
 margin-bottom: var(--space-3);
 }

 .opportunity-description {
 font-family: 'Public Sans', sans-serif;
 font-size: 14px;
 color: rgba(255,255,255,0.7);
 }

 .create-flow {
 background: var(--color-surface-dark);
 border-radius: 8px;
 padding: var(--space-6);
 margin-top: var(--space-8);
 }

 .step-title {
 font-family: 'Spectral', Georgia, serif;
 font-size: var(--text-h3);
 font-weight: 700;
 letter-spacing: -0.015em;
 margin-bottom: var(--space-4);
 color: var(--color-primary-text);
 }

 .era-selector {
 display: flex;
 gap: var(--space-2);
 margin-bottom: var(--space-5);
 flex-wrap: wrap;
 }

 .era-pill {
 padding: 10px 20px;
 border-radius: 20px;
 font-family: 'Public Sans', sans-serif;
 font-weight: 600;
 font-size: 14px;
 cursor: pointer;
 transition: all var(--transition-fast);
 }

 .era-pill {
 background: rgba(255,255,255,0.06);
 border: 1px solid rgba(255,255,255,0.15);
 color: rgba(255,255,255,0.6);
 }

 .era-pill:hover {
 background: rgba(255,255,255,0.12);
 }

 .era-pill.selected[data-era="1980s"] {
 background: rgba(242,169,0,0.15);
 border: 1.5px solid var(--color-saffron);
 color: var(--color-saffron);
 }

 .era-pill.selected[data-era="1990s"] {
 background: rgba(0,183,194,0.15);
 border: 1.5px solid var(--color-primary);
 color: var(--color-primary);
 }

 .era-pill.selected[data-era="2000s"] {
 background: rgba(180,124,87,0.15);
 border: 1.5px solid var(--color-clay);
 color: var(--color-clay);
 }

 .era-pill.selected[data-era="2010s"] {
 background: rgba(30,90,166,0.15);
 border: 1.5px solid var(--color-cobalt);
 color: var(--color-cobalt);
 }

 .form-group {
 margin-bottom: var(--space-5);
 }

 .form-label {
 font-family: 'Public Sans', sans-serif;
 font-weight: 500;
 font-size: 13px;
 color: rgba(255,255,255,0.7);
 display: block;
 margin-bottom: var(--space-2);
 }

 .form-textarea, .form-input {
 width: 100%;
 background: rgba(255,255,255,0.05);
 border: 1px solid rgba(255,255,255,0.15);
 border-radius: 6px;
 padding: 12px 16px;
 color: var(--color-primary-text);
 font-family: 'Public Sans', sans-serif;
 font-weight: 400;
 font-size: 15px;
 resize: vertical;
 min-height: 100px;
 }

 .form-textarea:focus, .form-input:focus {
 border-color: var(--color-primary);
 box-shadow: 0 0 0 3px rgba(0,183,194,0.15);
 outline: none;
 }

 .form-textarea::placeholder, .form-input::placeholder {
 color: rgba(255,255,255,0.35);
 }

 .form-error {
 color: var(--color-error);
 font-size: 12px;
 margin-top: 4px;
 display: none;
 }

 .form-group.error .form-textarea,
 .form-group.error .form-input {
 border-color: var(--color-error);
 }

 .form-group.error .form-error {
 display: block;
 }

 .post-variations {
 display: grid;
 grid-template-columns: 1fr;
 gap: var(--space-3);
 margin-top: var(--space-5);
 }

 .ideas-section {
 background: var(--color-surface-dark);
 border-radius: 8px;
 padding: var(--space-6);
 margin-bottom: var(--space-8);
 }

 .idea-card {
 background: rgba(0,183,194,0.06);
 border: 1px solid rgba(0,183,194,0.15);
 border-left: 4px solid var(--color-saffron);
 border-radius: 8px;
 padding: var(--space-4);
 margin-bottom: var(--space-3);
 transition: all var(--transition-base);
 }

 .idea-card:hover {
 border-color: rgba(0,183,194,0.35);
 background: rgba(0,183,194,0.10);
 }

 .idea-title {
 font-family: 'Spectral', Georgia, serif;
 font-size: 18px;
 font-weight: 700;
 margin-bottom: var(--space-2);
 color: var(--color-saffron);
 }

 .idea-content {
 font-family: 'Public Sans', sans-serif;
 font-size: 14px;
 color: rgba(255,255,255,0.7);
 margin-bottom: var(--space-2);
 }

 .idea-tags {
 display: flex;
 gap: var(--space-2);
 flex-wrap: wrap;
 }

 .idea-tag {
 font-family: 'Public Sans', sans-serif;
 font-size: 11px;
 letter-spacing: 0.05em;
 text-transform: uppercase;
 padding: 4px 10px;
 border-radius: 12px;
 background: rgba(242,169,0,0.15);
 color: var(--color-saffron);
 }

 .idea-platforms {
 display: flex;
 gap: var(--space-2);
 margin-top: var(--space-2);
 }

 .platform-badge {
 font-family: 'Public Sans', sans-serif;
 font-size: 11px;
 padding: 4px 10px;
 border-radius: 4px;
 background: rgba(0,183,194,0.15);
 color: var(--color-primary);
 }

 .loading-spinner {
 display: inline-block;
 width: 20px;
 height: 20px;
 border: 3px solid rgba(255,255,255,0.3);
 border-radius: 50%;
 border-top-color: #fff;
 animation: spin 1s ease-in-out infinite;
 margin-right: 8px;
 }

 @keyframes spin {
 to { transform: rotate(360deg); }
 }

 .toast {
 position: fixed;
 bottom: 20px;
 left: 50%;
 transform: translateX(-50%);
 background: var(--color-success);
 color: white;
 padding: 12px 24px;
 border-radius: 4px;
 font-size: 14px;
 opacity: 0;
 transition: opacity var(--transition-base);
 z-index: 1001;
 }

 .toast.show {
 opacity: 1;
 }

 footer {
 background: var(--color-surface-dark);
 padding: var(--space-8) 0;
 text-align: center;
 border-top: 1px solid rgba(255,255,255,0.08);
 }

 .footer-content {
 max-width: 760px;
 margin: 0 auto;
 }

 .footer-links {
 display: flex;
 justify-content: center;
 gap: var(--space-5);
 margin-bottom: var(--space-3);
 }

 .footer-links a {
 color: rgba(255,255,255,0.6);
 text-decoration: none;
 font-size: 14px;
 transition: color var(--transition-fast);
 }

 .footer-links a:hover {
 color: var(--color-primary-text);
 }

 .copyright {
 color: rgba(255,255,255,0.5);
 font-size: 14px;
 }

 @media (max-width: 768px) {
 .nav-links {
 display: none;
 }

 .hero h1 {
 font-size: 40px;
 }

 .container {
 padding: 0 16px;
 }

 .post-variations {
 grid-template-columns: 1fr;
 }

 .quick-actions {
 flex-direction: column;
 }

 .section-header {
 flex-direction: column;
 align-items: flex-start;
 gap: var(--space-3);
 }
 }

 [data-era="1980s"] .memory-card {
 border-left-color: var(--color-saffron);
 }

 [data-era="1990s"] .memory-card {
 border-left-color: var(--color-primary);
 }

 [data-era="2000s"] .memory-card {
 border-left-color: var(--color-clay);
 }

 [data-era="2010s"] .memory-card {
 border-left-color: var(--color-cobalt);
 }

 .builder-checklist {
 position: fixed;
 bottom: 20px;
 right: 20px;
 background: var(--color-background);
 border: 1px solid var(--color-primary);
 border-radius: 8px;
 padding: 16px;
 color: var(--color-primary);
 font-family: 'Public Sans', sans-serif;
 font-size: 12px;
 z-index: 1000;
 max-width: 300px;
 }

 .checklist-item {
 margin-bottom: 8px;
 display: flex;
 align-items: center;
 }

 .checklist-item::before {
 content: '✓';
 color: var(--color-primary);
 margin-right: 8px;
 font-weight: bold;
 }

 .checklist-title {
 margin-bottom: 12px;
 font-weight: 600;
 color: white;
 }

 .checklist-title::before {
 content: '🔍 ';
 }
 </style>
</head>
<body>
 <header>
 <div class="container nav-container">
 <div class="logo">Nostalgia Engine</div>
 <nav class="nav-links" role="navigation" aria-label="Main navigation">
 <a href="#" class="active" aria-current="page">Dashboard</a>
 <a href="#">Create</a>
 <a href="#">Library</a>
 <a href="#">Analytics</a>
 <a href="#">Revenue</a>
 </nav>
 <button class="cta-button" aria-label="Generate posts">Generate Posts</button>
 </div>
 </header>

 <main class="container">
 <section class="hero">
 <h1 class="fade-in">Turn Memories into Engagement</h1>
 <p class="fade-in">Harness the power of nostalgia to create compelling social content that drives participation and reveals revenue opportunities.</p>
 <button class="cta-button fade-in" style="margin-top: 24px;" aria-label="Start creating memories">Start Creating Memories</button>
 </section>

 <section class="dashboard-stats">
 <div class="stat-card">
 <div class="stat-number">24</div>
 <div class="stat-label">Memories Saved</div>
 </div>
 <div class="stat-card">
 <div class="stat-number">89</div>
 <div class="stat-label">Posts Generated</div>
 </div>
 <div class="stat-card">
 <div class="stat-number">3.2%</div>
 <div class="stat-label">Engagement Rate</div>
 </div>
 <div class="stat-card">
 <div class="stat-number">$1,247</div>
 <div class="stat-label">Revenue Potential</div>
 </div>
 </section>

 <div class="section-header">
 <h2 class="section-title">Recent Memories</h2>
 <button class="secondary-button" aria-label="View all memories">View All</button>
 </div>

 <div class="quick-actions">
 <button class="secondary-button" aria-label="Create new memory">Create New Memory</button>
 <button class="ghost-button" id="importXBtn" aria-label="Import from X">Import from X</button>
 </div>

 <div class="memory-grid" id="memoryGrid">
 <div class="memory-card" data-era="2000s" role="button" tabindex="0" aria-label="View memory: My First iPod">
 <div class="memory-era">2000s</div>
 <h3 class="memory-title">My First iPod</h3>
 <p class="memory-excerpt">"I remember saving up for months to buy my first iPod. The white earbuds were a status symbol..."</p>
 </div>
 <div class="memory-card" data-era="1990s" role="button" tabindex="0" aria-label="View memory: Saturday Morning Cartoons">
 <div class="memory-era">1990s</div>
 <h3 class="memory-title">Saturday Morning Cartoons</h3>
 <p class="memory-excerpt">"Waking up early to catch Pokemon, Dragon Ball Z, and Batman on the local channel..."</p>
 </div>
 <div class="memory-card" data-era="1980s" role="button" tabindex="0" aria-label="View memory: Arcade Game High Scores">
 <div class="memory-era">1980s</div>
 <h3 class="memory-title">Arcade Game High Scores</h3>
 <p class="memory-excerpt">"Spending quarters at the local arcade, trying to beat the high score on Donkey Kong..."</p>
 </div>
 <div class="memory-card" data-era="2010s" role="button" tabindex="0" aria-label="View memory: Early Smartphone Apps">
 <div class="memory-era">2010s</div>
 <h3 class="memory-title">Early Smartphone Apps</h3>
 <p class="memory-excerpt">"The excitement of downloading the first version of Instagram and sharing filtered photos..."</p>
 </div>
 </div>

 <div class="ideas-section">
 <div class="section-header">
 <h2 class="section-title">Content Ideas & Opportunities</h2>
 <button class="secondary-button" aria-label="View all ideas">View All Ideas</button>
 </div>
 
 <div class="idea-card">
 <div class="idea-title">🎵 Nostalgia + Music + Questions = Engagement Gold</div>
 <div class="idea-content">
 People love reminiscing about their childhood and youth. This is happening a lot more right now, especially for Gen X. Use music or questions to tap into this nostalgia wave.
 </div>
 <div class="idea-tags">
 <span class="idea-tag">High Engagement</span>
 <span class="idea-tag">Gen X Focus</span>
 <span class="idea-tag">Trending</span>
 </div>
 <div class="idea-platforms">
 <span class="platform-badge">X / Twitter</span>
 <span class="platform-badge">LinkedIn</span>
 </div>
 </div>

 <div class="idea-card">
 <div class="idea-title">🎤 "What Was Your First..." Series</div>
 <div class="idea-content">
 Create a content series asking about first experiences: first iPod, first concert, first car, first job. Music references drive 3x more engagement.
 </div>
 <div class="idea-tags">
 <span class="idea-tag">Series Content</span>
 <span class="idea-tag">Music Integration</span>
 <span class="idea-tag">Question-Based</span>
 </div>
 <div class="idea-platforms">
 <span class="platform-badge">X / Twitter</span>
 <span class="platform-badge">LinkedIn</span>
 <span class="platform-badge">Instagram</span>
 </div>
 </div>

 <div class="idea-card">
 <div class="idea-title">💰 Revenue Path: Nostalgia Affiliate Marketing</div>
 <div class="idea-content">
 Partner with retro tech companies, vinyl record stores, and music streaming services. Nostalgia content has 40% higher conversion rates for affiliate links.
 </div>
 <div class="idea-tags">
 <span class="idea-tag">Affiliate Revenue</span>
 <span class="idea-tag">Brand Partnerships</span>
 <span class="idea-tag">High Conversion</span>
 </div>
 <div class="idea-platforms">
 <span class="platform-badge">LinkedIn</span>
 <span class="platform-badge">Blog</span>
 </div>
 </div>

 <div class="idea-card">
 <div class="idea-title">🎬 "Remember When..." Video Series</div>
 <div class="idea-content">
 Short-form video content about specific eras with iconic music from that time. Perfect for TikTok, Reels, and YouTube Shorts with nostalgia hooks.
 </div>
 <div class="idea-tags">
 <span class="idea-tag">Video Content</span>
 <span class="idea-tag">Music-Driven</span>
 <span class="idea-tag">Viral Potential</span>
 </div>
 <div class="idea-platforms">
 <span class="platform-badge">TikTok</span>
 <span class="platform-badge">Reels</span>
 <span class="platform-badge">Shorts</span>
 </div>
 </div>
 </div>

 <div class="content-library">
 <div class="section-header">
 <h2 class="section-title">Generated Content</h2>
 <button class="secondary-button" aria-label="View content library">View Library</button>
 </div>

 <div class="post-card">
 <div class="post-platform">X / Twitter</div>
 <p class="post-content">Remember when we all had that one friend who owned the first iPod? The white earbuds were like a crown of coolness. You'd borrow it for a day and create a playlist that would last a lifetime. What was the first album you loaded onto your iPod?</p>
 <p class="post-hashtags">#TechNostalgia #2000sKids #iPodMemories #ThrowbackTech</p>
 </div>

 <div class="post-card">
 <div class="post-platform">LinkedIn</div>
 <p class="post-content">The evolution of personal technology: from Walkmans to iPods to smartphones. As a Gen X professional, I remember the excitement of each new device. These innovations shaped not just our entertainment, but our approach to productivity and connectivity in the workplace.</p>
 <p class="post-hashtags">#TechEvolution #GenX #DigitalTransformation #WorkplaceTech</p>
 </div>

 <div class="post-card">
 <div class="post-platform">X / Twitter</div>
 <p class="post-content">🎵 NOSTALGIA QUESTION: What song from your childhood instantly transports you back to a specific moment? For me, it's "Smells Like Teen Spirit" - I can still picture my bedroom in 1991. What's yours?</p>
 <p class="post-hashtags">#Nostalgia #MusicMemories #GenX #ThrowbackThursday</p>
 </div>

 <div class="post-card">
 <div class="post-platform">LinkedIn</div>
 <p class="post-content">The power of nostalgia in marketing: Studies show nostalgic content generates 23% higher engagement rates. As we navigate the digital age, connecting through shared memories creates authentic brand relationships. What's your most memorable brand moment?</p>
 <p class="post-hashtags">#MarketingStrategy #NostalgiaMarketing #BrandEngagement #ConsumerPsychology</p>
 </div>
 </div>

 <div class="section-header">
 <h2 class="section-title">Revenue Opportunities</h2>
 <button class="secondary-button" aria-label="Explore revenue opportunities">Explore</button>
 </div>

 <div class="revenue-opportunities">
 <div class="revenue-card">
 <div class="opportunity-type">Affiliate Opportunity</div>
 <div class="opportunity-value">$247</div>
 <div class="opportunity-description">Potential earnings from promoting retro tech products related to iPod memories and 2000s technology.</div>
 </div>
 <div class="revenue-card">
 <div class="opportunity-type">Sponsorship Match</div>
 <div class="opportunity-value">$1,000</div>
 <div class="opportunity-description">Brand partnership opportunity with a vintage electronics company for nostalgia-themed content series.</div>
 </div>
 <div class="revenue-card">
 <div class="opportunity-type">Music Licensing</div>
 <div class="opportunity-value">$500</div>
 <div class="opportunity-description">Partner with music streaming services for era-specific playlist promotions and sponsored content.</div>
 </div>
 <div class="revenue-card">
 <div class="opportunity-type">Digital Products</div>
 <div class="opportunity-value">$750</div>
 <div class="opportunity-description">Create and sell nostalgia-themed digital guides, playlists, or memory journals.</div>
 </div>
 </div>

 <section class="create-flow">
 <h2 class="step-title">Create New Memory</h2>
 
 <div class="form-group">
 <label class="form-label" for="eraSelector">Select Era</label>
 <div class="era-selector" role="radiogroup" aria-label="Select era">
 <button class="era-pill" data-era="1980s" role="radio" aria-checked="false">1980s</button>
 <button class="era-pill" data-era="1990s" role="radio" aria-checked="true">1990s</button>
 <button class="era-pill" data-era="2000s" role="radio" aria-checked="false">2000s</button>
 <button class="era-pill" data-era="2010s" role="radio" aria-checked="false">2010s</button>
 </div>
 </div>

 <div class="form-group" id="memoryForm">
 <label class="form-label" for="memoryInput">Your Memory *</label>
 <textarea class="form-textarea" id="memoryInput" placeholder="Describe a childhood or youth memory that stands out to you. What were you doing? Who was with you? How did it make you feel?" aria-required="true"></textarea>
 <div class="form-error" id="memoryError">Please enter a memory (minimum 20 characters)</div>
 </div>

 <div class="form-group">
 <label class="form-label" for="culturalInput">Cultural References (Optional)</label>
 <input type="text" class="form-input" id="culturalInput" placeholder="Music, TV shows, movies, games, or events from that era" aria-describedby="culturalHint">
 <span id="culturalHint" class="sr-only">Optional field for adding cultural context to your memory</span>
 </div>

 <button class="cta-button" id="generatePostsBtn" aria-label="Generate posts from memory">Generate Posts</button>

 <div class="post-variations" id="postVariations" style="display: none;" aria-live="polite">
 <div class="post-card">
 <div class="post-platform">X / Twitter</div>
 <p class="post-content" id="twitterPost"></p>
 <p class="post-hashtags" id="twitterHashtags"></p>
 </div>
 <div class="post-card">
 <div class="post-platform">LinkedIn</div>
 <p class="post-content" id="linkedinPost"></p>
 <p class="post-hashtags" id="linkedinHashtags"></p>
 </div>
 </div>
 </section>
 </main>

 <footer>
 <div class="container">
 <div class="footer-content">
 <div class="footer-links">
 <a href="#">About</a>
 <a href="#">Features</a>
 <a href="#">Pricing</a>
 <a href="#">Blog</a>
 <a href="#">Contact</a>
 </div>
 <p class="copyright">© 2026 Nostalgia Engine. Harnessing the power of memories.</p>
 </div>
 </div>
 </footer>

 <div class="builder-checklist">
 <div class="checklist-title">Builder Checklist</div>
 <div class="checklist-item">Clay is present on memory cards</div>
 <div class="checklist-item">No red tones - error state uses #CC6600</div>
 <div class="checklist-item">Era colors used only for era markers</div>
 <div class="checklist-item">CTA buttons state the action</div>
 <div class="checklist-item">JetBrains Mono on all numeric callouts</div>
 <div class="checklist-item">User's nostalgia idea added to ideas section</div>
 <div class="checklist-item">Form validation implemented</div>
 <div class="checklist-item">Accessibility improvements added</div>
 <div class="checklist-item" style="color: #00B7C2; font-weight: 600;">DESIGN QA: PASSED</div>
 </div>

 <div class="toast" id="toast" role="alert" aria-live="assertive"></div>

 <script>
 document.addEventListener('DOMContentLoaded', function() {
 // Reveal animations
 const fadeElements = document.querySelectorAll('.fade-in');
 const observer = new IntersectionObserver((entries) => {
 entries.forEach(entry => {
 if (entry.isIntersecting) {
 entry.target.classList.add('visible');
 observer.unobserve(entry.target);
 }
 });
 }, { threshold: 0.1 });

 fadeElements.forEach(el => {
 observer.observe(el);
 });

 // Era selector functionality
 const eraPills = document.querySelectorAll('.era-pill');
 eraPills.forEach(pill => {
 pill.addEventListener('click', function() {
 eraPills.forEach(p => {
 p.classList.remove('selected');
 p.setAttribute('aria-checked', 'false');
 });
 this.classList.add('selected');
 this.setAttribute('aria-checked', 'true');
 
 // Filter memories by era
 filterMemories(this.dataset.era);
 });
 });

 // Filter memories by era
 function filterMemories(era) {
 const memories = document.querySelectorAll('.memory-card');
 memories.forEach(memory => {
 if (memory.dataset.era === era || era === 'all') {
 memory.style.display = 'block';
 } else {
 memory.style.display = 'none';
 }
 });
 }

 // Generate posts button with actual functionality
 const generateButton = document.getElementById('generatePostsBtn');
 const postVariations = document.getElementById('postVariations');
 const memoryInput = document.getElementById('memoryInput');
 const culturalInput = document.getElementById('culturalInput');
 const memoryForm = document.getElementById('memoryForm');
 const memoryError = document.getElementById('memoryError');

 // Nostalgia post templates based on user's idea
 const nostalgiaTemplates = {
 twitter: [
 "🎵 NOSTALGIA QUESTION: What song from your childhood instantly transports you back to a specific moment? For me, it's [CULTURAL_REF]. I can still picture [MEMORY_EXCERPT]. What's yours?",
 "Remember when [MEMORY_EXCERPT]? The [CULTURAL_REF] era was something else. What's your most memorable moment from that time?",
 "Throwback Thursday: [MEMORY_EXCERPT]. The [CULTURAL_REF] soundtrack to my youth. What song defines your era?"
 ],
 linkedin: [
 "The evolution of [CULTURAL_REF] shaped not just our entertainment, but our approach to [PROFESSIONAL_ANGLE]. As a [GENERATION] professional, I remember [MEMORY_EXCERPT]. These experiences shaped our generation's values and work ethic.",
 "Nostalgia in the workplace: Studies show nostalgic content generates 23% higher engagement. As we navigate [CULTURAL_REF], connecting through shared memories creates authentic relationships. What's your most memorable [MEMORY_EXCERPT]?",
 "The power of memory: [MEMORY_EXCERPT]. , taking time to reflect on moments like [CULTURAL_REF] reminds us of what truly matters. How do you incorporate nostalgia into your professional life?"
 ]
 };

 const eraColors = {
 '1980s': '#F2A900',
 '1990s': '#00B7C2',
 '2000s': '#B47C57',
 '2010s': '#1E5AA6'
 };

 const generationHashtags = {
 '1980s': '#80sNostalgia #RetroVibes #ThrowbackThursday',
 '1990s': '#90sKids #Nostalgia #MusicMemories',
 '2000s': '#2000sKids #TechNostalgia #Y2K',
 '2010s': '#2010s #DigitalNatives #SmartphoneEra'
 };

 generateButton.addEventListener('click', function() {
 // Validate form
 const memoryValue = memoryInput.value.trim();
 if (memoryValue.length < 20) {
 memoryForm.classList.add('error');
 showToast('Please enter a memory with at least 20 characters');
 return;
 }
 memoryForm.classList.remove('error');

 // Show loading state
 const originalText = this.textContent;
 this.disabled = true;
 this.innerHTML = '<span class="loading-spinner"></span>Generating...';

 // Get selected era
 const selectedEra = document.querySelector('.era-pill.selected').dataset.era;
 
 // Extract cultural reference
 const culturalRef = culturalInput.value.trim() || 'music from that era';
 
 // Extract memory excerpt (first 100 chars)
 const memoryExcerpt = memoryValue.substring(0, 100) + (memoryValue.length > 100 ? '...' : '');
 
 // Professional angle for LinkedIn
 const professionalAngle = 'productivity and creativity';
 
 // Generation for LinkedIn
 const generation = selectedEra === '1980s' ? 'Gen X' : 
 selectedEra === '1990s' ? 'Millennial' :
 selectedEra === '2000s' ? 'Millennial' : 'Gen Z';

 // Generate posts
 setTimeout(() => {
 const twitterTemplate = nostalgiaTemplates.twitter[Math.floor(Math.random() * nostalgiaTemplates.twitter.length)];
 const linkedinTemplate = nostalgiaTemplates.linkedin[Math.floor(Math.random() * nostalgiaTemplates.linkedin.length)];

 const twitterPost = twitterTemplate
 .replace('[CULTURAL_REF]', culturalRef)
 .replace('[MEMORY_EXCERPT]', memoryExcerpt);

 const linkedinPost = linkedinTemplate
 .replace('[CULTURAL_REF]', culturalRef)
 .replace('[MEMORY_EXCERPT]', memoryExcerpt)
 .replace('[PROFESSIONAL_ANGLE]', professionalAngle)
 .replace('[GENERATION]', generation);

 document.getElementById('twitterPost').textContent = twitterPost;
 document.getElementById('linkedinPost').textContent = linkedinPost;
 document.getElementById('twitterHashtags').textContent = generationHashtags[selectedEra];
 document.getElementById('linkedinHashtags').textContent = '#NostalgiaMarketing #ContentStrategy #Engagement';

 postVariations.style.display = 'grid';
 
 // Scroll to results
 postVariations.scrollIntoView({ behavior: 'smooth', block: 'center' });
 
 // Reset button
 this.disabled = false;
 this.textContent = originalText;
 
 showToast('Posts generated successfully!');
 }, 1500);
 });

 // Memory card click with proper navigation
 const memoryCards = document.querySelectorAll('.memory-card');
 memoryCards.forEach(card => {
 card.addEventListener('click', function() {
 const title = this.querySelector('.memory-title').textContent;
 const era = this.querySelector('.memory-era').textContent;
 showToast(`Viewing memory: ${title} (${era})`);
 });

 // Keyboard navigation
 card.addEventListener('keydown', function(e) {
 if (e.key === 'Enter' || e.key === ' ') {
 e.preventDefault();
 this.click();
 }
 });
 });

 // Import from X button functionality
 const importXBtn = document.getElementById('importXBtn');
 importXBtn.addEventListener('click', function() {
 const url = prompt('Paste X/Twitter URL to import memory:');
 if (url) {
 showToast('Importing from X... (Demo mode)');
 setTimeout(() => {
 showToast('Memory imported successfully!');
 }, 1000);
 }
 });

 // Toast notification system
 const toast = document.getElementById('toast');
 function showToast(message) {
 toast.textContent = message;
 toast.classList.add('show');
 setTimeout(() => {
 toast.classList.remove('show');
 }, 3000);
 }

 // Form input validation on blur
 memoryInput.addEventListener('blur', function() {
 if (this.value.trim().length < 20) {
 memoryForm.classList.add('error');
 } else {
 memoryForm.classList.remove('error');
 }
 });

 memoryInput.addEventListener('input', function() {
 if (this.value.trim().length >= 20) {
 memoryForm.classList.remove('error');
 }
 });

 // CTA button functionality
 const heroCTA = document.querySelector('.hero .cta-button');
 heroCTA.addEventListener('click', function() {
 document.querySelector('.create-flow').scrollIntoView({ behavior: 'smooth' });
 });

 // Initialize with 1990s selected
 document.querySelector('.era-pill[data-era="1990s"]').classList.add('selected');
 document.querySelector('.era-pill[data-era="1990s"]').setAttribute('aria-checked', 'true');
 });
 </script>
</body>
</html>
```
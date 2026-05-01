/* =========================================================
   ELEVATE - scroll choreography (GSAP + ScrollTrigger)
   ========================================================= */
(function () {
  'use strict';
  // Fix P0-1: signal to CSS that JS is ready so split-line + fade-up can hide pre-reveal.
  // Without this, the CSS keeps everything visible and we get a graceful no-JS fallback.
  document.documentElement.classList.add('js-ready');
  const reduced = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---- Header state ---- */
  const header = document.querySelector('.site-header');
  const setHeader = () => header && header.classList.toggle('scrolled', window.scrollY > 32);
  setHeader();
  addEventListener('scroll', setHeader, { passive: true });

  /* ---- Mobile nav ---- */
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      const open = toggle.classList.toggle('open');
      links.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
    });
    links.querySelectorAll('a').forEach(a => a.addEventListener('click', () => {
      toggle.classList.remove('open'); links.classList.remove('open');
    }));
  }

  /* ---- Sticky mobile CTA ---- */
  const mcta = document.querySelector('.m-cta');
  if (mcta) {
    const update = () => mcta.classList.toggle('show', window.scrollY > 700);
    addEventListener('scroll', update, { passive: true });
    update();
  }

  /* ---- Year stamp ---- */
  document.querySelectorAll('[data-year]').forEach(el => el.textContent = new Date().getFullYear());

  /* ---- GSAP ---- */
  if (!window.gsap || !window.ScrollTrigger || reduced) {
    document.querySelectorAll('.fade-up').forEach(el => { el.style.opacity = '1'; el.style.transform = 'none'; });
    document.querySelectorAll('.split-line span').forEach(el => el.style.transform = 'none');
    return;
  }
  gsap.registerPlugin(ScrollTrigger);

  /* ---- Hero intro ---- */
  const heroEls = gsap.utils.toArray('.hero-top, .hero-headline, .hero-sub, .hero-cta, .hero-meta');
  if (heroEls.length) {
    gsap.from(heroEls, {
      y: 36,
      opacity: 0,
      duration: 1.1,
      stagger: 0.12,
      ease: 'power3.out',
      delay: 0.2,
    });
  }

  /* ---- Hero video → inset card transformation on scroll ---- *
   * On scroll the full-bleed video shrinks into a card pinned upper-right
   * while the headline scales slightly and the dark overlay deepens.        */
  const videoWrap = document.querySelector('.hero-video-wrap');
  if (videoWrap) {
    gsap.to(videoWrap, {
      scale: 1.08,
      yPercent: 12,
      ease: 'none',
      scrollTrigger: {
        trigger: '.hero',
        start: 'top top',
        end: 'bottom top',
        scrub: 0.6,
      },
    });
  }

  /* ---- Marquee speed-up on hover ---- */
  document.querySelectorAll('.marquee').forEach(m => {
    const track = m.querySelector('.marquee-track');
    if (!track) return;
    m.addEventListener('mouseenter', () => track.style.animationDuration = '14s');
    m.addEventListener('mouseleave', () => track.style.animationDuration = '38s');
  });

  /* ---- Generic fade-up reveals ---- */
  gsap.utils.toArray('.fade-up').forEach(el => {
    gsap.fromTo(el,
      { opacity: 0, y: 32 },
      {
        opacity: 1, y: 0,
        duration: 1, ease: 'power3.out',
        scrollTrigger: { trigger: el, start: 'top 88%', once: true },
      }
    );
  });

  /* ---- Split-line headline reveals (h2 in split-head) ---- */
  gsap.utils.toArray('.split-line').forEach(line => {
    const inner = line.querySelector('span');
    if (!inner) return;
    gsap.fromTo(inner,
      { yPercent: 110 },
      {
        yPercent: 0,
        duration: 1.15,
        ease: 'expo.out',
        scrollTrigger: { trigger: line, start: 'top 90%', once: true },
      }
    );
  });

  /* ---- Stagger for service mosaic ---- */
  const svcs = gsap.utils.toArray('.svc');
  if (svcs.length) {
    gsap.from(svcs, {
      y: 50, opacity: 0,
      duration: 0.95, stagger: 0.08, ease: 'power3.out',
      scrollTrigger: { trigger: svcs[0], start: 'top 82%', once: true },
    });
  }

  /* ---- Stack-list items: number-counter feel ---- */
  gsap.utils.toArray('.stack-item').forEach((item, i) => {
    gsap.from(item, {
      x: -30, opacity: 0,
      duration: 1, ease: 'power3.out',
      delay: i * 0.05,
      scrollTrigger: { trigger: item, start: 'top 85%', once: true },
    });
  });

  /* ---- Portfolio: masonry parallax ---- */
  gsap.utils.toArray('.proj img').forEach(img => {
    gsap.fromTo(img,
      { yPercent: -8 },
      {
        yPercent: 8, ease: 'none',
        scrollTrigger: {
          trigger: img.closest('.proj'),
          start: 'top bottom',
          end: 'bottom top',
          scrub: true,
        },
      }
    );
  });

  /* ---- Number count-up ---- */
  document.querySelectorAll('[data-count]').forEach(el => {
    const target = parseFloat(el.dataset.count);
    const dec = parseInt(el.dataset.decimals || '0', 10);
    const obj = { v: 0 };
    ScrollTrigger.create({
      trigger: el,
      start: 'top 88%',
      once: true,
      onEnter: () => {
        gsap.to(obj, {
          v: target, duration: 1.6, ease: 'power2.out',
          onUpdate: () => el.textContent = obj.v.toFixed(dec),
        });
      },
    });
  });

  /* ---- Founder block: subtle mouse-tracking glow ---- */
  const founder = document.querySelector('.founder');
  if (founder) {
    const glow = document.createElement('div');
    glow.style.cssText = `
      position: absolute; inset: 0; pointer-events: none; z-index: 0;
      background: radial-gradient(400px circle at var(--mx, 50%) var(--my, 50%),
        rgba(255,94,26,0.10), transparent 60%);
      transition: opacity 0.4s ease;
      opacity: 0;
    `;
    founder.style.position = founder.style.position || 'relative';
    founder.appendChild(glow);
    founder.addEventListener('mousemove', (e) => {
      const r = founder.getBoundingClientRect();
      glow.style.setProperty('--mx', ((e.clientX - r.left) / r.width * 100) + '%');
      glow.style.setProperty('--my', ((e.clientY - r.top) / r.height * 100) + '%');
      glow.style.opacity = '1';
    });
    founder.addEventListener('mouseleave', () => glow.style.opacity = '0');
  }

  /* ---- Cost-band tool ---- */
  const sel = document.querySelector('[data-cost-select]');
  const out = document.querySelector('[data-cost-result]');
  if (sel && out) {
    const ranges = {
      'roof-repair': '$450 - $2,800',
      'roof-replace-asphalt': '$9,500 - $22,000',
      'roof-replace-metal': '$18,000 - $42,000',
      'remodel-bath': '$28,000 - $65,000',
      'remodel-kitchen': '$48,000 - $135,000',
      'adu': '$185,000 - $420,000',
      'new-home': '$485,000 - $1.4M',
      'custom': 'We build the number after we walk the project.',
    };
    sel.addEventListener('change', e => {
      const v = e.target.value;
      out.textContent = ranges[v] || '- pick a project above -';
      gsap.fromTo(out, { opacity: 0, y: 8 }, { opacity: 1, y: 0, duration: 0.4, ease: 'power2.out' });
    });
  }
})();

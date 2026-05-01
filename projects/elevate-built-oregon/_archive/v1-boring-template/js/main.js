/* =========================================================
   Elevate Roofing & Construction — Interactivity
   GSAP + ScrollTrigger required (loaded from CDN in HTML)
   ========================================================= */

(function () {
  'use strict';

  const reduceMotion = window.matchMedia('(prefers-reduced-motion: reduce)').matches;

  /* ---------- Header scroll state ---------- */
  const header = document.querySelector('.site-header');
  const setHeader = () => {
    if (!header) return;
    header.classList.toggle('scrolled', window.scrollY > 24);
  };
  setHeader();
  window.addEventListener('scroll', setHeader, { passive: true });

  /* ---------- Mobile nav ---------- */
  const toggle = document.querySelector('.nav-toggle');
  const links = document.querySelector('.nav-links');
  if (toggle && links) {
    toggle.addEventListener('click', () => {
      const open = toggle.classList.toggle('open');
      links.classList.toggle('open', open);
      toggle.setAttribute('aria-expanded', String(open));
    });
    links.querySelectorAll('a').forEach(a => {
      a.addEventListener('click', () => {
        toggle.classList.remove('open');
        links.classList.remove('open');
      });
    });
  }

  /* ---------- Sticky mobile CTA visibility ---------- */
  const mobileCta = document.querySelector('.mobile-cta');
  if (mobileCta) {
    const showAfter = 600;
    const onScroll = () => {
      mobileCta.classList.toggle('visible', window.scrollY > showAfter);
    };
    window.addEventListener('scroll', onScroll, { passive: true });
    onScroll();
  }

  /* ---------- GSAP scroll animations ---------- */
  if (window.gsap && window.ScrollTrigger && !reduceMotion) {
    gsap.registerPlugin(ScrollTrigger);

    // Set initial state for all fade-up elements
    gsap.utils.toArray('.fade-up').forEach(el => {
      gsap.fromTo(el,
        { opacity: 0, y: 28 },
        {
          opacity: 1,
          y: 0,
          duration: 0.9,
          ease: 'power3.out',
          scrollTrigger: {
            trigger: el,
            start: 'top 88%',
            once: true,
          },
        }
      );
    });

    // Hero text intro
    const heroEls = gsap.utils.toArray('.hero .hero-eyebrow, .hero h1, .hero-sub, .hero-meta, .hero-cta');
    if (heroEls.length) {
      gsap.from(heroEls, {
        y: 32,
        opacity: 0,
        duration: 1,
        stagger: 0.12,
        ease: 'power3.out',
        delay: 0.15,
      });
    }

    // Hero parallax (subtle)
    const heroBg = document.querySelector('.hero-bg');
    if (heroBg) {
      gsap.to(heroBg, {
        yPercent: 18,
        ease: 'none',
        scrollTrigger: {
          trigger: '.hero',
          start: 'top top',
          end: 'bottom top',
          scrub: true,
        },
      });
    }

    // Count-up for trust strip + pitch stats
    document.querySelectorAll('[data-count]').forEach(el => {
      const target = parseFloat(el.dataset.count);
      const decimals = parseInt(el.dataset.decimals || '0', 10);
      const obj = { val: 0 };
      ScrollTrigger.create({
        trigger: el,
        start: 'top 90%',
        once: true,
        onEnter: () => {
          gsap.to(obj, {
            val: target,
            duration: 1.4,
            ease: 'power2.out',
            onUpdate: () => {
              el.textContent = obj.val.toFixed(decimals);
            },
          });
        },
      });
    });

    // Service card stagger reveal
    const cards = gsap.utils.toArray('.service-card');
    if (cards.length) {
      gsap.from(cards, {
        y: 40,
        opacity: 0,
        duration: 0.8,
        stagger: 0.1,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: cards[0],
          start: 'top 85%',
          once: true,
        },
      });
    }

    // Portfolio cards reveal
    const portfolio = gsap.utils.toArray('.portfolio-card');
    if (portfolio.length) {
      gsap.from(portfolio, {
        y: 50,
        opacity: 0,
        duration: 0.9,
        stagger: 0.12,
        ease: 'power3.out',
        scrollTrigger: {
          trigger: portfolio[0],
          start: 'top 80%',
          once: true,
        },
      });
    }
  } else {
    // Reduced motion fallback — just reveal everything
    document.querySelectorAll('.fade-up').forEach(el => {
      el.style.opacity = '1';
      el.style.transform = 'none';
    });
  }

  /* ---------- Cost-band tool ---------- */
  const costSelect = document.querySelector('[data-cost-select]');
  const costResult = document.querySelector('[data-cost-result]');
  if (costSelect && costResult) {
    const ranges = {
      'roof-repair': '$450 – $2,800',
      'roof-replace-asphalt': '$9,500 – $22,000',
      'roof-replace-metal': '$18,000 – $42,000',
      'remodel-bath': '$28,000 – $65,000',
      'remodel-kitchen': '$48,000 – $135,000',
      'adu': '$185,000 – $420,000',
      'new-home': '$485,000 – $1.4M',
      'custom': 'We build the number after we walk the project.',
    };
    costSelect.addEventListener('change', e => {
      const v = e.target.value;
      costResult.textContent = ranges[v] || '—';
      costResult.classList.add('shown');
    });
  }

  /* ---------- Year in footer ---------- */
  document.querySelectorAll('[data-year]').forEach(el => {
    el.textContent = new Date().getFullYear();
  });

})();

"use client"

/**
 * ScrollReveal: agentsHQ Compiled Craft
 *
 * General-purpose scroll-triggered reveal for non-headline content.
 * Less dramatic than KineticText: use for supporting content, cards,
 * images, and body copy sections, not for headlines.
 *
 * USAGE:
 *   import { ScrollReveal } from "@/components/craft/ScrollReveal"
 *
 *   // Single element reveal:
 *   <ScrollReveal>
 *     <p className="body-copy">Supporting content here.</p>
 *   </ScrollReveal>
 *
 *   // Staggered card grid (delay each card):
 *   {cards.map((card, i) => (
 *     <ScrollReveal key={card.id} delay={i * 0.1}>
 *       <Card {...card} />
 *     </ScrollReveal>
 *   ))}
 *
 *   // Slide in from the left:
 *   <ScrollReveal from="left">
 *     <FeatureBlock />
 *   </ScrollReveal>
 *
 * FROM DIRECTIONS:
 *   "bottom": standard content entry (default). Translates up into position.
 *   "left"  : slides in from left. Use for alternating layout sections.
 *   "right" : slides in from right.
 *   "fade"  : opacity only, no translation. Use for full-width elements.
 *
 * CHOREOGRAPHY RULE: Motion must reinforce hierarchy.
 *   - Hero headlines: use KineticText
 *   - Supporting headings: use ScrollReveal with from="bottom"
 *   - Body copy blocks: use ScrollReveal with from="fade" or from="bottom"
 *   - Card grids: use ScrollReveal with staggered delay (0, 0.1, 0.2)
 *   - Navigation: NO animation: must already be visible
 *
 * DEPENDENCIES: gsap, gsap/ScrollTrigger
 *   npm install gsap
 */

import { useEffect, useRef } from "react"
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"

gsap.registerPlugin(ScrollTrigger)

type RevealDirection = "bottom" | "left" | "right" | "fade"

interface ScrollRevealProps {
  children: React.ReactNode
  /** Direction the element enters from. Default "bottom". */
  from?: RevealDirection
  /** Delay in seconds. Use for staggering sibling elements. Default 0. */
  delay?: number
  /** Override the trigger threshold. Default "top 85%". */
  triggerPoint?: string
  className?: string
}

const FROM_VARIANTS: Record<RevealDirection, gsap.TweenVars> = {
  bottom: { y: 40, opacity: 0 },
  left:   { x: -40, opacity: 0 },
  right:  { x: 40, opacity: 0 },
  fade:   { opacity: 0 },
}

export function ScrollReveal({
  children,
  from = "bottom",
  delay = 0,
  triggerPoint = "top 85%",
  className,
}: ScrollRevealProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches

    if (prefersReducedMotion) return

    const animation = gsap.from(el, {
      ...FROM_VARIANTS[from],
      duration: 0.6,                // --duration-slow equivalent
      delay,
      ease: "power2.out",           // GSAP_EASE.standard: not ease-in-out
      scrollTrigger: {
        trigger: el,
        start: triggerPoint,
        toggleActions: "play none none none", // plays once, does not reverse
      },
    })

    return () => {
      animation.scrollTrigger?.kill()
      animation.kill()
    }
  }, [from, delay, triggerPoint])

  return (
    <div ref={ref} className={className}>
      {children}
    </div>
  )
}

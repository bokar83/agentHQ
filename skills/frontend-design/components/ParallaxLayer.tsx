"use client"

/**
 * ParallaxLayer: agentsHQ Compiled Craft
 *
 * Wraps any element to apply a scroll-driven parallax offset. Uses GSAP
 * ScrollTrigger for frame-perfect Lenis compatibility. Always uses
 * translate3d for GPU-composited rendering (no layout reflow).
 *
 * USAGE:
 *   import { ParallaxLayer } from "@/components/craft/ParallaxLayer"
 *
 *   // Background image layer (slowest):
 *   <ParallaxLayer speed={0.3} className="absolute inset-0">
 *     <Image src="/hero-bg.jpg" fill alt="" />
 *   </ParallaxLayer>
 *
 *   // Midground decorative element:
 *   <ParallaxLayer speed={0.6}>
 *     <div className="some-floating-element" />
 *   </ParallaxLayer>
 *
 * SPEED GUIDE:
 *   0.2-0.4: background layer (furthest back, moves least)
 *   0.5-0.7: midground layer
 *   1.1-1.3: foreground layer (in front of content, moves most)
 *   Never apply speed > 0.3 to text elements: legibility degrades.
 *
 * PERFORMANCE RULES enforced by this component:
 *   - Only animates transform (never top/left/margin: avoids layout reflow)
 *   - Uses will-change: transform for GPU layer promotion
 *   - Respects prefers-reduced-motion
 *
 * DEPENDENCIES: gsap, gsap/ScrollTrigger
 *   npm install gsap
 */

import { useEffect, useRef } from "react"
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"

gsap.registerPlugin(ScrollTrigger)

interface ParallaxLayerProps {
  children: React.ReactNode
  /**
   * Parallax speed multiplier.
   * 0.2-0.4 = background, 0.5-0.7 = midground, 1.1-1.3 = foreground.
   * Default 0.3.
   */
  speed?: number
  className?: string
}

export function ParallaxLayer({
  children,
  speed = 0.3,
  className,
}: ParallaxLayerProps) {
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches

    if (prefersReducedMotion) return

    // The yPercent value creates a parallax offset relative to the element's height.
    // Negative value means the element moves upward as the user scrolls down.
    // scrub: 0.5 gives a half-second lag behind scroll position: responsive but smooth.
    const animation = gsap.to(el, {
      yPercent: -(speed * 30), // empirically tuned: speed 0.3 = 9% vertical travel
      ease: "none",            // linear scrub: easing is applied by Lenis
      scrollTrigger: {
        trigger: el,
        start: "top bottom",
        end: "bottom top",
        scrub: 0.5,
      },
    })

    return () => {
      animation.scrollTrigger?.kill()
      animation.kill()
    }
  }, [speed])

  return (
    <div
      ref={ref}
      className={className}
      style={{ willChange: "transform" }}
    >
      {children}
    </div>
  )
}

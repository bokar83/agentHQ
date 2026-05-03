"use client"

/**
 * KineticText: agentsHQ Compiled Craft
 *
 * Splits text into characters or words and applies a staggered reveal
 * on scroll entry. The motionStyle prop selects the archetype-specific
 * animation character. Respects prefers-reduced-motion with a graceful
 * CSS-only fallback.
 *
 * USAGE:
 *   import { KineticText } from "@/components/craft/KineticText"
 *
 *   // Hero headline (Calm Product archetype):
 *   <KineticText as="h1" motionStyle="calm" className="text-5xl font-bold">
 *     Your headline here
 *   </KineticText>
 *
 *   // Cinematic hero:
 *   <KineticText as="h1" motionStyle="cinematic" className="text-display">
 *     Your headline here
 *   </KineticText>
 *
 * MOTION STYLES by archetype:
 *   "calm"     : CALM_PRODUCT, DOCUMENTARY_DATA, TRUST_ENTERPRISE (hero only)
 *   "editorial": EDITORIAL_NARRATIVE (word-by-word reveal)
 *   "cinematic": CINEMATIC_AGENCY (rotationX, dramatic stagger)
 *   "playful"  : ILLUSTRATIVE_PLAYFUL (scale + bounce)
 *
 * FALLBACK: If SplitText fails to register (missing GSAP Club license or
 * network error), the component renders with a CSS-only fade+translateY
 * using --ease-out-expo and --duration-slow from craft-tokens.css.
 *
 * DEPENDENCIES: gsap, gsap/SplitText, gsap/ScrollTrigger
 *   npm install gsap
 *   Note: SplitText is free as of GSAP 3.12+ (post-Webflow acquisition).
 *   Verify at https://gsap.com/pricing/ if licensing questions arise.
 */

import { useEffect, useRef, useState, JSX } from "react"
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"

gsap.registerPlugin(ScrollTrigger)

export type MotionStyle = "calm" | "editorial" | "cinematic" | "playful"

interface KineticTextProps {
  children: string
  as?: keyof JSX.IntrinsicElements
  motionStyle?: MotionStyle
  className?: string
  /** Delay before animation fires (seconds). Use for staggered siblings. */
  delay?: number
}

// Animation configurations per motionStyle
const MOTION_CONFIG: Record<MotionStyle, {
  splitType: "chars,words" | "words,lines"
  unitKey: "chars" | "words"
  from: gsap.TweenVars
  duration: number
  stagger: number
  ease: string
}> = {
  calm: {
    splitType: "chars,words",
    unitKey: "chars",
    from: { y: 20, opacity: 0 },
    duration: 0.5,
    stagger: 0.015,
    ease: "power2.out",
  },
  editorial: {
    splitType: "words,lines",
    unitKey: "words",
    from: { y: 30, opacity: 0 },
    duration: 0.7,
    stagger: 0.04,
    ease: "power2.out",
  },
  cinematic: {
    splitType: "chars,words",
    unitKey: "chars",
    from: { y: 60, opacity: 0, rotationX: -90, transformOrigin: "50% 50% -30px" },
    duration: 0.8,
    stagger: 0.03,
    ease: "expo.out",
  },
  playful: {
    splitType: "chars,words",
    unitKey: "chars",
    from: { y: 40, opacity: 0, scale: 0.8 },
    duration: 0.6,
    stagger: 0.02,
    ease: "back.out(1.7)",
  },
}

export function KineticText({
  children,
  as: Tag = "h1",
  motionStyle = "calm",
  className,
  delay = 0,
}: KineticTextProps) {
  const ref = useRef<HTMLElement>(null)
  const [splitTextAvailable, setSplitTextAvailable] = useState(false)

  // Check if SplitText plugin is available
  useEffect(() => {
    const checkSplitText = async () => {
      try {
        const { SplitText } = await import("gsap/SplitText")
        gsap.registerPlugin(SplitText)
        setSplitTextAvailable(true)
      } catch {
        // SplitText not available: CSS fallback will handle animation
        setSplitTextAvailable(false)
      }
    }
    checkSplitText()
  }, [])

  useEffect(() => {
    const el = ref.current
    if (!el) return

    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches

    if (prefersReducedMotion) return

    if (!splitTextAvailable) {
      // CSS fallback: simple opacity + translateY using craft token values
      el.style.opacity = "0"
      el.style.transform = "translateY(20px)"
      el.style.transition = `opacity var(--duration-slow) var(--ease-out-expo) ${delay}s, transform var(--duration-slow) var(--ease-out-expo) ${delay}s`

      const observer = new IntersectionObserver(
        ([entry]) => {
          if (entry.isIntersecting) {
            el.style.opacity = "1"
            el.style.transform = "translateY(0)"
            observer.disconnect()
          }
        },
        { threshold: 0.1 }
      )
      observer.observe(el)
      return () => observer.disconnect()
    }

    // SplitText animation path
    let split: { chars: Element[]; words: Element[]; revert: () => void } | null = null

    const setupAnimation = async () => {
      try {
        const { SplitText } = await import("gsap/SplitText")
        const config = MOTION_CONFIG[motionStyle]

        split = new SplitText(el, { type: config.splitType })
        const units = split[config.unitKey] as Element[]

        gsap.from(units, {
          ...config.from,
          duration: config.duration,
          stagger: config.stagger,
          ease: config.ease,
          delay,
          scrollTrigger: {
            trigger: el,
            start: "top 85%",
            toggleActions: "play none none none",
          },
        })
      } catch {
        // If import fails at animation time, the el is already visible (no opacity:0 set)
      }
    }

    setupAnimation()

    return () => {
      // Revert SplitText on unmount to restore original DOM before any reflow
      if (split) {
        try {
          split.revert()
        } catch {
          // Ignore revert errors
        }
      }
    }
  }, [motionStyle, delay, splitTextAvailable])

  // @ts-expect-error: dynamic tag from string
  return <Tag ref={ref} className={className}>{children}</Tag>
}

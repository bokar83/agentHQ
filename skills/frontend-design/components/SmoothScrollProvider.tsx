"use client"

/**
 * SmoothScrollProvider: agentsHQ Compiled Craft
 *
 * Wraps the application root. Configures Lenis smooth scroll and
 * registers the GSAP ScrollTrigger proxy so ScrollTrigger works
 * correctly with Lenis's virtual scroll position.
 *
 * USAGE (in src/app/layout.tsx):
 *   import { SmoothScrollProvider } from "@/components/craft/SmoothScrollProvider"
 *
 *   export default function RootLayout({ children }) {
 *     return (
 *       <html>
 *         <body>
 *           <SmoothScrollProvider lerp={0.07}>
 *             {children}
 *           </SmoothScrollProvider>
 *         </body>
 *       </html>
 *     )
 *   }
 *
 * ARCHETYPE LERP VALUES (pass as the lerp prop):
 *   EDITORIAL_NARRATIVE:  0.05
 *   CINEMATIC_AGENCY:     0.05
 *   DOCUMENTARY_DATA:     0.07  (default)
 *   CALM_PRODUCT:         0.10
 *   ILLUSTRATIVE_PLAYFUL: 0.10
 *   CONVERSION_FIRST:     0.10
 *   BRUTALIST:            do NOT use this component
 *   TRUST_ENTERPRISE:     do NOT use this component
 *
 * DEPENDENCIES: lenis, gsap, gsap/ScrollTrigger
 *   npm install lenis gsap
 */

import { useEffect, useRef } from "react"
import Lenis from "lenis"
import { gsap } from "gsap"
import { ScrollTrigger } from "gsap/ScrollTrigger"

gsap.registerPlugin(ScrollTrigger)

interface SmoothScrollProviderProps {
  children: React.ReactNode
  /** Lenis lerp value. Lower = slower/more cinematic. Default 0.07. */
  lerp?: number
  /** Wheel speed multiplier. Default 1.2. */
  wheelMultiplier?: number
}

export function SmoothScrollProvider({
  children,
  lerp = 0.07,
  wheelMultiplier = 1.2,
}: SmoothScrollProviderProps) {
  const lenisRef = useRef<Lenis | null>(null)

  useEffect(() => {
    // Respect prefers-reduced-motion: disable smooth scroll for accessibility
    const prefersReducedMotion = window.matchMedia(
      "(prefers-reduced-motion: reduce)"
    ).matches

    if (prefersReducedMotion) return

    const lenis = new Lenis({
      lerp,
      wheelMultiplier,
      smoothTouch: false, // native touch scroll feels better on mobile
    })

    lenisRef.current = lenis

    // Keep ScrollTrigger in sync with Lenis virtual scroll position
    lenis.on("scroll", ScrollTrigger.update)

    // Drive Lenis from GSAP's ticker for frame-perfect synchronization
    const gsapTickerCallback = (time: number) => {
      lenis.raf(time * 1000)
    }

    gsap.ticker.add(gsapTickerCallback)
    gsap.ticker.lagSmoothing(0) // prevents large jumps after tab switch

    return () => {
      lenis.destroy()
      gsap.ticker.remove(gsapTickerCallback)
    }
  }, [lerp, wheelMultiplier])

  return <>{children}</>
}

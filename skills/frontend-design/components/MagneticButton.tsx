"use client"

/**
 * MagneticButton: agentsHQ Compiled Craft
 *
 * A button with cursor-tracking magnetic hover effect and a tactile
 * spring press. The spring values are hardcoded to research-derived
 * constants. No generic "transition: all 0.3s ease".
 *
 * USAGE:
 *   import { MagneticButton } from "@/components/craft/MagneticButton"
 *
 *   // Primary CTA:
 *   <MagneticButton
 *     className="bg-brand-primary text-white px-8 py-4 rounded-[var(--radius-sm)]"
 *     onClick={() => router.push("/contact")}
 *   >
 *     Get started
 *   </MagneticButton>
 *
 *   // Subtle variant (less magnetic pull):
 *   <MagneticButton strength={0.1} className="...">
 *     Learn more
 *   </MagneticButton>
 *
 * STRENGTH GUIDE:
 *   0.1: subtle, almost imperceptible. Use for secondary actions.
 *   0.2: default. Noticeable but not distracting. Primary CTAs.
 *   0.3: dramatic. Use for hero CTAs or portfolio work buttons.
 *   0.4: very dramatic. Use only in CINEMATIC_AGENCY archetype.
 *
 * NOTE: Wrap in a container with sufficient padding to allow the magnetic
 * offset range without clipping. overflow:hidden on a parent will cut
 * the magnetic movement.
 *
 * DEPENDENCIES: framer-motion
 *   npm install framer-motion
 */

import { useRef, useState } from "react"
import { motion, useSpring } from "framer-motion"

interface MagneticButtonProps {
  children: React.ReactNode
  className?: string
  onClick?: () => void
  type?: "button" | "submit" | "reset"
  disabled?: boolean
  /** Magnetic pull strength. 0.2 default. Range 0.1-0.4. */
  strength?: number
  /** aria-label for accessibility. Required when button contains only an icon. */
  "aria-label"?: string
}

export function MagneticButton({
  children,
  className,
  onClick,
  type = "button",
  disabled = false,
  strength = 0.2,
  "aria-label": ariaLabel,
}: MagneticButtonProps) {
  const ref = useRef<HTMLButtonElement>(null)
  const [position, setPosition] = useState({ x: 0, y: 0 })

  // Spring configuration: responsive but not jittery
  // Lower stiffness = more "heavy" feel; higher = snappier
  const springConfig = { stiffness: 200, damping: 15, mass: 1 }
  const springX = useSpring(position.x, springConfig)
  const springY = useSpring(position.y, springConfig)

  const handleMouseMove = (e: React.MouseEvent<HTMLButtonElement>) => {
    if (disabled) return
    const rect = ref.current?.getBoundingClientRect()
    if (!rect) return

    const centerX = rect.left + rect.width / 2
    const centerY = rect.top + rect.height / 2

    setPosition({
      x: (e.clientX - centerX) * strength,
      y: (e.clientY - centerY) * strength,
    })
  }

  const handleMouseLeave = () => {
    setPosition({ x: 0, y: 0 })
  }

  return (
    <motion.button
      ref={ref}
      type={type}
      className={className}
      onClick={onClick}
      disabled={disabled}
      onMouseMove={handleMouseMove}
      onMouseLeave={handleMouseLeave}
      style={{ x: springX, y: springY }}
      whileTap={{
        scale: 0.96,
        transition: {
          type: "spring",
          stiffness: 400,
          damping: 30,
          mass: 1,
        },
      }}
      aria-label={ariaLabel}
    >
      {children}
    </motion.button>
  )
}

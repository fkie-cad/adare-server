// Single source of truth for the categorical brand-accent system. Each entity
// type maps to one of the five logo hues, reused across the home stat cards,
// the login welcome-card stats, and anywhere else entities are color-coded so
// assignment stays consistent app-wide. Teal (--color-primary) stays the
// interactive color and is deliberately not in this map.
//
// Class strings are written out in full so Tailwind's source scan picks them up.

export interface BrandAccent {
  /** Icon stroke color (lucide icons inherit `currentColor`). */
  icon: string
  /** Text color for numbers / labels. */
  text: string
  /** Soft tinted fill for chips and backgrounds. */
  tint: string
  /** Border color for thin accent rules. */
  border: string
}

export const brandAccents = {
  cyan: {
    icon: 'text-brand-cyan',
    text: 'text-brand-cyan',
    tint: 'bg-brand-cyan/15',
    border: 'border-brand-cyan',
  },
  lime: {
    icon: 'text-brand-lime',
    text: 'text-brand-lime',
    tint: 'bg-brand-lime/15',
    border: 'border-brand-lime',
  },
  orange: {
    icon: 'text-brand-orange',
    text: 'text-brand-orange',
    tint: 'bg-brand-orange/15',
    border: 'border-brand-orange',
  },
  magenta: {
    icon: 'text-brand-magenta',
    text: 'text-brand-magenta',
    tint: 'bg-brand-magenta/15',
    border: 'border-brand-magenta',
  },
  purple: {
    icon: 'text-brand-purple',
    text: 'text-brand-purple',
    tint: 'bg-brand-purple/15',
    border: 'border-brand-purple',
  },
} as const satisfies Record<string, BrandAccent>

export type BrandAccentKey = keyof typeof brandAccents

/** Entity type → accent. Keyed by lowercase singular entity name. */
export const entityAccents = {
  experiment: brandAccents.magenta,
  environment: brandAccents.cyan,
  testfunctionset: brandAccents.purple,
  run: brandAccents.orange,
  request: brandAccents.lime,
  user: brandAccents.cyan,
} as const satisfies Record<string, BrandAccent>

export type EntityKey = keyof typeof entityAccents

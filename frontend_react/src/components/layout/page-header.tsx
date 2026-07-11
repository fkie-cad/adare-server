import * as React from 'react'
import { cn } from '@/lib/utils'

interface PageHeaderProps extends Omit<React.HTMLAttributes<HTMLDivElement>, 'title'> {
  /** Small uppercase mono label above the title — the "instrument channel". */
  eyebrow?: React.ReactNode
  title: React.ReactNode
  description?: React.ReactNode
  /** Right-aligned actions (buttons, links). */
  actions?: React.ReactNode
}

/**
 * Standard page title block. Space-Grotesk title, optional mono eyebrow and a
 * teal hairline accent — replaces the ad-hoc <h1>/<h2> each page invented.
 */
export function PageHeader({
  eyebrow,
  title,
  description,
  actions,
  className,
  ...props
}: PageHeaderProps) {
  return (
    <div className={cn('mb-6 flex items-start justify-between gap-4', className)} {...props}>
      <div className="min-w-0">
        {eyebrow && (
          <div className="mb-1 flex items-center gap-2 font-mono text-xs uppercase tracking-widest text-muted-foreground">
            <span className="h-px w-4 bg-primary" aria-hidden />
            {eyebrow}
          </div>
        )}
        <h1 className="font-display text-3xl font-semibold leading-tight tracking-tight text-foreground">
          {title}
        </h1>
        {description && (
          <p className="mt-1.5 max-w-2xl text-sm text-muted-foreground">{description}</p>
        )}
      </div>
      {actions && <div className="flex shrink-0 items-center gap-2">{actions}</div>}
    </div>
  )
}

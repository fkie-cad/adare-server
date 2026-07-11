import * as React from 'react'
import { cn } from '@/lib/utils'

/**
 * Consistent width + padding for content pages. Full-bleed list/sidebar pages
 * keep their own shell and don't use this.
 */
export function PageContainer({
  className,
  ...props
}: React.HTMLAttributes<HTMLDivElement>) {
  return <div className={cn('mx-auto max-w-7xl px-6 py-6', className)} {...props} />
}

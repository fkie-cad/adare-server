import * as React from 'react'
import { createPortal } from 'react-dom'
import { cn } from '@/lib/utils'

interface TooltipProps {
  content: React.ReactNode
  children: React.ReactElement
  side?: 'top' | 'bottom' | 'left' | 'right'
}

export function Tooltip({ content, children, side = 'top' }: TooltipProps) {
  const [open, setOpen] = React.useState(false)
  const triggerRef = React.useRef<HTMLSpanElement>(null)
  const [position, setPosition] = React.useState({ top: 0, left: 0 })

  React.useEffect(() => {
    if (open && triggerRef.current) {
      const rect = triggerRef.current.getBoundingClientRect()
      switch (side) {
        case 'top':
          setPosition({
            top: rect.top + window.scrollY,
            left: rect.left + rect.width / 2 + window.scrollX,
          })
          break
        case 'bottom':
          setPosition({
            top: rect.bottom + window.scrollY,
            left: rect.left + rect.width / 2 + window.scrollX,
          })
          break
        case 'left':
          setPosition({
            top: rect.top + rect.height / 2 + window.scrollY,
            left: rect.left + window.scrollX,
          })
          break
        case 'right':
          setPosition({
            top: rect.top + rect.height / 2 + window.scrollY,
            left: rect.right + window.scrollX,
          })
          break
      }
    }
  }, [open, side])

  const positionStyles: Record<string, React.CSSProperties> = {
    top: { bottom: undefined, top: position.top, left: position.left, transform: 'translate(-50%, -100%) translateY(-8px)' },
    bottom: { top: position.top, left: position.left, transform: 'translate(-50%, 8px)' },
    left: { top: position.top, left: position.left, transform: 'translate(-100%, -50%) translateX(-8px)' },
    right: { top: position.top, left: position.left, transform: 'translate(8px, -50%)' },
  }

  return (
    <span
      ref={triggerRef}
      className="relative inline-flex"
      onMouseEnter={() => setOpen(true)}
      onMouseLeave={() => setOpen(false)}
    >
      {children}
      {open && content && createPortal(
        <span
          className={cn(
            'fixed z-50 rounded-md bg-primary px-3 py-1.5 text-xs text-primary-foreground shadow-md animate-in fade-in-0 whitespace-pre-line pointer-events-none',
          )}
          style={{
            ...positionStyles[side],
            position: 'absolute',
          }}
        >
          {content}
        </span>,
        document.body,
      )}
    </span>
  )
}

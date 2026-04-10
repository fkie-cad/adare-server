import { useState, useRef, useEffect } from 'react'
import { ChevronDown, Check } from 'lucide-react'
import { Button } from '@/components/ui/button'

interface DataTableSelectFilterProps {
  label: string
  options: string[]
  selected: string[]
  onChange: (selected: string[]) => void
}

export function DataTableSelectFilter({ label, options, selected, onChange }: DataTableSelectFilterProps) {
  const [open, setOpen] = useState(false)
  const ref = useRef<HTMLDivElement>(null)

  useEffect(() => {
    function handleClick(e: MouseEvent) {
      if (ref.current && !ref.current.contains(e.target as Node)) {
        setOpen(false)
      }
    }
    document.addEventListener('mousedown', handleClick)
    return () => document.removeEventListener('mousedown', handleClick)
  }, [])

  if (options.length === 0) return null

  function toggle(opt: string) {
    const next = selected.includes(opt)
      ? selected.filter((s) => s !== opt)
      : [...selected, opt]
    onChange(next)
  }

  return (
    <div className="relative" ref={ref}>
      <Button
        variant="outline"
        size="sm"
        onClick={() => setOpen(!open)}
        className="gap-1"
      >
        {label}
        {selected.length > 0 && (
          <span className="ml-1 rounded-full bg-primary text-primary-foreground text-xs px-1.5">
            {selected.length}
          </span>
        )}
        <ChevronDown className="h-3 w-3" />
      </Button>
      {open && (
        <div className="absolute left-0 top-full mt-1 bg-popover text-popover-foreground rounded-md shadow-lg border border-border p-1 min-w-48 z-50 max-h-60 overflow-y-auto">
          {options.map((opt) => (
            <button
              key={opt}
              onClick={() => toggle(opt)}
              className="flex items-center gap-2 w-full px-2 py-1.5 text-sm hover:bg-accent rounded text-left"
            >
              <span className="w-4 h-4 flex items-center justify-center">
                {selected.includes(opt) && <Check className="h-3 w-3" />}
              </span>
              {opt}
            </button>
          ))}
        </div>
      )}
    </div>
  )
}

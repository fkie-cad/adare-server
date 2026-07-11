import { Sun, Moon, Monitor } from 'lucide-react'
import { useThemeStore } from '@/stores/theme-store'
import { cn } from '@/lib/utils'

type Theme = 'light' | 'dark' | 'system'

const options: { value: Theme; icon: typeof Sun; label: string }[] = [
  { value: 'light', icon: Sun, label: 'Light' },
  { value: 'dark', icon: Moon, label: 'Dark' },
  { value: 'system', icon: Monitor, label: 'System' },
]

export function ThemeToggle() {
  const { theme, setTheme } = useThemeStore()

  return (
    <div className="flex gap-0.5 rounded-md bg-black/10 p-0.5">
      {options.map(({ value, icon: Icon, label }) => (
        <button
          key={value}
          onClick={() => setTheme(value)}
          className={cn(
            'rounded p-1.5 transition-colors',
            theme === value
              ? 'bg-background text-primary shadow-sm'
              : 'text-primary-foreground/70 hover:text-primary-foreground',
          )}
          title={label}
        >
          <Icon className="h-3.5 w-3.5" />
        </button>
      ))}
    </div>
  )
}

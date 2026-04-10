import { create } from 'zustand'

type Theme = 'light' | 'dark' | 'system'

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
}

function getSystemDark(): boolean {
  return window.matchMedia('(prefers-color-scheme: dark)').matches
}

function applyTheme(theme: Theme): void {
  const isDark = theme === 'dark' || (theme === 'system' && getSystemDark())
  document.documentElement.classList.toggle('dark', isDark)
}

export const useThemeStore = create<ThemeState>((set) => {
  const stored = (localStorage.getItem('adare-theme') as Theme | null) ?? 'system'
  applyTheme(stored)

  // Listen for OS preference changes when theme is 'system'
  const mq = window.matchMedia('(prefers-color-scheme: dark)')
  mq.addEventListener('change', () => {
    const current = useThemeStore.getState().theme
    if (current === 'system') {
      applyTheme('system')
    }
  })

  return {
    theme: stored,
    setTheme: (theme: Theme) => {
      localStorage.setItem('adare-theme', theme)
      applyTheme(theme)
      set({ theme })
    },
  }
})

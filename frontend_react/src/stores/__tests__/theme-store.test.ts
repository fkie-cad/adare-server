import { describe, it, expect, beforeEach } from 'vitest'
import { useThemeStore } from '../theme-store'

describe('theme-store', () => {
  beforeEach(() => {
    localStorage.clear()
    document.documentElement.classList.remove('dark')
    useThemeStore.setState({ theme: 'system' })
  })

  it('defaults to system theme', () => {
    const state = useThemeStore.getState()
    expect(state.theme).toBe('system')
  })

  it('sets theme to dark', () => {
    useThemeStore.getState().setTheme('dark')
    expect(useThemeStore.getState().theme).toBe('dark')
  })

  it('sets theme to light', () => {
    useThemeStore.getState().setTheme('light')
    expect(useThemeStore.getState().theme).toBe('light')
  })

  it('persists theme to localStorage', () => {
    useThemeStore.getState().setTheme('dark')
    expect(localStorage.getItem('adare-theme')).toBe('dark')
  })

  it('applies dark class when set to dark', () => {
    useThemeStore.getState().setTheme('dark')
    expect(document.documentElement.classList.contains('dark')).toBe(true)
  })

  it('removes dark class when set to light', () => {
    document.documentElement.classList.add('dark')
    useThemeStore.getState().setTheme('light')
    expect(document.documentElement.classList.contains('dark')).toBe(false)
  })

  it('cycles through all three values', () => {
    useThemeStore.getState().setTheme('light')
    expect(useThemeStore.getState().theme).toBe('light')

    useThemeStore.getState().setTheme('dark')
    expect(useThemeStore.getState().theme).toBe('dark')

    useThemeStore.getState().setTheme('system')
    expect(useThemeStore.getState().theme).toBe('system')
  })
})

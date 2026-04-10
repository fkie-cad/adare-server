import { useEffect } from 'react'
import { Outlet } from '@tanstack/react-router'
import { Header } from './header'
import { useAuthStore } from '@/stores/auth-store'
import { useThemeStore } from '@/stores/theme-store'

export function MainLayout() {
  const initLogin = useAuthStore((s) => s.initLogin)
  useThemeStore()

  useEffect(() => {
    initLogin()
  }, [initLogin])

  return (
    <div className="min-h-screen bg-background">
      <Header />
      <main className="px-4 py-4">
        <Outlet />
      </main>
    </div>
  )
}

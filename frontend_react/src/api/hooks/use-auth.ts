import { useMutation } from '@tanstack/react-query'
import { useNavigate } from '@tanstack/react-router'
import { api } from '@/api/client'
import { endpoints, FRONTEND_URL } from '@/api/endpoints'
import { useAuthStore } from '@/stores/auth-store'

export function useGiteaLogin() {
  return useMutation({
    mutationFn: async () => {
      const state =
        Math.random().toString(36).substring(2, 15) +
        Math.random().toString(36).substring(2, 15)

      const resp = await api.get(
        `${endpoints.authGiteaCallback}?redirect_uri=${FRONTEND_URL}login/oauth&state=${state}`,
      )

      localStorage.setItem('state', state)
      return resp.data.url as string
    },
    onSuccess: (url) => {
      window.location.assign(url)
    },
  })
}

export function useDevLogin() {
  const setLoginToken = useAuthStore((s) => s.setLoginToken)
  const navigate = useNavigate()

  return useMutation({
    mutationFn: async () => {
      const response = await api.post(endpoints.authDev)
      return response.data as { user: string; token: string; expiry: string }
    },
    onSuccess: (data) => {
      setLoginToken(data.user, data.token, data.expiry)
      navigate({ to: '/home' })
    },
  })
}

export function useOAuthCallback() {
  const setLoginToken = useAuthStore((s) => s.setLoginToken)

  return useMutation({
    mutationFn: async ({ code, state }: { code: string; state: string }) => {
      const formData = new FormData()
      formData.append('code', code)
      const response = await api.post(`${endpoints.authGitea}?state=${state}`, formData)
      return response.data as { user: string; token: string; expiry: string }
    },
    onSuccess: (data) => {
      setLoginToken(data.user, data.token, data.expiry)
    },
  })
}

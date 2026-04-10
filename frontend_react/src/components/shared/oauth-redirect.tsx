import { useEffect } from 'react'
import { useNavigate, useSearch } from '@tanstack/react-router'
import { Loader2 } from 'lucide-react'
import { useOAuthCallback } from '@/api/hooks/use-auth'

export function OauthRedirect() {
  const navigate = useNavigate()
  const search = useSearch({ strict: false }) as Record<string, string>
  const oauthCallback = useOAuthCallback()

  useEffect(() => {
    const state = search.state
    const code = search.code

    if (!state || !code) {
      navigate({ to: '/login' })
      return
    }

    if (state !== localStorage.getItem('state')) {
      navigate({ to: '/login' })
      return
    }

    oauthCallback.mutate(
      { code, state },
      {
        onSuccess: () => navigate({ to: '/profile' }),
        onError: () => navigate({ to: '/login' }),
      },
    )
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  return (
    <div className="flex flex-col items-center justify-center h-[60vh]">
      <Loader2 className="w-16 h-16 animate-spin text-primary" />
      <p className="mt-4 text-muted-foreground">Authenticating...</p>
    </div>
  )
}

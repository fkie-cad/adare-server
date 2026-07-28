import { useEffect, useState } from 'react'
import { Link, useNavigate, useSearch } from '@tanstack/react-router'
import { AlertCircle, Loader2 } from 'lucide-react'
import { useOAuthCallback } from '@/api/hooks/use-auth'
import { Alert, AlertDescription, AlertTitle } from '@/components/ui/alert'
import { Button } from '@/components/ui/button'

export function OauthRedirect() {
  const navigate = useNavigate()
  const search = useSearch({ strict: false }) as Record<string, string>
  const oauthCallback = useOAuthCallback()
  const [error, setError] = useState<string | null>(null)

  useEffect(() => {
    const state = search.state
    const code = search.code

    if (!state || !code) {
      setError('Missing authorization code or state in the callback URL.')
      return
    }

    if (state !== localStorage.getItem('state')) {
      setError('Authorization state did not match. Please start the login again.')
      return
    }

    oauthCallback.mutate(
      { code, state },
      {
        onSuccess: () => navigate({ to: '/home' }),
        onError: () =>
          setError('Sign-in with Gitea failed during the token exchange. Please try again.'),
      },
    )
  }, []) // eslint-disable-line react-hooks/exhaustive-deps

  if (error) {
    return (
      <div className="flex flex-col items-center justify-center h-[60vh] gap-4">
        <Alert variant="destructive" className="max-w-md">
          <AlertCircle className="h-4 w-4" />
          <AlertTitle>Login failed</AlertTitle>
          <AlertDescription>{error}</AlertDescription>
        </Alert>
        <Button asChild>
          <Link to="/login">Back to login</Link>
        </Button>
      </div>
    )
  }

  return (
    <div className="flex flex-col items-center justify-center h-[60vh]">
      <Loader2 className="w-16 h-16 animate-spin text-primary" />
      <p className="mt-4 text-muted-foreground">Authenticating...</p>
    </div>
  )
}

import { useNavigate } from '@tanstack/react-router'
import { UserCircle } from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import { useGiteaLogin, useDevLogin } from '@/api/hooks/use-auth'
import { Button } from '@/components/ui/button'
import { Card, CardContent, CardHeader } from '@/components/ui/card'
import { Alert, AlertDescription } from '@/components/ui/alert'

const isLocalhost = () =>
  window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1'

export function LoginForm() {
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn)
  const navigate = useNavigate()
  const giteaLogin = useGiteaLogin()
  const devLogin = useDevLogin()

  if (isLoggedIn) {
    navigate({ to: '/profile' })
    return null
  }

  return (
    <Card className="w-full max-w-md mx-auto">
      <CardHeader className="text-center">
        <h3 className="text-3xl font-bold">Sign In</h3>
        <div className="flex justify-center py-4">
          <UserCircle className="w-24 h-24 text-muted-foreground" />
        </div>
      </CardHeader>
      <CardContent className="space-y-4">
        {(giteaLogin.error || devLogin.error) && (
          <Alert variant="destructive">
            <AlertDescription>Something went wrong. Please try again later.</AlertDescription>
          </Alert>
        )}
        <Button
          size="lg"
          className="w-full bg-foreground text-background hover:bg-foreground/90"
          onClick={() => giteaLogin.mutate()}
          disabled={giteaLogin.isPending}
        >
          {giteaLogin.isPending ? 'Redirecting...' : 'Sign In with Gitea'}
        </Button>
        {isLocalhost() && (
          <>
            <div className="relative">
              <div className="absolute inset-0 flex items-center">
                <span className="w-full border-t" />
              </div>
              <div className="relative flex justify-center text-xs uppercase">
                <span className="bg-background px-2 text-muted-foreground">or</span>
              </div>
            </div>
            <Button
              size="lg"
              variant="outline"
              className="w-full"
              onClick={() => devLogin.mutate()}
              disabled={devLogin.isPending}
            >
              {devLogin.isPending ? 'Logging in...' : 'Dev Login'}
            </Button>
          </>
        )}
      </CardContent>
    </Card>
  )
}

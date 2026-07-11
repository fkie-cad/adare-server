import { LoginForm } from '@/components/shared/login-form'
import { WelcomeCard } from '@/components/shared/welcome-card'

export default function LoginPage() {
  return (
    <div className="flex min-h-[80vh] items-center justify-center px-4 py-8">
      <div className="flex w-full max-w-6xl flex-col items-center justify-evenly gap-8 md:flex-row md:items-center">
        <div className="w-full md:w-3/5">
          <WelcomeCard />
        </div>
        <div className="w-full md:w-2/5">
          <LoginForm />
        </div>
      </div>
    </div>
  )
}

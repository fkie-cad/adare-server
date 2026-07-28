import { Link, useNavigate } from '@tanstack/react-router'
import {
  Home,
  Play,
  FlaskConical,
  Mountain,
  GitPullRequest,
  Boxes,
  LogIn,
  User,
  LogOut,
  ChevronDown,
  Upload,
} from 'lucide-react'
import { useAuthStore } from '@/stores/auth-store'
import { useLoggedInUser } from '@/api/hooks/use-user'
import { ThemeToggle } from '@/components/ui/theme-toggle'

export function Header() {
  const isLoggedIn = useAuthStore((s) => s.isLoggedIn)

  return (
    <header className="border-b border-border bg-card">
      <div className="flex h-14 items-center px-4">
        <Link to="/home" className="mr-8 flex items-center">
          <img src="/logo.svg" alt="ADARE" className="h-8 w-8" />
        </Link>

        <nav className="flex gap-0.5">
          <NavTab to="/home" label="Home" icon={<Home className="h-4 w-4" />} />
          <NavTab to="/run" label="Runs" icon={<Play className="h-4 w-4" />} />
          <NavTab to="/experiment" label="Experiments" icon={<FlaskConical className="h-4 w-4" />} />
          <NavTab to="/environment" label="Environments" icon={<Mountain className="h-4 w-4" />} />
          <NavTab to="/request" label="Requests" icon={<GitPullRequest className="h-4 w-4" />} />
          <NavTab to="/testfunctionset" label="Testfunctionsets" icon={<Boxes className="h-4 w-4" />} />
          {isLoggedIn && <SubmitDropdown />}
        </nav>

        <div className="ml-auto flex items-center gap-2">
          <ThemeToggle />
          {!isLoggedIn ? (
            <Link
              to="/login"
              className="flex items-center gap-2 rounded-md bg-primary px-4 py-1.5 text-sm font-semibold text-primary-foreground transition-colors hover:bg-primary/90"
            >
              <LogIn className="h-4 w-4" />
              Login
            </Link>
          ) : (
            <UserMenu />
          )}
        </div>
      </div>
    </header>
  )
}

const navTabBase =
  'relative flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium text-muted-foreground transition-colors hover:bg-muted hover:text-foreground'
const navTabActive =
  'relative flex items-center gap-1.5 rounded-md px-3 py-2 text-sm font-medium text-foreground after:absolute after:inset-x-3 after:-bottom-px after:h-0.5 after:rounded-full after:bg-primary'

function NavTab({ to, label, icon }: { to: string; label: string; icon?: React.ReactNode }) {
  return (
    <Link to={to} className={navTabBase} activeProps={{ className: navTabActive }}>
      {icon}
      {label}
    </Link>
  )
}

function SubmitDropdown() {
  return (
    <div className="group relative">
      <button className={navTabBase}>
        <Upload className="h-4 w-4" />
        Submit
        <ChevronDown className="h-3 w-3" />
      </button>
      <div className="invisible absolute left-0 top-full z-50 mt-1 min-w-48 rounded-md border border-border bg-popover text-popover-foreground opacity-0 shadow-lg transition-all group-hover:visible group-hover:opacity-100">
        <div className="p-1">
          <Link to="/submit/experiment" className="block rounded px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground">
            Experiment
          </Link>
          <Link to="/submit/testfunction" className="block rounded px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground">
            Testfunction
          </Link>
          <Link to="/submit/environment" className="block rounded px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground">
            Environment
          </Link>
        </div>
      </div>
    </div>
  )
}

function UserMenu() {
  const { logout, loginUser } = useAuthStore()
  const { data: profile } = useLoggedInUser()
  const navigate = useNavigate()

  const handleLogout = () => {
    logout()
    navigate({ to: '/login' })
  }

  return (
    <div className="group relative">
      <button className="flex items-center gap-2 rounded-md border border-border px-3 py-1.5 text-sm font-medium text-foreground transition-colors hover:bg-muted">
        <User className="h-4 w-4 text-primary" />
        {profile?.user.username ?? loginUser}
      </button>
      <div className="invisible absolute right-0 top-full z-50 mt-1 min-w-48 rounded-md border border-border bg-popover text-popover-foreground opacity-0 shadow-lg transition-all group-hover:visible group-hover:opacity-100">
        <div className="border-b border-border p-4 text-center">
          {profile?.avatar && (
            <img src={profile.avatar} alt="" className="mx-auto mb-2 h-16 w-16 rounded-full object-cover" />
          )}
          <div className="text-sm font-medium">{profile?.user.username ?? loginUser}</div>
        </div>
        <div className="flex flex-col gap-1 p-2">
          <Link to="/profile" className="flex items-center gap-2 rounded px-3 py-2 text-sm hover:bg-accent hover:text-accent-foreground">
            <User className="h-4 w-4" />
            Profile
          </Link>
          <button
            onClick={handleLogout}
            className="flex w-full items-center gap-2 rounded px-3 py-2 text-left text-sm hover:bg-accent hover:text-accent-foreground"
          >
            <LogOut className="h-4 w-4" />
            Logout
          </button>
        </div>
      </div>
    </div>
  )
}

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
    <header className="bg-primary text-primary-foreground">
      <div className="flex items-center h-14 px-4">
        <h1 className="text-lg font-semibold mr-8">Adare Web</h1>

        {isLoggedIn && (
          <nav className="flex gap-1">
            <NavTab to="/home" label="Home" icon={<Home className="w-4 h-4" />} />
            <NavTab to="/run" label="Runs" icon={<Play className="w-4 h-4" />} />
            <NavTab to="/experiment" label="Experiments" icon={<FlaskConical className="w-4 h-4" />} />
            <NavTab to="/environment" label="Environments" icon={<Mountain className="w-4 h-4" />} />
            <NavTab to="/request" label="Requests" icon={<GitPullRequest className="w-4 h-4" />} />
            <NavTab to="/testfunctionset" label="Testfunctionsets" icon={<Boxes className="w-4 h-4" />} />
            <SubmitDropdown />
          </nav>
        )}

        <div className="ml-auto">
          {!isLoggedIn ? (
            <Link
              to="/login"
              className="flex items-center gap-2 bg-background text-primary px-4 py-1.5 rounded text-sm font-bold hover:bg-accent"
            >
              <LogIn className="w-4 h-4" />
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

function NavTab({ to, label, icon }: { to: string; label: string; icon?: React.ReactNode }) {
  return (
    <Link
      to={to}
      className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded hover:bg-white/10 transition-colors"
      activeProps={{ className: 'flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded bg-brand' }}
    >
      {icon}
      {label}
    </Link>
  )
}

function SubmitDropdown() {
  return (
    <div className="relative group">
      <button className="flex items-center gap-1.5 px-3 py-2 text-sm font-medium rounded hover:bg-white/10 transition-colors">
        <Upload className="w-4 h-4" />
        Submit
        <ChevronDown className="w-3 h-3" />
      </button>
      <div className="absolute left-0 top-full mt-1 bg-popover text-popover-foreground rounded shadow-lg border border-border min-w-48 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
        <div className="p-1">
          <Link to="/submit/experiment" className="block px-3 py-2 text-sm hover:bg-accent rounded">
            Experiment
          </Link>
          <Link to="/submit/testfunction" className="block px-3 py-2 text-sm hover:bg-accent rounded">
            Testfunction
          </Link>
          <Link to="/submit/environment" className="block px-3 py-2 text-sm hover:bg-accent rounded">
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
    <div className="relative group">
      <button className="flex items-center gap-2 bg-background text-primary px-3 py-1.5 rounded text-sm font-bold">
        <User className="w-4 h-4" />
        {profile?.user.username ?? loginUser}
      </button>
      <div className="absolute right-0 top-full mt-1 bg-popover text-popover-foreground rounded shadow-lg border border-border min-w-48 opacity-0 invisible group-hover:opacity-100 group-hover:visible transition-all z-50">
        <div className="p-4 text-center border-b border-border">
          {profile?.avatar && (
            <img src={profile.avatar} alt="" className="w-16 h-16 rounded-full mx-auto mb-2 object-cover" />
          )}
          <div className="text-sm font-medium">{profile?.user.username ?? loginUser}</div>
        </div>
        <div className="p-2 flex flex-col gap-1">
          <Link to="/profile" className="flex items-center gap-2 px-3 py-2 text-sm hover:bg-accent rounded">
            <User className="w-4 h-4" />
            Profile
          </Link>
          <ThemeToggle />
          <button
            onClick={handleLogout}
            className="flex items-center gap-2 w-full text-left px-3 py-2 text-sm hover:bg-accent rounded"
          >
            <LogOut className="w-4 h-4" />
            Logout
          </button>
        </div>
      </div>
    </div>
  )
}

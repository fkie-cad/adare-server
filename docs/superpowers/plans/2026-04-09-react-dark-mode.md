# React Dark Mode Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Add dark mode support to the React frontend with teal-tinted dark palette, system preference detection, manual toggle (light/dark/system), and localStorage persistence.

**Architecture:** CSS custom property overrides via `.dark` class on `<html>` (shadcn/ui pattern). A Zustand store manages theme state and syncs with localStorage + `prefers-color-scheme` media query. An inline script in `index.html` prevents FOUC. All hardcoded Tailwind color classes in 19 files get replaced with semantic theme tokens.

**Tech Stack:** Tailwind CSS 4, Zustand, React 19, lucide-react, OKLch color space

---

## File Structure

**Create:**
- `frontend_react/src/stores/theme-store.ts` — Zustand store for theme state (light/dark/system), localStorage persistence, media query listener
- `frontend_react/src/components/ui/theme-toggle.tsx` — Segmented light/dark/system toggle component

**Modify:**
- `frontend_react/src/styles/globals.css` — Add `.dark` block overriding all `--color-*` custom properties
- `frontend_react/index.html` — Add inline FOUC-prevention script
- `frontend_react/src/components/layout/header.tsx` — Replace hardcoded colors in dropdowns/buttons, add theme toggle to user menu
- `frontend_react/src/components/data-table/data-table-panel.tsx` — Replace `bg-white`, `hover:bg-gray-50`
- `frontend_react/src/components/data-table/data-table-select-filter.tsx` — Replace `bg-white`, `hover:bg-gray-50`
- `frontend_react/src/components/data-table/columns/parameter-cell.tsx` — Replace `bg-gray-200 text-gray-800` fallback
- `frontend_react/src/components/data-table/columns/os-info-cell.tsx` — Replace `text-gray-600` fallback
- `frontend_react/src/components/data-table/columns/run-counts-cell.tsx` — Replace `bg-green-500 text-white` / `bg-red-500 text-white` with badge variants
- `frontend_react/src/components/shared/login-form.tsx` — Replace `bg-gray-800 hover:bg-gray-900`
- `frontend_react/src/components/shared/status-icon.tsx` — Replace `text-gray-400` fallback
- `frontend_react/src/components/profile/profile-card.tsx` — Fix `bg-black`, `text-black`, `bg-teal-100`, `border-gray-700`
- `frontend_react/src/components/run/event-timeline.tsx` — Replace `bg-green-300`, `bg-gray-400`
- `frontend_react/src/components/experiment/experiment-overview.tsx` — Replace `bg-pink-700 text-white`, `bg-green-500 text-white`, `bg-red-500 text-white` with badge variants
- `frontend_react/src/components/environment/environment-overview.tsx` — Same badge pattern
- `frontend_react/src/components/ui/badge.tsx` — Add `success` and `destructive` variant fixes, replace `text-white` with `text-destructive-foreground`
- `frontend_react/src/constants/mappings.ts` — Replace `text-gray-800` linux color, adjust `statusBgColorMapping` and `dtypeColorMapping` for dark mode
- `frontend_react/src/constants/tag-colors.ts` — Replace `bg-gray-700` with theme-aware default
- `frontend_react/src/pages/home.tsx` — `bg-white/20` works on colored badges, no change needed
- `frontend_react/src/components/experiment/experiment-tag-cloud-view.tsx` — `bg-white/20` works on colored badges, no change needed

---

### Task 1: Dark Theme CSS Variables

**Files:**
- Modify: `frontend_react/src/styles/globals.css`

- [ ] **Step 1: Add the `.dark` class override block after the `@theme` block**

In `frontend_react/src/styles/globals.css`, add this block between the `@theme` closing brace and the `@layer base` block:

```css
.dark {
  --color-background: oklch(0.12 0.02 168);
  --color-foreground: oklch(0.93 0.02 168);
  --color-card: oklch(0.16 0.025 168);
  --color-card-foreground: oklch(0.93 0.02 168);
  --color-popover: oklch(0.16 0.025 168);
  --color-popover-foreground: oklch(0.93 0.02 168);
  --color-primary: oklch(0.55 0.15 168);
  --color-primary-foreground: oklch(0.93 0.02 168);
  --color-secondary: oklch(0.50 0.15 255);
  --color-secondary-foreground: oklch(0.93 0.02 168);
  --color-muted: oklch(0.20 0.025 168);
  --color-muted-foreground: oklch(0.65 0.04 168);
  --color-accent: oklch(0.22 0.03 168);
  --color-accent-foreground: oklch(0.85 0.05 168);
  --color-destructive: oklch(0.55 0.22 25);
  --color-destructive-foreground: oklch(0.93 0.02 168);
  --color-border: oklch(0.25 0.03 168);
  --color-input: oklch(0.25 0.03 168);
  --color-ring: oklch(0.55 0.15 168);
  --color-chart-1: oklch(0.70 0.20 41);
  --color-chart-2: oklch(0.65 0.12 185);
  --color-chart-3: oklch(0.50 0.08 227);
  --color-chart-4: oklch(0.80 0.17 84);
  --color-chart-5: oklch(0.75 0.17 70);
  --color-sidebar: oklch(0.14 0.022 168);
  --color-sidebar-foreground: oklch(0.93 0.02 168);
  --color-sidebar-primary: oklch(0.55 0.15 168);
  --color-sidebar-primary-foreground: oklch(0.93 0.02 168);
  --color-sidebar-accent: oklch(0.22 0.03 168);
  --color-sidebar-accent-foreground: oklch(0.85 0.05 168);
  --color-sidebar-border: oklch(0.25 0.03 168);
  --color-sidebar-ring: oklch(0.55 0.15 168);
  --color-brand: oklch(0.55 0.15 168);
}
```

The full `globals.css` should now be:

```css
@import "tailwindcss";
@import "@fontsource-variable/inter";

@theme {
  --color-background: oklch(1 0 0);
  --color-foreground: oklch(0.145 0 0);
  --color-card: oklch(1 0 0);
  --color-card-foreground: oklch(0.145 0 0);
  --color-popover: oklch(1 0 0);
  --color-popover-foreground: oklch(0.145 0 0);
  --color-primary: oklch(0.55 0.15 168);
  --color-primary-foreground: oklch(0.985 0 0);
  --color-secondary: oklch(0.50 0.15 255);
  --color-secondary-foreground: oklch(0.985 0 0);
  --color-muted: oklch(0.97 0.014 254.604);
  --color-muted-foreground: oklch(0.556 0.022 257.417);
  --color-accent: oklch(0.95 0.02 168);
  --color-accent-foreground: oklch(0.25 0.05 168);
  --color-destructive: oklch(0.45 0.22 25);
  --color-destructive-foreground: oklch(0.577 0.245 27.325);
  --color-border: oklch(0.922 0.013 255.508);
  --color-input: oklch(0.922 0.013 255.508);
  --color-ring: oklch(0.55 0.15 168);
  --color-chart-1: oklch(0.646 0.222 41.116);
  --color-chart-2: oklch(0.6 0.118 184.704);
  --color-chart-3: oklch(0.398 0.07 227.392);
  --color-chart-4: oklch(0.828 0.189 84.429);
  --color-chart-5: oklch(0.769 0.188 70.08);
  --color-sidebar: oklch(0.985 0.002 247.839);
  --color-sidebar-foreground: oklch(0.145 0 0);
  --color-sidebar-primary: oklch(0.55 0.15 168);
  --color-sidebar-primary-foreground: oklch(0.985 0 0);
  --color-sidebar-accent: oklch(0.95 0.02 168);
  --color-sidebar-accent-foreground: oklch(0.25 0.05 168);
  --color-sidebar-border: oklch(0.922 0.013 255.508);
  --color-sidebar-ring: oklch(0.55 0.15 168);
  --radius-sm: 0.25rem;
  --radius-md: 0.375rem;
  --radius-lg: 0.5rem;
  --radius-xl: 0.75rem;
  --color-brand: oklch(0.55 0.15 168);
}

.dark {
  --color-background: oklch(0.12 0.02 168);
  --color-foreground: oklch(0.93 0.02 168);
  --color-card: oklch(0.16 0.025 168);
  --color-card-foreground: oklch(0.93 0.02 168);
  --color-popover: oklch(0.16 0.025 168);
  --color-popover-foreground: oklch(0.93 0.02 168);
  --color-primary: oklch(0.55 0.15 168);
  --color-primary-foreground: oklch(0.93 0.02 168);
  --color-secondary: oklch(0.50 0.15 255);
  --color-secondary-foreground: oklch(0.93 0.02 168);
  --color-muted: oklch(0.20 0.025 168);
  --color-muted-foreground: oklch(0.65 0.04 168);
  --color-accent: oklch(0.22 0.03 168);
  --color-accent-foreground: oklch(0.85 0.05 168);
  --color-destructive: oklch(0.55 0.22 25);
  --color-destructive-foreground: oklch(0.93 0.02 168);
  --color-border: oklch(0.25 0.03 168);
  --color-input: oklch(0.25 0.03 168);
  --color-ring: oklch(0.55 0.15 168);
  --color-chart-1: oklch(0.70 0.20 41);
  --color-chart-2: oklch(0.65 0.12 185);
  --color-chart-3: oklch(0.50 0.08 227);
  --color-chart-4: oklch(0.80 0.17 84);
  --color-chart-5: oklch(0.75 0.17 70);
  --color-sidebar: oklch(0.14 0.022 168);
  --color-sidebar-foreground: oklch(0.93 0.02 168);
  --color-sidebar-primary: oklch(0.55 0.15 168);
  --color-sidebar-primary-foreground: oklch(0.93 0.02 168);
  --color-sidebar-accent: oklch(0.22 0.03 168);
  --color-sidebar-accent-foreground: oklch(0.85 0.05 168);
  --color-sidebar-border: oklch(0.25 0.03 168);
  --color-sidebar-ring: oklch(0.55 0.15 168);
  --color-brand: oklch(0.55 0.15 168);
}

@layer base {
  body {
    @apply bg-background text-foreground;
    font-family: 'Inter Variable', ui-sans-serif, system-ui, sans-serif;
    -webkit-font-smoothing: antialiased;
    -moz-osx-font-smoothing: grayscale;
  }
}
```

- [ ] **Step 2: Verify the CSS compiles**

Run: `cd frontend_react && npm run build 2>&1 | head -20`
Expected: No CSS errors. Build succeeds or only TS errors (not CSS).

- [ ] **Step 3: Commit**

```bash
git add frontend_react/src/styles/globals.css
git commit -m "feat: add dark mode CSS variable overrides with teal-tinted palette"
```

---

### Task 2: Theme Store

**Files:**
- Create: `frontend_react/src/stores/theme-store.ts`

- [ ] **Step 1: Create the theme store**

Create `frontend_react/src/stores/theme-store.ts`:

```ts
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
```

- [ ] **Step 2: Verify it compiles**

Run: `cd frontend_react && npx tsc --noEmit 2>&1 | grep theme-store || echo "No errors"`
Expected: No type errors related to theme-store.

- [ ] **Step 3: Commit**

```bash
git add frontend_react/src/stores/theme-store.ts
git commit -m "feat: add theme store with system preference detection and localStorage persistence"
```

---

### Task 3: FOUC Prevention Script

**Files:**
- Modify: `frontend_react/index.html`

- [ ] **Step 1: Add inline script to `<head>`**

In `frontend_react/index.html`, add a `<script>` tag inside `<head>` after the `<title>`:

```html
<!doctype html>
<html lang="en">
  <head>
    <meta charset="UTF-8" />
    <link rel="icon" href="/favicon.ico" />
    <meta name="viewport" content="width=device-width, initial-scale=1.0" />
    <title>Adare Web</title>
    <script>
      (function() {
        var t = localStorage.getItem('adare-theme') || 'system';
        var dark = t === 'dark' || (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
        if (dark) document.documentElement.classList.add('dark');
      })();
    </script>
  </head>
  <body>
    <div id="root"></div>
    <script type="module" src="/src/main.tsx"></script>
  </body>
</html>
```

- [ ] **Step 2: Commit**

```bash
git add frontend_react/index.html
git commit -m "feat: add FOUC prevention script for dark mode"
```

---

### Task 4: Theme Toggle Component

**Files:**
- Create: `frontend_react/src/components/ui/theme-toggle.tsx`

- [ ] **Step 1: Create the toggle component**

Create `frontend_react/src/components/ui/theme-toggle.tsx`:

```tsx
import { Sun, Moon, Monitor } from 'lucide-react'
import { useThemeStore } from '@/stores/theme-store'
import { cn } from '@/lib/utils'

type Theme = 'light' | 'dark' | 'system'

const options: { value: Theme; icon: typeof Sun; label: string }[] = [
  { value: 'light', icon: Sun, label: 'Light' },
  { value: 'dark', icon: Moon, label: 'Dark' },
  { value: 'system', icon: Monitor, label: 'System' },
]

export function ThemeToggle() {
  const { theme, setTheme } = useThemeStore()

  return (
    <div className="flex items-center gap-2 px-3 py-2">
      <span className="text-sm">Theme</span>
      <div className="ml-auto flex gap-0.5 rounded-md bg-muted p-0.5">
        {options.map(({ value, icon: Icon, label }) => (
          <button
            key={value}
            onClick={() => setTheme(value)}
            className={cn(
              'rounded p-1.5 transition-colors',
              theme === value
                ? 'bg-background text-foreground shadow-sm'
                : 'text-muted-foreground hover:text-foreground',
            )}
            title={label}
          >
            <Icon className="h-3.5 w-3.5" />
          </button>
        ))}
      </div>
    </div>
  )
}
```

- [ ] **Step 2: Verify it compiles**

Run: `cd frontend_react && npx tsc --noEmit 2>&1 | grep theme-toggle || echo "No errors"`
Expected: No type errors.

- [ ] **Step 3: Commit**

```bash
git add frontend_react/src/components/ui/theme-toggle.tsx
git commit -m "feat: add theme toggle component with light/dark/system selector"
```

---

### Task 5: Header Dark Mode Fixes + Toggle Integration

**Files:**
- Modify: `frontend_react/src/components/layout/header.tsx`

- [ ] **Step 1: Add ThemeToggle import and replace hardcoded colors**

The full updated `header.tsx`:

```tsx
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
```

Key changes:
- Line 42: `bg-white text-primary hover:bg-gray-100` → `bg-background text-primary hover:bg-accent`
- Line 77: Submit dropdown `bg-white rounded shadow-lg border` → `bg-popover text-popover-foreground rounded shadow-lg border border-border`
- Lines 79-85: `text-gray-700 hover:bg-gray-100` → `hover:bg-accent` (inherits text from popover-foreground)
- Line 106: User button `bg-white text-primary` → `bg-background text-primary`
- Line 110: User dropdown `bg-white rounded shadow-lg border` → `bg-popover text-popover-foreground rounded shadow-lg border border-border`
- Line 111: `border-b` → `border-b border-border`
- Line 115: `text-gray-900` → removed (inherits from popover-foreground)
- Lines 118, 124: `text-gray-700 hover:bg-gray-100` → `hover:bg-accent` (inherits text)
- Added `<ThemeToggle />` between Profile link and Logout button
- Added `import { ThemeToggle }` at top

- [ ] **Step 2: Verify it compiles**

Run: `cd frontend_react && npx tsc --noEmit 2>&1 | grep -i error | head -5 || echo "No errors"`
Expected: No errors related to header.tsx.

- [ ] **Step 3: Commit**

```bash
git add frontend_react/src/components/layout/header.tsx
git commit -m "feat: update header with theme-aware colors and integrate theme toggle"
```

---

### Task 6: Data Table Components

**Files:**
- Modify: `frontend_react/src/components/data-table/data-table-panel.tsx`
- Modify: `frontend_react/src/components/data-table/data-table-select-filter.tsx`

- [ ] **Step 1: Fix data-table-panel.tsx**

In `frontend_react/src/components/data-table/data-table-panel.tsx`, change line 65:

Old: `"absolute right-0 top-full mt-1 bg-white rounded-md shadow-lg border p-2 min-w-48 z-50"`
New: `"absolute right-0 top-full mt-1 bg-popover text-popover-foreground rounded-md shadow-lg border border-border p-2 min-w-48 z-50"`

Change line 83:

Old: `"flex items-center gap-2 px-2 py-1 text-sm hover:bg-gray-50 rounded cursor-pointer"`
New: `"flex items-center gap-2 px-2 py-1 text-sm hover:bg-accent rounded cursor-pointer"`

- [ ] **Step 2: Fix data-table-select-filter.tsx**

In `frontend_react/src/components/data-table/data-table-select-filter.tsx`, change line 52:

Old: `"absolute left-0 top-full mt-1 bg-white rounded-md shadow-lg border p-1 min-w-48 z-50 max-h-60 overflow-y-auto"`
New: `"absolute left-0 top-full mt-1 bg-popover text-popover-foreground rounded-md shadow-lg border border-border p-1 min-w-48 z-50 max-h-60 overflow-y-auto"`

Change line 57:

Old: `"flex items-center gap-2 w-full px-2 py-1.5 text-sm hover:bg-gray-50 rounded text-left"`
New: `"flex items-center gap-2 w-full px-2 py-1.5 text-sm hover:bg-accent rounded text-left"`

- [ ] **Step 3: Commit**

```bash
git add frontend_react/src/components/data-table/data-table-panel.tsx frontend_react/src/components/data-table/data-table-select-filter.tsx
git commit -m "feat: update data table dropdown components with theme-aware colors"
```

---

### Task 7: Badge Variant Cleanup

**Files:**
- Modify: `frontend_react/src/components/ui/badge.tsx`

- [ ] **Step 1: Update badge variants**

In `frontend_react/src/components/ui/badge.tsx`, update the variants object:

Old:
```ts
        destructive: 'border-transparent bg-destructive text-white shadow',
```
New:
```ts
        destructive: 'border-transparent bg-destructive text-destructive-foreground shadow',
```

The `success` variant (`border-transparent bg-green-500 text-white`) is fine — green-500 on both light and dark backgrounds has good contrast with white text. No change needed.

- [ ] **Step 2: Commit**

```bash
git add frontend_react/src/components/ui/badge.tsx
git commit -m "fix: use theme token for destructive badge text color"
```

---

### Task 8: Constants and Mapping Colors

**Files:**
- Modify: `frontend_react/src/constants/mappings.ts`
- Modify: `frontend_react/src/constants/tag-colors.ts`

- [ ] **Step 1: Update mappings.ts**

In `frontend_react/src/constants/mappings.ts`:

Change `osColorMapping` (line 62-65):

Old:
```ts
export const osColorMapping: Record<OSListType, string> = {
  windows: 'text-blue-600',
  linux: 'text-gray-800',
}
```
New:
```ts
export const osColorMapping: Record<OSListType, string> = {
  windows: 'text-blue-600',
  linux: 'text-foreground',
}
```

Change `statusBgColorMapping` (lines 35-42) to use slightly more saturated colors that work on both light and dark backgrounds:

Old:
```ts
export const statusBgColorMapping: Record<StatusType, string> = {
  'not assigned': 'bg-blue-100 text-blue-700',
  accepted: 'bg-green-100 text-green-700',
  rejected: 'bg-red-100 text-red-700',
  assigned: 'bg-yellow-100 text-yellow-700',
  success: 'bg-green-100 text-green-700',
  failed: 'bg-red-100 text-red-700',
}
```
New:
```ts
export const statusBgColorMapping: Record<StatusType, string> = {
  'not assigned': 'bg-blue-500/15 text-blue-600',
  accepted: 'bg-green-500/15 text-green-600',
  rejected: 'bg-red-500/15 text-red-600',
  assigned: 'bg-yellow-500/15 text-yellow-600',
  success: 'bg-green-500/15 text-green-600',
  failed: 'bg-red-500/15 text-red-600',
}
```

Using `bg-{color}-500/15` (15% opacity of a mid-range color) provides a subtle tint that adapts to any background, while the `-600` text has enough contrast in both modes.

Change `dtypeColorMapping` (lines 69-75) similarly:

Old:
```ts
export const dtypeColorMapping: Record<(typeof dtypeList)[number], string> = {
  int: 'bg-indigo-200 text-indigo-800',
  float: 'bg-blue-200 text-blue-800',
  str: 'bg-orange-200 text-orange-800',
  bool: 'bg-lime-200 text-lime-800',
  list: 'bg-cyan-200 text-cyan-800',
}
```
New:
```ts
export const dtypeColorMapping: Record<(typeof dtypeList)[number], string> = {
  int: 'bg-indigo-500/15 text-indigo-600',
  float: 'bg-blue-500/15 text-blue-600',
  str: 'bg-orange-500/15 text-orange-600',
  bool: 'bg-lime-500/15 text-lime-600',
  list: 'bg-cyan-500/15 text-cyan-600',
}
```

- [ ] **Step 2: Update tag-colors.ts**

In `frontend_react/src/constants/tag-colors.ts`, change line 8:

Old: `export const defaultTagColor = 'bg-gray-700 text-white'`
New: `export const defaultTagColor = 'bg-muted-foreground text-background'`

This uses the semantic tokens so the default tag color adapts to the theme. The scoped tag colors (`bg-blue-800 text-white`, etc.) are saturated enough to work in both modes — no change needed.

- [ ] **Step 3: Commit**

```bash
git add frontend_react/src/constants/mappings.ts frontend_react/src/constants/tag-colors.ts
git commit -m "feat: update color mappings to use theme-adaptive colors for dark mode"
```

---

### Task 9: Status, Parameter, and OS Cell Fixes

**Files:**
- Modify: `frontend_react/src/components/shared/status-icon.tsx`
- Modify: `frontend_react/src/components/data-table/columns/parameter-cell.tsx`
- Modify: `frontend_react/src/components/data-table/columns/os-info-cell.tsx`

- [ ] **Step 1: Fix status-icon.tsx**

In `frontend_react/src/components/shared/status-icon.tsx`, change line 20:

Old: `const colorClass = valid ? statusColorMapping[status as StatusType] : 'text-gray-400'`
New: `const colorClass = valid ? statusColorMapping[status as StatusType] : 'text-muted-foreground'`

- [ ] **Step 2: Fix parameter-cell.tsx**

In `frontend_react/src/components/data-table/columns/parameter-cell.tsx`, change line 17:

Old: `const colorClass = isValidDtype(dtype) ? dtypeColorMapping[dtype as keyof typeof dtypeColorMapping] : 'bg-gray-200 text-gray-800'`
New: `const colorClass = isValidDtype(dtype) ? dtypeColorMapping[dtype as keyof typeof dtypeColorMapping] : 'bg-muted text-muted-foreground'`

- [ ] **Step 3: Fix os-info-cell.tsx**

In `frontend_react/src/components/data-table/columns/os-info-cell.tsx`, change line 15:

Old: `const colorClass = isValidOSListType(osType) ? osColorMapping[osType as OSListType] : 'text-gray-600'`
New: `const colorClass = isValidOSListType(osType) ? osColorMapping[osType as OSListType] : 'text-muted-foreground'`

- [ ] **Step 4: Commit**

```bash
git add frontend_react/src/components/shared/status-icon.tsx frontend_react/src/components/data-table/columns/parameter-cell.tsx frontend_react/src/components/data-table/columns/os-info-cell.tsx
git commit -m "feat: replace hardcoded gray fallback colors with theme tokens"
```

---

### Task 10: Login Form and Profile Card

**Files:**
- Modify: `frontend_react/src/components/shared/login-form.tsx`
- Modify: `frontend_react/src/components/profile/profile-card.tsx`

- [ ] **Step 1: Fix login-form.tsx**

In `frontend_react/src/components/shared/login-form.tsx`, change line 39:

Old: `className="w-full bg-gray-800 hover:bg-gray-900"`
New: `className="w-full bg-foreground text-background hover:bg-foreground/90"`

This uses the theme's foreground color as a button background (dark in light mode, light in dark mode), creating a high-contrast inverted button that works in both themes.

- [ ] **Step 2: Fix profile-card.tsx**

In `frontend_react/src/components/profile/profile-card.tsx`:

Change the `roleColorMapping` (lines 11-16):

Old:
```ts
const roleColorMapping: Record<string, string> = {
  Owners: 'bg-black text-white border-gray-700',
  Supervisor: 'bg-pink-700 text-white border-pink-600',
  admin: 'bg-black text-white border-gray-700',
  supervisor: 'bg-pink-700 text-white border-pink-600',
}
```
New:
```ts
const roleColorMapping: Record<string, string> = {
  Owners: 'bg-foreground text-background border-border',
  Supervisor: 'bg-pink-700 text-white border-pink-600',
  admin: 'bg-foreground text-background border-border',
  supervisor: 'bg-pink-700 text-white border-pink-600',
}
```

Change the fallback in `getRoleColor` (line 19):

Old: `return roleColorMapping[role] ?? 'bg-amber-400 text-black border-amber-300'`
New: `return roleColorMapping[role] ?? 'bg-amber-400 text-foreground border-amber-300'`

Change the profile banner (line 25):

Old: `<div className="bg-teal-100 h-32 flex items-end justify-center pb-0 relative">`
New: `<div className="bg-primary/15 h-32 flex items-end justify-center pb-0 relative">`

Using `bg-primary/15` gives a subtle teal tint that works on both light and dark backgrounds.

- [ ] **Step 3: Commit**

```bash
git add frontend_react/src/components/shared/login-form.tsx frontend_react/src/components/profile/profile-card.tsx
git commit -m "feat: update login form and profile card with theme-aware colors"
```

---

### Task 11: Event Timeline and Run Count Cells

**Files:**
- Modify: `frontend_react/src/components/run/event-timeline.tsx`
- Modify: `frontend_react/src/components/data-table/columns/run-counts-cell.tsx`
- Modify: `frontend_react/src/components/experiment/experiment-overview.tsx`
- Modify: `frontend_react/src/components/environment/environment-overview.tsx`

- [ ] **Step 1: Fix event-timeline.tsx**

In `frontend_react/src/components/run/event-timeline.tsx`:

Change line 30 (timeline line color):

Old: `<div className="absolute left-3 top-0 bottom-0 w-0.5 bg-green-300" />`
New: `<div className="absolute left-3 top-0 bottom-0 w-0.5 bg-border" />`

Change line 109 (default dot color):

Old: `return 'bg-gray-400'`
New: `return 'bg-muted-foreground'`

The `bg-green-500`, `bg-red-500` dot colors in lines 105-108 are fine — they're saturated enough for both modes.

- [ ] **Step 2: Fix run-counts-cell.tsx**

In `frontend_react/src/components/data-table/columns/run-counts-cell.tsx`, the current code uses:

```tsx
<Badge className="bg-green-500 text-white">{counts.successful}</Badge>
<Badge className="bg-red-500 text-white">{counts.failed}</Badge>
```

These work fine in both modes (saturated colors with white text). No change needed.

- [ ] **Step 3: Fix experiment-overview.tsx**

In `frontend_react/src/components/experiment/experiment-overview.tsx`, the badges on lines 80, 89, 92:

```tsx
<Badge className="bg-pink-700 text-white">  // tags - fine
<Badge className="bg-green-500 text-white">  // success count - fine
<Badge className="bg-red-500 text-white">    // failed count - fine
```

These are all saturated colors with white text — they work in both modes. No change needed.

- [ ] **Step 4: Fix environment-overview.tsx**

In `frontend_react/src/components/environment/environment-overview.tsx`, lines 218-219:

```tsx
<Badge className="bg-green-500 text-white">{exp.run_counts.successful}</Badge>
<Badge className="bg-red-500 text-white">{exp.run_counts.failed}</Badge>
```

Same as above — saturated colors with white text work in both modes. No change needed.

- [ ] **Step 5: Commit**

```bash
git add frontend_react/src/components/run/event-timeline.tsx
git commit -m "feat: update event timeline with theme-aware colors"
```

---

### Task 12: Initialize Theme Store on App Load

**Files:**
- Modify: `frontend_react/src/components/layout/main-layout.tsx`

- [ ] **Step 1: Read the current main-layout.tsx**

Read `frontend_react/src/components/layout/main-layout.tsx` to see the current structure.

- [ ] **Step 2: Import and initialize theme store**

Add to the imports in `main-layout.tsx`:

```ts
import { useThemeStore } from '@/stores/theme-store'
```

Inside the `MainLayout` component, add this line (before the return statement, alongside the existing `useAuthStore` call):

```ts
useThemeStore() // Initialize theme on mount
```

This ensures the Zustand store is created (which triggers the media query listener setup) when the app loads.

- [ ] **Step 3: Commit**

```bash
git add frontend_react/src/components/layout/main-layout.tsx
git commit -m "feat: initialize theme store on app mount"
```

---

### Task 13: Final Verification

- [ ] **Step 1: Build check**

Run: `cd frontend_react && npm run build`
Expected: Build succeeds with no errors.

- [ ] **Step 2: Manual testing**

Run: `cd frontend_react && npm run dev`

Test the following:
1. Open the app — should render in light or dark mode based on OS preference
2. Log in → open user menu → verify theme toggle is visible between Profile and Logout
3. Click "Dark" segment → entire app should switch to teal-tinted dark mode
4. Click "Light" segment → app returns to light mode
5. Click "System" segment → app follows OS preference
6. Hard-refresh while in dark mode → no white flash (FOUC prevention works)
7. Close tab, reopen → theme choice persists
8. Navigate through all pages: Home, Runs, Experiments, Environments, Testfunctionsets, Profile
9. Check dropdowns (Submit menu, User menu, column visibility menu, filter dropdowns) render with correct dark backgrounds
10. Check badges, tags, status icons, and data table cells for readability

- [ ] **Step 3: Final commit (if any adjustments needed)**

After visual testing, if any color values need fine-tuning (especially the OKLch dark palette values), adjust `globals.css` and commit:

```bash
git add -u frontend_react/
git commit -m "fix: fine-tune dark mode colors after visual testing"
```

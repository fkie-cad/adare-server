# Dark Mode Support — Design Spec

## Context

The ADARE React frontend (`frontend_react/`) currently only supports a light theme. Users have no way to switch to a dark color scheme. The app already uses a CSS variable-based theme system (OKLCH colors in `globals.css`), which makes adding dark mode straightforward — override the variables rather than rewriting every component.

## Decisions

- **Mode control:** System preference + manual override (light / dark / system), persisted in localStorage
- **Toggle location:** Inside the user dropdown menu (between Profile and Logout), as a submenu with radio options
- **Implementation approach:** CSS variable overrides via `.dark` class on `<html>`, managed by a Zustand store
- **No new dependencies**

## 1. Theme Infrastructure

### 1.1 Dark Color Palette (`globals.css`)

Add a `.dark` selector block that overrides all existing `@theme` CSS variables with dark equivalents. Colors stay in OKLCH color space for consistency.

Key mappings:
| Variable | Light | Dark |
|---|---|---|
| `--color-background` | `oklch(1 0 0)` (white) | `oklch(0.145 0 0)` (near-black) |
| `--color-foreground` | `oklch(0.145 0 0)` (near-black) | `oklch(0.985 0 0)` (near-white) |
| `--color-card` | `oklch(1 0 0)` | `oklch(0.2 0 0)` |
| `--color-popover` | `oklch(1 0 0)` | `oklch(0.2 0 0)` |
| `--color-muted` | `oklch(0.97 0.014 254)` | `oklch(0.25 0.014 254)` |
| `--color-muted-foreground` | `oklch(0.556 0.022 257)` | `oklch(0.7 0.022 257)` |
| `--color-accent` | `oklch(0.95 0.02 168)` | `oklch(0.25 0.02 168)` |
| `--color-accent-foreground` | `oklch(0.25 0.05 168)` | `oklch(0.85 0.05 168)` |
| `--color-border` | `oklch(0.922 0.013 255)` | `oklch(0.3 0.013 255)` |
| `--color-input` | `oklch(0.922 0.013 255)` | `oklch(0.3 0.013 255)` |
| `--color-sidebar` | `oklch(0.985 0.002 247)` | `oklch(0.17 0.002 247)` |
| `--color-sidebar-foreground` | `oklch(0.145 0 0)` | `oklch(0.985 0 0)` |
| `--color-sidebar-accent` | `oklch(0.95 0.02 168)` | `oklch(0.25 0.02 168)` |
| `--color-sidebar-accent-foreground` | `oklch(0.25 0.05 168)` | `oklch(0.85 0.05 168)` |
| `--color-sidebar-border` | `oklch(0.922 0.013 255)` | `oklch(0.3 0.013 255)` |

Primary, secondary, destructive, ring, brand, and chart colors remain unchanged (they have sufficient contrast in both themes).

### 1.2 Theme Store (`src/stores/theme-store.ts`)

A Zustand store with `persist` middleware (localStorage):

```typescript
type ThemePreference = 'light' | 'dark' | 'system'

interface ThemeState {
  preference: ThemePreference
  setPreference: (pref: ThemePreference) => void
}
```

### 1.3 Theme Applicator (`src/lib/theme.ts`)

A utility that:
- Resolves `'system'` to actual light/dark using `window.matchMedia('(prefers-color-scheme: dark)')`
- Adds/removes `.dark` class on `document.documentElement`
- Listens for OS preference changes when set to `'system'`

Called from a `useEffect` in `App.tsx` (or a small `ThemeProvider` wrapper).

### 1.4 Flash Prevention

Add a small inline `<script>` in `index.html` that reads localStorage and applies `.dark` before React hydrates, preventing a white flash on dark-mode page loads.

## 2. Theme Toggle UI

### Location
Inside the `UserMenu` component in `Header.tsx`, between the Profile link and Logout button.

### Appearance
A "Theme" menu item that expands a submenu showing three radio-style options:
- Sun icon + "Light"
- Moon icon + "Dark"
- Monitor icon + "System"

Active option displays a checkmark and uses the primary (teal) color. Uses `Sun`, `Moon`, `Monitor`, `Check` icons from `lucide-react` (already a dependency).

### Logged-out behavior
No toggle available — the app follows system preference only. The theme store defaults to `'system'`.

## 3. Hardcoded Color Migration

### 3.1 Replace semantic gray/white classes

Replace hardcoded Tailwind color classes with CSS variable-based classes in these files:

| File | Changes |
|---|---|
| `components/layout/Header.tsx` | `bg-white` → `bg-popover`, `text-gray-700` → `text-popover-foreground`, `hover:bg-gray-100` → `hover:bg-accent`, `text-gray-900` → `text-foreground`, dropdown `bg-white` → `bg-popover` |
| `components/shared/login-form.tsx` | Keep as-is — Gitea-branded button with dark bg + white text works in both themes |
| `components/data-table/data-table-select-filter.tsx` | `bg-white` → `bg-popover`, `hover:bg-gray-50` → `hover:bg-accent` |
| `components/data-table/data-table-panel.tsx` | `bg-white` → `bg-popover`, `hover:bg-gray-50` → `hover:bg-accent`, `text-blue-600` → `text-secondary` |
| `components/data-table/columns/parameter-cell.tsx` | `bg-gray-200 text-gray-800` → `bg-muted text-muted-foreground` |
| `components/data-table/columns/os-info-cell.tsx` | `text-gray-600` → `text-muted-foreground` |
| `components/shared/status-icon.tsx` | `text-gray-400` → `text-muted-foreground` |
| `components/profile/profile-card.tsx` | `bg-teal-100` → `bg-accent` |
| `components/run/event-timeline.tsx` | `bg-green-300` → keep (semantic), `bg-gray-400` → `bg-muted-foreground` |

### 3.2 Add dark variants to badge-style mappings

Update `constants/mappings.ts`:
- `statusBgColorMapping`: Add `dark:` variants, e.g. `'bg-blue-100 text-blue-700 dark:bg-blue-900 dark:text-blue-300'`
- `dtypeColorMapping`: Same pattern, e.g. `'bg-indigo-200 text-indigo-800 dark:bg-indigo-900 dark:text-indigo-200'`

### 3.3 Leave as-is (already dark-mode compatible)

- **Tag colors** (`tag-colors.ts`): Dark backgrounds with white text — work in both themes
- **Role badges** (`profile-card.tsx`): Dark backgrounds with white text
- **Status text colors** (`statusColorMapping`): Mid-range shades (500-600) have sufficient contrast
- **Dashboard stat colors** (`home.tsx`, `welcome-card.tsx`): Decorative, mid-range shades
- **Chart/progress bar colors** (`experiment-dashboard-view.tsx`): Data visualization, fixed colors
- **Success/fail badges** (`environment-overview.tsx`, `experiment-overview.tsx`, `run-counts-cell.tsx`): Colored badges with white text

## 4. Files to Create/Modify

### New files
- `src/stores/theme-store.ts` — Zustand theme preference store
- `src/lib/theme.ts` — Theme resolution and DOM application logic

### Modified files
- `src/styles/globals.css` — Add `.dark` variable overrides
- `index.html` — Add flash-prevention script
- `src/App.tsx` — Hook up theme applicator
- `src/components/layout/Header.tsx` — Add theme toggle to UserMenu, fix hardcoded colors
- `src/constants/mappings.ts` — Add `dark:` variants to badge mappings
- `src/components/data-table/data-table-select-filter.tsx` — Semantic color classes
- `src/components/data-table/data-table-panel.tsx` — Semantic color classes
- `src/components/data-table/columns/parameter-cell.tsx` — Semantic color classes
- `src/components/data-table/columns/os-info-cell.tsx` — Semantic color classes
- `src/components/shared/status-icon.tsx` — Semantic color classes
- `src/components/profile/profile-card.tsx` — Semantic color classes
- `src/components/run/event-timeline.tsx` — Semantic color classes
- `src/components/ui/alert.tsx` — Add dark variant to success alert
- `src/components/ui/badge.tsx` — Review destructive/success variants

## 5. Verification

1. Run `make react` to start the dev server
2. Toggle through Light / Dark / System in the user menu
3. Verify all pages render correctly in both themes:
   - Home page (stats cards)
   - Run list and detail (event timeline, status badges)
   - Experiment list and dashboard (charts, tag cloud, run counts)
   - Environment list and detail
   - Profile page (role badges, avatar)
   - Login page (follows system preference)
   - Data tables (filters, column panels, parameter cells)
4. Test system preference tracking: change OS dark mode setting while app is set to "System"
5. Test persistence: reload page, verify theme preference is retained
6. Test flash prevention: load page in dark mode, verify no white flash
7. Test logged-out state: verify login page follows system preference with no toggle

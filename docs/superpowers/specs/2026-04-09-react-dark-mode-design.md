# React Frontend Dark Mode

## Context

The ADARE React frontend currently only supports a light theme. Users working in dark environments (common for researchers and developers) need a dark mode option. The frontend already uses Tailwind CSS 4 with all colors defined as CSS custom properties in `globals.css`, making it well-suited for CSS-variable-based theming.

## Design Decisions

- **Palette direction:** Teal-tinted dark (subtle teal undertones in backgrounds, brand-immersive)
- **Approach:** CSS custom property overrides via `.dark` class on `<html>` (shadcn/ui convention)
- **Toggle:** Light / Dark / System segmented control inside the user menu dropdown
- **Persistence:** `localStorage` key `adare-theme`, defaults to `system`
- **FOUC prevention:** Inline `<script>` in `index.html` applies `.dark` class before React hydrates

## Architecture

### 1. Dark Theme CSS Variables (`globals.css`)

Add a `.dark` selector block that overrides all `--color-*` custom properties with teal-tinted dark values:

```
.dark {
  --color-background: oklch(0.12 0.02 168);        /* teal-tinted near-black */
  --color-foreground: oklch(0.93 0.02 168);         /* light teal-white */
  --color-card: oklch(0.16 0.025 168);              /* slightly lighter card bg */
  --color-card-foreground: oklch(0.93 0.02 168);
  --color-popover: oklch(0.16 0.025 168);
  --color-popover-foreground: oklch(0.93 0.02 168);
  --color-primary: oklch(0.45 0.12 168);            /* slightly darker teal for dark bg */
  --color-primary-foreground: oklch(0.93 0.02 168);
  --color-secondary: oklch(0.45 0.12 255);
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

Exact OKLch values will be fine-tuned during implementation to ensure WCAG AA contrast ratios.

### 2. Theme Store (`stores/theme-store.ts`)

Zustand store managing theme state:

```ts
type Theme = 'light' | 'dark' | 'system'

interface ThemeState {
  theme: Theme
  setTheme: (theme: Theme) => void
}
```

- Reads initial value from `localStorage` key `adare-theme` (default: `system`)
- On `setTheme`: writes to localStorage, applies/removes `.dark` class on `document.documentElement`
- When `system`: listens to `window.matchMedia('(prefers-color-scheme: dark)')` change events
- Resolves effective theme: if `system`, check media query; otherwise use stored value

### 3. FOUC Prevention (`index.html`)

Inline `<script>` in `<head>` before any CSS/JS loads:

```html
<script>
  (function() {
    var t = localStorage.getItem('adare-theme') || 'system';
    var dark = t === 'dark' || (t === 'system' && window.matchMedia('(prefers-color-scheme: dark)').matches);
    if (dark) document.documentElement.classList.add('dark');
  })();
</script>
```

### 4. Theme Toggle Component (`components/ui/theme-toggle.tsx`)

A segmented pill with 3 options using `lucide-react` icons:
- Sun icon = Light
- Moon icon = Dark  
- Monitor icon = System

Rendered inside the `UserMenu` dropdown in `header.tsx`, between Profile and Logout.

### 5. Component Updates (19 files, ~45 replacements)

Replace all hardcoded Tailwind color classes with semantic token classes:

| Hardcoded Class | Replacement |
|---|---|
| `bg-white` | `bg-card` (page sections, cards) or `bg-popover` (dropdown menus, floating panels) |
| `text-gray-700`, `text-gray-900` | `text-foreground` or `text-popover-foreground` |
| `text-gray-500`, `text-gray-600` | `text-muted-foreground` |
| `bg-gray-100` (hover) | `bg-muted` or `bg-accent` |
| `border-gray-*` | `border-border` |
| `hover:bg-gray-100` | `hover:bg-accent` |
| `shadow-lg border` (dropdowns) | `shadow-lg border-border` |

**Files to update:**
- `components/layout/header.tsx` (12 occurrences) -- dropdown menus, user button, nav items
- `components/profile/profile-card.tsx` (5) -- card backgrounds, text colors
- `components/experiment/experiment-overview.tsx` (3) -- detail page colors
- `components/environment/environment-overview.tsx` (2) -- detail page colors
- `components/run/event-timeline.tsx` (2) -- timeline styling
- `components/data-table/data-table-panel.tsx` (2) -- table panel backgrounds
- `components/data-table/data-table-select-filter.tsx` (2) -- filter dropdown
- `components/data-table/columns/run-counts-cell.tsx` (2) -- cell backgrounds
- `components/data-table/columns/parameter-cell.tsx` (1)
- `components/data-table/columns/os-info-cell.tsx` (1)
- `components/shared/login-form.tsx` (1) -- login page
- `components/shared/status-icon.tsx` (1)
- `components/experiment/experiment-tag-cloud-view.tsx` (1)
- `components/ui/button.tsx` (1) -- ghost/outline variants
- `components/ui/badge.tsx` (2) -- badge variants
- `pages/home.tsx` (1) -- dashboard background
- `constants/tag-colors.ts` (4) -- tag color definitions use `bg-*-800 text-white` which work in both modes
- `constants/mappings.ts` (1)

**Tag colors** (`bg-blue-800 text-white`, `bg-green-800 text-white`, etc.) are already high-contrast and work well on both light and dark backgrounds. No changes needed.

## Verification

1. Run `npm run dev` and toggle between Light / Dark / System modes
2. Verify FOUC prevention: hard-refresh in dark mode -- page should not flash white
3. Check all pages (home, experiments, runs, environments, testfunctionsets, profile, login) in both modes
4. Verify system preference tracking: change OS dark mode setting while app is open with "System" selected
5. Verify localStorage persistence: select Dark, close tab, reopen -- should stay dark
6. Check dropdown menus, popovers, and data tables for proper dark styling
7. Verify WCAG AA contrast ratios on key text elements using browser dev tools

# ADARE Quasar Frontend — Discovery Platform Redesign

## Context

The ADARE platform shares experiments, environments, and test function sets for digital forensics research. The current Quasar frontend has basic list/detail pages but lacks:
- Environment detail pages (list only)
- Cross-referencing between entities (can't see which experiments use an environment)
- Structural search (only basic text search + one tag multi-select on experiments)
- Scoped tagging (tags are flat strings, no way to filter by tool, artifact, or goal)

The platform serves both researchers and tool developers who need to discover, compare, and group experiments by tool, artifact, environment, or research goal.

## Design: Enhanced Tables + Faceted Sidebar

Build on the existing DataTable infrastructure. Add a filter sidebar with scoped tag facets, cross-reference sections on detail pages, a dashboard homepage, and a new environment detail page.

---

## 1. Scoped Tag Model

### Backend

**TagScope model** (new):
- `name: CharField(unique, max_length=50)` — e.g. "tool", "artifact", "goal", "os"
- `is_predefined: BooleanField(default=False)` — predefined scopes appear first in UI
- `color: CharField(max_length=7, blank=True)` — optional hex color for frontend display

**Tag model** (modified):
- `scope: ForeignKey(TagScope, null=True, blank=True, on_delete=SET_NULL)` — the namespace
- `value: CharField(max_length=100)` — the tag value (e.g. "Autopsy", "trash-bin")
- `name` field kept for backwards compatibility, auto-generated as `scope:value` or just `value` if unscoped
- Unique constraint on `(scope, value)`

**Migration path**: Existing tags without `:` keep `scope=null`. Tags containing `:` are split into scope+value during migration. Seed predefined scopes: `tool`, `artifact`, `goal`.

**Tags on TestFunctionSet**: Add M2M `tags` field to `TestfunctionSet` model (currently only Experiment and Environment have tags).

**Serializer changes**:
- `TagSerializer` exposes: `name` (full `scope:value` string), `scope` (scope name or null), `value`, `color`
- `filteroptions/` endpoints return tags grouped by scope:
  ```json
  {
    "tags_by_scope": {
      "tool": [{"value": "Autopsy", "count": 12}, ...],
      "artifact": [{"value": "trash-bin", "count": 5}, ...],
      "goal": [{"value": "tool-test", "count": 15}, ...],
      "null": [{"value": "windows-10", "count": 11}, ...]
    }
  }
  ```

**Filter changes**:
- Add `tag_scope` filter parameter: `?tag_scope=tool&tag_value=Autopsy`
- Keep existing `tags_mc` for backwards compatibility
- Add scope-aware filter: `?tags_scoped=tool:Autopsy,goal:tool-test` (comma-separated)

### Frontend

- Tag badges color-coded by scope (blue=tool, green=artifact, purple=goal, gray=unscoped)
- Colors come from `TagScope.color` or fall back to a default palette
- `DataTableTags` component updated to render scoped badges
- New `ScopedTagBadge` component for consistent tag display across pages

---

## 2. Dashboard Homepage

Replace the current `HomePage` (WelcomeCard) with a dashboard at `/home`.

**Sections:**
1. **Stats cards row** — 4 cards: Experiments, Environments, Test Function Sets, Runs (with success/fail split). Data from existing `/api/stats/` endpoint.
2. **Quick search bar** — text input that navigates to the relevant list page with search pre-filled. Type toggle chips (Experiments | Environments | Test Sets) to choose which list page.
3. **Recent items** — two-column grid:
   - Left: Recent Experiments (3-5 items, name + author + date + top tags, link to detail)
   - Right: Recent Environments (3-5 items, name + OS + experiment count, link to detail)
   - Each section has "View all →" link to the full list page
4. **Popular tags** — clickable tag cloud showing most-used scoped tags with counts. Clicking navigates to the experiment list pre-filtered by that tag.

**Data sources**: Stats endpoint + experiment list (sorted by `-published_at`, limit 5) + environment list (sorted by `-published_at`, limit 5) + filter options (for tag counts).

**Components**: New `DashboardPage.vue` replacing current `HomePage.vue`. Reuses existing stores (`useStatsStore`, `useExperimentStore`, `useEnvironmentStore`).

---

## 3. List Page Layout — Faceted Sidebar

Add a collapsible filter sidebar to Experiment, Environment, and TestFunctionSet list pages.

### Sidebar Component: `FilterSidebar.vue`

**Structure:**
- Collapsible left drawer (Quasar `q-drawer` with `v-model`)
- Header with "Filters" title and tag search input
- Collapsible sections per tag scope (Quasar `q-expansion-item`)
- Each section shows checkboxes with result counts
- Sections auto-populated from `filteroptions/` API response grouped by scope

**Per-page filter sections:**

| Section | Experiments | Environments | TestFunctionSets |
|---------|-------------|--------------|------------------|
| Tool tags | ✓ | ✓ | ✓ |
| Artifact tags | ✓ | ✓ | ✓ |
| Goal tags | ✓ | ✓ | ✓ |
| Other tags | ✓ | ✓ | ✓ |
| Environment | ✓ (M2M filter) | — | — |
| Run Results | ✓ (min_runcount) | — | — |
| OS | — | ✓ (os_info filter) | — |

**Active filters bar**: Shown above the table when filters are active. Displays selected filters as dismissible chips with scope-colored badges. "Clear all" link.

**Behavior:**
- Filter counts update dynamically based on current selections (cascading facets)
- Sidebar state persisted in URL query params (shareable filtered views)
- Sidebar collapsible via toggle button (remembers state in localStorage)
- Mobile: sidebar becomes a full-overlay drawer

**Backend requirements:**
- `filteroptions/` endpoints must return tags grouped by scope (see Section 1)
- Environment filter on experiments: new `environment_mc` filter parameter
- OS filter on environments: new `os_mc` filter parameter

### Table Updates

- Existing `DataTable` and `DataTablePanel` components remain
- `DataTablePanel` simplified: search stays, column toggle stays, multi-select filter dropdowns replaced by sidebar
- Active filter chips bar added between panel and table

---

## 4. Environment Detail Page (NEW)

New page at `/environment/:name`.

**Sections:**
1. **Header card**: name, ULID, description, scoped tag badges
2. **Metadata row**: published_by (avatar + name), published_at, vagrant box (link to cloud), file link (Gitea)
3. **Two-column grid**:
   - Left: OS Info card (os, distribution, version, architecture, language)
   - Right: Post-setup installations (name, description, command for each)
4. **Cross-reference: "Experiments Using This Environment"** — table showing experiments that have this environment in their M2M, with columns: name (linked), tags, run counts, latest run status/date

**Backend requirements:**
- New API endpoint or filter: experiments filtered by environment name/ULID
- Could use existing experiment list with new `environment_mc` filter: `/api/experiment/?environment_mc=Win10-Forensic-Base`

**Frontend:**
- New `EnvironmentPage.vue` page component
- New `EnvironmentOverview.vue` component (similar pattern to `ExperimentOverview.vue`)
- Route: `/environment/:name` → `EnvironmentPage`
- Uses `useEnvironmentStore.loadEnvironmentByName()`
- Uses `useExperimentStore.fetchExperimentsAdvanced()` with environment filter for cross-reference

---

## 5. Cross-Reference Sections on Existing Detail Pages

### Experiment Detail (`ExperimentPage.vue`)

Add below existing tests table:
1. **Environments table** — list environments from the experiment's M2M relationship. Columns: name (linked to new env detail page), OS info, vagrant box. Data already available in experiment serializer (`environments` field).
2. **Recent Runs table** — last 5 runs for this experiment. Columns: ULID (linked), environment, result status, duration, date. Uses existing run list API with experiment filter.
3. **Related Experiments** — experiments sharing tags with this one (same tool or artifact). Columns: name, shared tags, run counts. Uses experiment list API with tag filters.

### TestFunctionSet Detail (`TestfunctionsetDetailsPage.vue`)

Add below existing testfunctions table:
1. **Experiments Using These Functions** — experiments whose abstract_tests reference testfunctions from this set. Columns: name (linked), matching tests count, tags, run counts.
   - Backend: new filter or endpoint to find experiments by testfunction_set name
   - Traversal: Experiment → abstract_tests → testfunction → testfunction_set

---

## 6. Backend API Changes Summary

| Change | Type | Endpoint |
|--------|------|----------|
| TagScope model | New model | — |
| Tag.scope field | Migration | — |
| Tags on TestFunctionSet | Migration | — |
| Tags grouped by scope | Modified | `GET /api/*/filteroptions/` |
| Scoped tag filter | Modified | `?tags_scoped=scope:value,...` |
| Environment filter on experiments | New filter | `?environment_mc=name` |
| OS filter on environments | New filter | `?os_mc=Windows` |
| Experiments by testfunction set | New filter | `?testfunction_set=name` |
| Environment detail by name | New URL wiring | `GET /api/environment/<name>/` — `EnvironmentView` class exists in views.py but is not wired in urls.py |
| Recent experiments/environments | Existing | `GET /api/experiment/?ordering=-published_at&limit=5` |

---

## 7. Frontend File Changes Summary

| File | Action | Purpose |
|------|--------|---------|
| `pages/HomePage.vue` | Rewrite | Dashboard with stats, recent items, popular tags |
| `pages/EnvironmentPage.vue` | New | Environment detail page |
| `components/EnvironmentOverview.vue` | New | Environment detail content |
| `components/FilterSidebar.vue` | New | Reusable faceted filter sidebar |
| `components/ActiveFilters.vue` | New | Active filter chips bar |
| `components/ScopedTagBadge.vue` | New | Scoped tag badge (scope-colored) |
| `components/datatable/DataTableTags.vue` | Modify | Use ScopedTagBadge, show scope colors |
| `components/datatable/DataTablePanel.vue` | Modify | Remove inline multi-select, integrate with sidebar |
| `pages/ExperimentListPage.vue` | Modify | Add FilterSidebar, pass filters to store |
| `pages/EnvironmentListPage.vue` | Modify | Add FilterSidebar |
| `pages/TestfunctionsetListPage.vue` | Modify | Add FilterSidebar |
| `pages/ExperimentPage.vue` | Modify | Add environments table, runs table, related experiments |
| `pages/TestfunctionsetDetailsPage.vue` | Modify | Add experiments-using section |
| `store/experiment.ts` | Modify | Support new filter params (environment_mc, tags_scoped) |
| `store/environment.ts` | Modify | Support new filter params, loadByName |
| `store/storeUtils.ts` | Modify | Handle scoped tag filter serialization |
| `models/index.ts` | Modify | Update Tag type (add scope, value, color) |
| `router/routes.ts` | Modify | Add `/environment/:name` route |
| `constants/tagColors.ts` | New | Default color palette for tag scopes |

---

## 8. Quasar Component Mapping

All UI uses existing Quasar components — no custom CSS framework:

| Design element | Quasar component |
|---------------|-----------------|
| Filter sidebar | `q-drawer` (mini mode capable) |
| Filter sections | `q-expansion-item` |
| Filter checkboxes | `q-checkbox` |
| Active filter chips | `q-chip` (removable) |
| Tag badges | `q-badge` with dynamic color |
| Stats cards | `q-card` in grid |
| Search bar | `q-input` with prepend icon |
| Detail page cards | `q-card` with `q-card-section` |
| Data tables | existing `DataTable` component |
| OS info table | `q-markup-table` |
| Popular tags | `q-chip` (clickable) |

---

## 9. Verification Plan

### Backend
1. Run migrations, verify TagScope and Tag schema changes
2. Run existing tests — they should still pass (Tag.name preserved)
3. Test `filteroptions/` returns tags grouped by scope
4. Test new filter params: `environment_mc`, `os_mc`, `tags_scoped`, `testfunction_set`
5. Test environment detail API returns full data

### Frontend
1. **Dashboard**: verify stats load, recent items render, tag cloud links navigate correctly
2. **List pages**: verify sidebar renders scope sections, checkboxes filter the table, active filters bar works, URL params are shareable
3. **Environment detail**: verify all sections render, cross-reference table loads experiments
4. **Experiment detail**: verify new environments/runs/related sections render
5. **TestFunctionSet detail**: verify experiments-using section renders
6. **Tag badges**: verify scope colors display correctly across all pages
7. **Mobile**: verify sidebar collapses to overlay drawer
8. **Run `podman compose up`** and test end-to-end in dev environment

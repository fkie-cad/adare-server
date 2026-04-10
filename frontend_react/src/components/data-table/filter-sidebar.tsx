import { useState } from 'react'
import { X, Search, ChevronDown, ChevronRight } from 'lucide-react'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'

export interface TagOption {
  value: string
  name: string
  count: number
}

export interface TagsByScope {
  [scope: string]: TagOption[]
}

interface FilterSidebarProps {
  open: boolean
  onClose: () => void
  tagsByScope: TagsByScope
  selectedTags: string[]
  onSelectedTagsChange: (tags: string[]) => void
  children?: React.ReactNode
}

export function FilterSidebar({
  open,
  onClose,
  tagsByScope,
  selectedTags,
  onSelectedTagsChange,
  children,
}: FilterSidebarProps) {
  const [tagSearch, setTagSearch] = useState('')
  const [collapsedScopes, setCollapsedScopes] = useState<Set<string>>(new Set())

  if (!open) return null

  const filteredTagsByScope: TagsByScope = {}
  for (const [scope, tags] of Object.entries(tagsByScope)) {
    const filtered = tags.filter(
      (tag) => !tagSearch || tag.value.toLowerCase().includes(tagSearch.toLowerCase()),
    )
    if (filtered.length > 0) {
      filteredTagsByScope[scope] = filtered
    }
  }

  function toggleTag(tagName: string) {
    const next = selectedTags.includes(tagName)
      ? selectedTags.filter((t) => t !== tagName)
      : [...selectedTags, tagName]
    onSelectedTagsChange(next)
  }

  function toggleScope(scope: string) {
    const next = new Set(collapsedScopes)
    if (next.has(scope)) {
      next.delete(scope)
    } else {
      next.add(scope)
    }
    setCollapsedScopes(next)
  }

  return (
    <div className="w-64 bg-sidebar border-r border-sidebar-border shrink-0 overflow-y-auto sticky top-0 h-[calc(100vh-3.5rem)] shadow-[1px_0_3px_0_rgba(0,0,0,0.04)]">
      <div className="p-4">
        <div className="flex items-center justify-between pb-3 border-b border-sidebar-border mb-3">
          <span className="text-sm font-semibold uppercase tracking-wide text-sidebar-accent-foreground">Filters</span>
          <Button variant="ghost" size="icon" className="h-6 w-6" onClick={onClose}>
            <X className="h-4 w-4" />
          </Button>
        </div>

        <div className="relative mb-4">
          <Search className="absolute left-2 top-2 h-3.5 w-3.5 text-muted-foreground" />
          <Input
            placeholder="Filter tags..."
            value={tagSearch}
            onChange={(e) => setTagSearch(e.target.value)}
            className="pl-7 h-8 text-sm"
          />
        </div>

        {Object.entries(filteredTagsByScope).map(([scope, tags]) => (
          <div key={scope} className="mb-3">
            <button
              onClick={() => toggleScope(scope)}
              className="flex items-center gap-1 w-full text-left text-xs font-bold uppercase tracking-wider text-muted-foreground mb-1 hover:text-foreground py-1 px-1 -mx-1 rounded hover:bg-sidebar-accent"
            >
              {collapsedScopes.has(scope) ? (
                <ChevronRight className="h-3 w-3" />
              ) : (
                <ChevronDown className="h-3 w-3" />
              )}
              {scope === 'unscoped' ? 'Other Tags' : scope}
            </button>
            {!collapsedScopes.has(scope) && (
              <div className="pl-4 space-y-0.5">
                {tags.map((tag) => (
                  <label
                    key={tag.name}
                    className={`flex items-center gap-2 text-sm cursor-pointer hover:bg-sidebar-accent/50 rounded px-1 py-0.5 ${selectedTags.includes(tag.name) ? 'bg-sidebar-accent/30' : ''}`}
                  >
                    <input
                      type="checkbox"
                      checked={selectedTags.includes(tag.name)}
                      onChange={() => toggleTag(tag.name)}
                      className="rounded"
                    />
                    <span className="flex-1 truncate">{tag.value}</span>
                    <span className="text-xs text-muted-foreground">({tag.count})</span>
                  </label>
                ))}
              </div>
            )}
          </div>
        ))}

        {children}
      </div>
    </div>
  )
}

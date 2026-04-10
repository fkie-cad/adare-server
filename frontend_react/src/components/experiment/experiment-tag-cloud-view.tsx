import { Badge } from '@/components/ui/badge'
import { Card, CardContent } from '@/components/ui/card'
import { getTagColorClass } from '@/constants/tag-colors'
import type { TagsByScope } from '@/components/data-table/filter-sidebar'

const SIZE_CLASSES = ['text-xs', 'text-sm', 'text-base', 'text-lg', 'text-xl'] as const

function tagSizeClass(count: number, max: number): string {
  if (max <= 1) return SIZE_CLASSES[2]
  const idx = count === max
    ? SIZE_CLASSES.length - 1
    : Math.floor((count / max) * (SIZE_CLASSES.length - 1))
  return SIZE_CLASSES[idx]
}

const SCOPE_LABELS: Record<string, string> = {
  tool: 'Tools',
  artifact: 'Artifacts',
  goal: 'Goals',
  unscoped: 'Other Tags',
}

interface ExperimentTagCloudViewProps {
  tagsByScope: TagsByScope
  selectedTags: string[]
  onTagClick: (tagName: string) => void
}

export function ExperimentTagCloudView({ tagsByScope, selectedTags, onTagClick }: ExperimentTagCloudViewProps) {
  const scopes = Object.entries(tagsByScope)

  if (scopes.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6 pb-6 text-center text-muted-foreground">
          No tags available.
        </CardContent>
      </Card>
    )
  }

  return (
    <div className="space-y-4">
      {/* Summary */}
      <Card>
        <CardContent className="pt-4 pb-4">
          <div className="flex gap-6 items-center">
            <div>
              <span className="text-2xl font-bold text-foreground">
                {scopes.reduce((acc, [, tags]) => acc + tags.length, 0)}
              </span>
              <span className="text-sm text-muted-foreground ml-2">unique tags</span>
            </div>
            {scopes.map(([scope, tags]) => (
              <div key={scope} className="flex items-center gap-1.5">
                <div className={`w-2.5 h-2.5 rounded-full ${getTagColorClass(scope === 'unscoped' ? null : scope).split(' ')[0]}`} />
                <span className="text-sm text-muted-foreground">
                  {tags.length} {SCOPE_LABELS[scope] ?? scope}
                </span>
              </div>
            ))}
          </div>
        </CardContent>
      </Card>

      {/* Tag groups */}
      <div className="grid grid-cols-1 md:grid-cols-3 gap-4">
        {scopes.map(([scope, tags]) => {
          const maxCount = Math.max(...tags.map((t) => t.count))
          const scopeColor = scope === 'unscoped' ? null : scope

          return (
            <Card key={scope}>
              <CardContent className="pt-4 pb-4">
                <div className="flex items-center gap-2 mb-3">
                  <div className={`w-2.5 h-2.5 rounded-full ${getTagColorClass(scopeColor).split(' ')[0]}`} />
                  <span className="text-xs font-bold uppercase tracking-wider text-muted-foreground">
                    {SCOPE_LABELS[scope] ?? scope}
                  </span>
                  <span className="text-xs text-muted-foreground ml-auto">{tags.length} tags</span>
                </div>
                <div className="flex flex-wrap gap-2">
                  {tags.map((tag) => {
                    const isSelected = selectedTags.includes(tag.name)
                    return (
                      <Badge
                        key={tag.name}
                        className={`${getTagColorClass(scopeColor)} ${tagSizeClass(tag.count, maxCount)} cursor-pointer transition-all hover:opacity-80 ${isSelected ? 'ring-2 ring-offset-1 ring-primary' : ''}`}
                        onClick={() => onTagClick(tag.name)}
                      >
                        {tag.value}
                        <span className="ml-1.5 bg-white/20 rounded-full px-1.5 text-xs">{tag.count}</span>
                      </Badge>
                    )
                  })}
                </div>
              </CardContent>
            </Card>
          )
        })}
      </div>
    </div>
  )
}

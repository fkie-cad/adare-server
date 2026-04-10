import { X } from 'lucide-react'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { getTagColorClass, getTagScope } from '@/constants/tag-colors'

interface ActiveFiltersProps {
  selectedTags: string[]
  onRemove: (tag: string) => void
  onClear: () => void
}

export function ActiveFilters({ selectedTags, onRemove, onClear }: ActiveFiltersProps) {
  if (selectedTags.length === 0) return null

  return (
    <div className="flex items-center gap-2 flex-wrap">
      <span className="text-xs text-muted-foreground">Active:</span>
      {selectedTags.map((tag) => (
        <Badge
          key={tag}
          className={`${getTagColorClass(getTagScope(tag))} gap-1 cursor-pointer`}
          onClick={() => onRemove(tag)}
        >
          {tag}
          <X className="h-3 w-3" />
        </Badge>
      ))}
      <Button variant="link" size="sm" className="h-auto p-0 text-xs" onClick={onClear}>
        Clear all
      </Button>
    </div>
  )
}

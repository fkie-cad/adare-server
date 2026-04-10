import type { Tag } from '@/types/experiment'
import { Badge } from '@/components/ui/badge'
import { getTagColorClass, getTagScope } from '@/constants/tag-colors'

interface TagsCellProps {
  tags: Tag[]
}

export function TagsCell({ tags }: TagsCellProps) {
  if (!tags?.length) return null

  return (
    <div className="flex flex-wrap gap-1">
      {tags.map((tag) => (
        <Badge key={tag.name} className={`${getTagColorClass(getTagScope(tag.name))} text-xs`}>
          #{tag.name}
        </Badge>
      ))}
    </div>
  )
}

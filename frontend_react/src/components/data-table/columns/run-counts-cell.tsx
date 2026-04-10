import type { RunCount } from '@/types/experiment'
import { Badge } from '@/components/ui/badge'

interface RunCountsCellProps {
  counts: RunCount
}

export function RunCountsCell({ counts }: RunCountsCellProps) {
  if (!counts) return null

  return (
    <div className="flex gap-1">
      <Badge className="bg-green-500 text-white">{counts.successful}</Badge>
      <Badge className="bg-red-500 text-white">{counts.failed}</Badge>
    </div>
  )
}

import type { RunCount } from '@/types/experiment'
import { Badge } from '@/components/ui/badge'

interface RunCountsCellProps {
  counts: RunCount
}

export function RunCountsCell({ counts }: RunCountsCellProps) {
  if (!counts) return null

  return (
    <div className="flex gap-1">
      <Badge variant="success" className="font-mono tabular-nums">{counts.successful}</Badge>
      <Badge variant="destructive" className="font-mono tabular-nums">{counts.failed}</Badge>
    </div>
  )
}

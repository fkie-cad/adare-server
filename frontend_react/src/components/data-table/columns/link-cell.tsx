import { ExternalLink } from 'lucide-react'
import { Tooltip } from '@/components/ui/tooltip'

interface LinkCellProps {
  url: string | null | undefined
  tooltip?: string
}

export function LinkCell({ url, tooltip = 'Open in new tab' }: LinkCellProps) {
  if (!url) return null

  return (
    <Tooltip content={tooltip}>
      <a
        href={url}
        target="_blank"
        rel="noopener noreferrer"
        className="inline-flex items-center text-primary hover:text-primary/80"
      >
        <ExternalLink className="w-4 h-4" />
      </a>
    </Tooltip>
  )
}

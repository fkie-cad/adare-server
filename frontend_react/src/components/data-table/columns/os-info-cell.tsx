import type { OsInfo } from '@/types/experiment'
import { Monitor } from 'lucide-react'
import { Tooltip } from '@/components/ui/tooltip'
import { osColorMapping, isValidOSListType, type OSListType } from '@/constants/mappings'
import { cn } from '@/lib/utils'

interface OsInfoCellProps {
  osInfo: OsInfo
}

export function OsInfoCell({ osInfo }: OsInfoCellProps) {
  if (!osInfo) return null

  const osType = osInfo.os?.toLowerCase()
  const colorClass = isValidOSListType(osType) ? osColorMapping[osType as OSListType] : 'text-muted-foreground'

  const tooltipContent = [
    osInfo.version && `Version: ${osInfo.version}`,
    osInfo.language && `Language: ${osInfo.language}`,
    osInfo.architecture && `Arch: ${osInfo.architecture}`,
    osInfo.details && `Details: ${osInfo.details}`,
  ]
    .filter(Boolean)
    .join('\n')

  return (
    <Tooltip content={tooltipContent || osInfo.distribution}>
      <span className={cn('flex items-center gap-1.5', colorClass)}>
        <Monitor className="w-4 h-4" />
        <span className="text-sm">{osInfo.distribution}</span>
      </span>
    </Tooltip>
  )
}

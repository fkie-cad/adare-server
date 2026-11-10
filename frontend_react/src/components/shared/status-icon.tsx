import {
  statusColorMapping,
  statusIconMapping,
  statusTooltipMapping,
  defaultStatusIcon,
  isValidStatusType,
  type StatusType,
} from '@/constants/mappings'
import { Tooltip } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

interface StatusIconProps {
  status: string
  size?: string
  showTooltip?: boolean
}

export function StatusIcon({ status, size = 'w-6 h-6', showTooltip = true }: StatusIconProps) {
  const valid = isValidStatusType(status)
  const Icon = valid ? statusIconMapping[status as StatusType] : defaultStatusIcon
  const colorClass = valid ? statusColorMapping[status as StatusType] : 'text-muted-foreground'

  const icon = <Icon className={cn(size, colorClass)} />

  if (showTooltip) {
    const tooltip = (valid && statusTooltipMapping[status as StatusType]) || status
    return <Tooltip content={tooltip}>{icon}</Tooltip>
  }

  return icon
}

import type { Parameter } from '@/types/experiment'
import { Badge } from '@/components/ui/badge'
import { Tooltip } from '@/components/ui/tooltip'
import { dtypeColorMapping, isValidDtype } from '@/constants/mappings'

interface ParameterCellProps {
  parameters: Parameter[]
}

export function ParameterCell({ parameters }: ParameterCellProps) {
  if (!parameters?.length) return null

  return (
    <div className="flex flex-wrap gap-1">
      {parameters.map((param) => {
        const dtype = param.parameter.dtype
        const colorClass = isValidDtype(dtype) ? dtypeColorMapping[dtype as keyof typeof dtypeColorMapping] : 'bg-muted text-muted-foreground'
        return (
          <Tooltip key={param.parameter.name} content={param.parameter.description}>
            <span className="inline-flex items-center gap-1">
              <Badge className={colorClass}>{param.parameter.name}</Badge>
              <span className="text-sm">{param.value}</span>
            </span>
          </Tooltip>
        )
      })}
    </div>
  )
}

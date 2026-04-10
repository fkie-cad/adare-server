import type { Status } from '@/types/experiment'
import { StatusIcon } from '@/components/shared/status-icon'

interface StatusCellProps {
  status: Status
}

export function StatusCell({ status }: StatusCellProps) {
  return <StatusIcon status={status.name} />
}

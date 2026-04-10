import { Link } from '@tanstack/react-router'
import { PlusCircle } from 'lucide-react'
import { Tooltip } from '@/components/ui/tooltip'

interface DetailsCellProps {
  to: string
}

export function DetailsCell({ to }: DetailsCellProps) {
  return (
    <Tooltip content="View details">
      <Link to={to} className="text-muted-foreground hover:text-primary">
        <PlusCircle className="w-5 h-5" />
      </Link>
    </Tooltip>
  )
}

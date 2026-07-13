import type { Environment } from '@/types/experiment'
import { Badge } from '@/components/ui/badge'

interface SourceKindCellProps {
  environment: Pick<Environment, 'recipe' | 'vagrantbox'>
}

export function SourceKindCell({ environment }: SourceKindCellProps) {
  const kind = environment.recipe ? 'Recipe' : environment.vagrantbox ? 'Vagrant' : 'Baked'
  const variant = kind === 'Recipe' ? 'success' : kind === 'Vagrant' ? 'secondary' : 'outline'

  return <Badge variant={variant}>{kind}</Badge>
}

import type { Environment } from '@/types/experiment'
import { Badge } from '@/components/ui/badge'

interface SourceKindCellProps {
  environment: Pick<Environment, 'recipe' | 'vagrantbox'>
}

export function SourceKindCell({ environment }: SourceKindCellProps) {
  const kind = environment.recipe ? 'Recipe' : environment.vagrantbox ? 'Vagrant' : 'Baked'
  const variant = kind === 'Recipe' ? 'success' : kind === 'Vagrant' ? 'secondary' : 'outline'
  // A BYO ('bring your own') recipe has no ISO URL: the consumer must supply the
  // ISO locally before it can build, which is worth flagging in a list view.
  const isByoIso = Boolean(environment.recipe && !environment.recipe.iso && environment.recipe.iso_name)
  const provisionCount = environment.recipe?.provision?.length ?? 0

  return (
    <div className="flex flex-wrap items-center gap-1">
      <Badge variant={variant}>{kind}</Badge>
      {isByoIso && (
        <Badge variant="outline" title="you supply the ISO locally">
          BYO ISO
        </Badge>
      )}
      {provisionCount > 0 && (
        <Badge variant="outline" title="build-time provisioning steps">
          +{provisionCount} provisioned
        </Badge>
      )}
    </div>
  )
}

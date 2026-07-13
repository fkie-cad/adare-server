import { useParams } from '@tanstack/react-router'
import { Loader2 } from 'lucide-react'
import { useTestfunctionSet } from '@/api/hooks/use-testfunction-sets'
import { useUserProfile } from '@/api/hooks/use-user'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { ProfileImage } from '@/components/profile/profile-image'
import { EntityActions } from '@/components/entity-actions'
import { LinkCell } from '@/components/data-table/columns/link-cell'
import { PageContainer } from '@/components/layout/page-container'

export default function TestfunctionSetDetailPage() {
  const { name } = useParams({ strict: false }) as { name: string }
  const { data: tfSet, isLoading } = useTestfunctionSet(name)
  const { data: publishedByProfile } = useUserProfile(tfSet?.published_by ?? '')
  const { data: createdByProfile } = useUserProfile(tfSet?.created_by ?? '')

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  if (!tfSet) {
    return (
      <PageContainer className="max-w-4xl">
        <Card>
          <CardContent className="py-6">
            <p>Testfunction set not found</p>
          </CardContent>
        </Card>
      </PageContainer>
    )
  }

  return (
    <PageContainer className="max-w-4xl">
    <Card>
      <CardContent className="space-y-6 pt-6">
        <div className="flex justify-end">
          <EntityActions
            entity="testfunction"
            name={tfSet.name}
            editTo="/testfunctionset/$name/edit"
          />
        </div>

        <div className="flex justify-between">
          <div>
            <div className="text-sm text-muted-foreground">name</div>
            <div className="font-display text-2xl font-semibold tracking-tight">{tfSet.name}</div>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground">functions</div>
            <div className="font-mono text-2xl font-semibold tabular-nums text-primary">
              {tfSet.num_testfunctions}
            </div>
          </div>
        </div>

        {tfSet.description && (
          <div>
            <div className="text-sm text-muted-foreground">description</div>
            <p>{tfSet.description}</p>
          </div>
        )}

        <div className="flex justify-between">
          <div>
            <div className="text-sm text-muted-foreground mb-1">created by</div>
            {createdByProfile && (
              <ProfileImage profile={createdByProfile} size="md" showTooltip linkToProfile />
            )}
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground mb-1">published by</div>
            {publishedByProfile && (
              <ProfileImage profile={publishedByProfile} size="md" showTooltip linkToProfile />
            )}
          </div>
        </div>

        <div className="flex gap-4">
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">File:</span>
            <LinkCell url={tfSet.file} tooltip="Open in Gitea" />
          </div>
          <div className="flex items-center gap-2">
            <span className="text-sm text-muted-foreground">Requirements:</span>
            <LinkCell url={tfSet.requirements_file} tooltip="Open in Gitea" />
          </div>
        </div>

        {tfSet.testfunctions?.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold mb-3">Testfunctions</h3>
            <div className="rounded-md border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left p-2 font-medium">Name</th>
                    <th className="text-left p-2 font-medium">Description</th>
                    <th className="text-left p-2 font-medium">Parameters</th>
                  </tr>
                </thead>
                <tbody>
                  {tfSet.testfunctions.map((tf) => (
                    <tr key={tf.name} className="border-b">
                      <td className="p-2">{tf.name}</td>
                      <td className="p-2">{tf.description}</td>
                      <td className="p-2">
                        <div className="flex flex-wrap gap-1">
                          {tf.possible_parameters.map((p) => (
                            <Badge key={p.name} variant="secondary">
                              {p.name} ({p.dtype})
                            </Badge>
                          ))}
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          </div>
        )}
      </CardContent>
    </Card>
    </PageContainer>
  )
}

import { ExternalLink } from 'lucide-react'
import { useExperiment } from '@/api/hooks/use-experiments'
import { useUserProfile } from '@/api/hooks/use-user'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ProfileImage } from '@/components/profile/profile-image'
import { ParameterCell } from '@/components/data-table/columns/parameter-cell'
import { TestfunctionCell } from '@/components/data-table/columns/testfunction-cell'
import { Loader2 } from 'lucide-react'

interface ExperimentOverviewProps {
  name: string
}

export function ExperimentOverview({ name }: ExperimentOverviewProps) {
  const { data: experiment, isLoading } = useExperiment(name)
  const { data: createdByProfile } = useUserProfile(experiment?.created_by ?? '')
  const { data: publishedByProfile } = useUserProfile(experiment?.published_by ?? '')

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  if (!experiment) {
    return (
      <Card>
        <CardContent className="py-6">
          <p className="text-lg">Experiment not found</p>
        </CardContent>
      </Card>
    )
  }

  const giteaUrl = experiment.action_file?.split('/').slice(0, -1).join('/')

  return (
    <Card>
      <CardContent className="space-y-6 pt-6">
        {/* Name + ULID */}
        <div>
          <div className="flex justify-between text-sm text-muted-foreground">
            <span>name</span>
            <span>ulid</span>
          </div>
          <div className="flex justify-between items-start text-2xl">
            <div className="flex items-center gap-1">
              {experiment.name}
              {giteaUrl && (
                <Button variant="ghost" size="icon" className="h-6 w-6" asChild>
                  <a href={giteaUrl} target="_blank" rel="noopener noreferrer">
                    <ExternalLink className="w-3.5 h-3.5" />
                  </a>
                </Button>
              )}
            </div>
            <span className="text-right">{experiment.ulid}</span>
          </div>
        </div>

        {/* Description */}
        {experiment.description && (
          <div>
            <div className="text-sm text-muted-foreground">description</div>
            <p>{experiment.description}</p>
          </div>
        )}

        {/* Tags + Run counts */}
        {experiment.tags && (
          <div className="flex justify-between items-start">
            <div>
              <div className="text-sm text-muted-foreground mb-1">tags</div>
              <div className="flex flex-wrap gap-1">
                {experiment.tags.map((tag) => (
                  <Badge key={tag.name} className="bg-pink-700 text-white">
                    #{tag.name}
                  </Badge>
                ))}
              </div>
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground mb-1">run counts</div>
              <div className="flex gap-2 justify-end">
                <Badge className="bg-green-500 text-white text-lg px-3">
                  {experiment.run_counts.successful}
                </Badge>
                <Badge className="bg-red-500 text-white text-lg px-3">
                  {experiment.run_counts.failed}
                </Badge>
              </div>
            </div>
          </div>
        )}

        {/* Created by / Published by */}
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

        {/* Tests table */}
        {experiment.abstract_tests?.length > 0 && (
          <div>
            <h3 className="text-lg font-semibold mb-3">Tests</h3>
            <div className="rounded-md border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left p-2 font-medium">Name</th>
                    <th className="text-left p-2 font-medium">Description</th>
                    <th className="text-left p-2 font-medium">Testfunction</th>
                    <th className="text-left p-2 font-medium">Parameters</th>
                  </tr>
                </thead>
                <tbody>
                  {experiment.abstract_tests.map((test) => (
                    <tr key={test.ulid} className="border-b">
                      <td className="p-2">{test.name}</td>
                      <td className="p-2">{test.description}</td>
                      <td className="p-2">
                        <TestfunctionCell testfunction={test.testfunction} />
                      </td>
                      <td className="p-2">
                        <ParameterCell parameters={test.parameters} />
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
  )
}

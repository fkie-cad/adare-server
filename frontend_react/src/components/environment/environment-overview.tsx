import { ExternalLink, Loader2 } from 'lucide-react'
import { Link } from '@tanstack/react-router'
import { useEnvironment } from '@/api/hooks/use-environments'
import { useExperiments } from '@/api/hooks/use-experiments'
import { useUserProfile } from '@/api/hooks/use-user'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { ProfileImage } from '@/components/profile/profile-image'
import { getTagColorClass, getTagScope } from '@/constants/tag-colors'

interface EnvironmentOverviewProps {
  name: string
}

export function EnvironmentOverview({ name }: EnvironmentOverviewProps) {
  const { data: environment, isLoading } = useEnvironment(name)
  const { data: createdByProfile } = useUserProfile(environment?.created_by ?? '')
  const { data: publishedByProfile } = useUserProfile(environment?.published_by ?? '')

  const { data: relatedExperimentsData } = useExperiments({
    limit: 20,
    sortBy: 'published_at',
    descending: true,
    filters: environment ? `environment_mc=${name}` : undefined,
  })
  const relatedExperiments = relatedExperimentsData?.results ?? []

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  if (!environment) {
    return (
      <Card>
        <CardContent className="py-6">
          <p className="text-lg">Environment not found</p>
        </CardContent>
      </Card>
    )
  }

  const vagrantCloudUrl = environment.vagrantbox
    ? `https://app.vagrantup.com/${environment.vagrantbox}`
    : null

  return (
    <div className="space-y-4">
      {/* Header card */}
      <Card>
        <CardContent className="space-y-6 pt-6">
          {/* Name + ULID */}
          <div>
            <div className="flex justify-between text-sm text-muted-foreground">
              <span>name</span>
              <span>ulid</span>
            </div>
            <div className="flex justify-between items-start gap-4">
              <div className="flex items-center gap-1 font-display text-2xl font-semibold tracking-tight">
                {environment.name}
                {environment.file && (
                  <Button variant="ghost" size="icon" className="h-6 w-6" asChild>
                    <a href={environment.file} target="_blank" rel="noopener noreferrer">
                      <ExternalLink className="w-3.5 h-3.5" />
                    </a>
                  </Button>
                )}
              </div>
              <span className="text-right font-mono text-sm tabular-nums text-muted-foreground break-all">
                {environment.ulid}
              </span>
            </div>
          </div>

          {/* Description */}
          {environment.description && (
            <div>
              <div className="text-sm text-muted-foreground">description</div>
              <p>{environment.description}</p>
            </div>
          )}

          {/* Tags */}
          {environment.tags?.length > 0 && (
            <div>
              <div className="text-sm text-muted-foreground mb-1">tags</div>
              <div className="flex flex-wrap gap-1">
                {environment.tags.map((tag) => (
                  <Badge key={tag.name} className={getTagColorClass(getTagScope(tag.name))}>
                    #{tag.name}
                  </Badge>
                ))}
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

          {/* Vagrant box + Published at */}
          <div className="flex justify-between">
            <div>
              <div className="text-sm text-muted-foreground">vagrant box</div>
              {vagrantCloudUrl ? (
                <a href={vagrantCloudUrl} target="_blank" rel="noopener noreferrer" className="text-primary hover:underline">
                  {environment.vagrantbox}
                </a>
              ) : (
                <span className="text-muted-foreground">-</span>
              )}
            </div>
            <div className="text-right">
              <div className="text-sm text-muted-foreground">published at</div>
              <span className="font-mono text-sm tabular-nums">{environment.published_at}</span>
            </div>
          </div>
        </CardContent>
      </Card>

      {/* OS Info + Post-setup installations */}
      <div className="grid grid-cols-2 gap-4">
        <Card>
          <CardContent className="pt-6">
            <h3 className="text-base font-bold mb-3">Operating System</h3>
            {environment.os_info ? (
              <table className="text-sm w-full">
                <tbody>
                  {environment.os_info.os && (
                    <tr><td className="text-muted-foreground pr-4 py-0.5 w-28">OS</td><td className="font-medium">{environment.os_info.os}</td></tr>
                  )}
                  {environment.os_info.distribution && (
                    <tr><td className="text-muted-foreground pr-4 py-0.5">Distribution</td><td className="font-medium">{environment.os_info.distribution}</td></tr>
                  )}
                  {environment.os_info.version && (
                    <tr><td className="text-muted-foreground pr-4 py-0.5">Version</td><td className="font-medium">{environment.os_info.version}</td></tr>
                  )}
                  {environment.os_info.architecture && (
                    <tr><td className="text-muted-foreground pr-4 py-0.5">Architecture</td><td className="font-medium">{environment.os_info.architecture}</td></tr>
                  )}
                  {environment.os_info.language && (
                    <tr><td className="text-muted-foreground pr-4 py-0.5">Language</td><td className="font-medium">{environment.os_info.language}</td></tr>
                  )}
                </tbody>
              </table>
            ) : (
              <p className="text-muted-foreground">No OS info available</p>
            )}
          </CardContent>
        </Card>

        <Card>
          <CardContent className="pt-6">
            <h3 className="text-base font-bold mb-3">Post-Setup Installations</h3>
            {environment.postsetup_installations ? (
              <pre className="text-sm whitespace-pre-wrap bg-muted p-3 rounded-md">
                {environment.postsetup_installations}
              </pre>
            ) : (
              <p className="text-muted-foreground">No post-setup installations</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Related experiments */}
      <Card>
        <CardContent className="pt-6">
          <div className="flex items-center gap-2 mb-3">
            <h3 className="text-base font-bold">Experiments Using This Environment</h3>
            {relatedExperiments.length > 0 && (
              <Badge className="font-mono tabular-nums">{relatedExperiments.length}</Badge>
            )}
          </div>
          {relatedExperiments.length > 0 ? (
            <div className="rounded-md border">
              <table className="w-full text-sm">
                <thead>
                  <tr className="border-b bg-muted/50">
                    <th className="text-left p-2 font-medium">Experiment</th>
                    <th className="text-left p-2 font-medium">Tags</th>
                    <th className="text-center p-2 font-medium">Runs</th>
                  </tr>
                </thead>
                <tbody>
                  {relatedExperiments.map((exp) => (
                    <tr key={exp.ulid} className="border-b">
                      <td className="p-2">
                        <Link to="/experiment/$name" params={{ name: exp.name }} className="text-primary font-medium hover:underline">
                          {exp.name}
                        </Link>
                      </td>
                      <td className="p-2">
                        <div className="flex flex-wrap gap-1">
                          {exp.tags.slice(0, 3).map((tag) => (
                            <Badge key={tag.name} className={`${getTagColorClass(getTagScope(tag.name))} text-xs`}>
                              #{tag.name}
                            </Badge>
                          ))}
                        </div>
                      </td>
                      <td className="p-2 text-center">
                        <div className="flex gap-1 justify-center">
                          <Badge variant="success" className="font-mono tabular-nums">{exp.run_counts.successful}</Badge>
                          <Badge variant="destructive" className="font-mono tabular-nums">{exp.run_counts.failed}</Badge>
                        </div>
                      </td>
                    </tr>
                  ))}
                </tbody>
              </table>
            </div>
          ) : (
            <p className="text-muted-foreground">No experiments use this environment yet.</p>
          )}
        </CardContent>
      </Card>
    </div>
  )
}

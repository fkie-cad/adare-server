import { useState } from 'react'
import { useNavigate } from '@tanstack/react-router'
import { Link } from '@tanstack/react-router'
import { Search, FlaskConical, Monitor, Boxes, PlayCircle } from 'lucide-react'
import { useStats } from '@/api/hooks/use-stats'
import { useExperiments } from '@/api/hooks/use-experiments'
import { useEnvironments } from '@/api/hooks/use-environments'
import { useExperimentFilterOptions } from '@/api/hooks/use-experiments'
import { Card, CardContent } from '@/components/ui/card'
import { Badge } from '@/components/ui/badge'
import { Button } from '@/components/ui/button'
import { Input } from '@/components/ui/input'
import { Separator } from '@/components/ui/separator'
import { getTagColorClass, getTagScope } from '@/constants/tag-colors'

interface PopularTag {
  name: string
  value: string
  scope: string | null
  count: number
}

function formatDate(dateStr: string): string {
  if (!dateStr) return ''
  const d = new Date(dateStr)
  const now = new Date()
  const diff = Math.floor((now.getTime() - d.getTime()) / (1000 * 60 * 60 * 24))
  if (diff === 0) return 'today'
  if (diff === 1) return 'yesterday'
  if (diff < 7) return `${diff} days ago`
  return d.toLocaleDateString()
}

export default function HomePage() {
  const { data: stats } = useStats()
  const [searchQuery, setSearchQuery] = useState('')
  const [searchTarget, setSearchTarget] = useState<'experiment' | 'environment' | 'testfunctionset'>('experiment')
  const navigate = useNavigate()

  const { data: recentExperimentsData } = useExperiments({
    limit: 5,
    sortBy: 'published_at',
    descending: true,
  })
  const recentExperiments = recentExperimentsData?.results ?? []

  const { data: recentEnvironmentsData } = useEnvironments({
    limit: 5,
    sortBy: 'published_at',
    descending: true,
  })
  const recentEnvironments = recentEnvironmentsData?.results ?? []

  const { data: filterOpts } = useExperimentFilterOptions()

  const popularTags: PopularTag[] = (() => {
    if (!filterOpts?.tags_by_scope) return []
    const allTags: PopularTag[] = []
    for (const [scope, tags] of Object.entries(filterOpts.tags_by_scope)) {
      for (const tag of tags as Array<{ name: string; value: string; count: number }>) {
        allTags.push({
          name: tag.name,
          value: tag.value,
          scope: scope === 'unscoped' ? null : scope,
          count: tag.count,
        })
      }
    }
    return allTags.sort((a, b) => b.count - a.count).slice(0, 12)
  })()

  function doSearch() {
    if (!searchQuery) return
    navigate({ to: `/${searchTarget}`, search: { search: searchQuery } })
  }

  const statCards = [
    { label: 'Experiments', value: stats?.experiment_count ?? 0, icon: FlaskConical, color: 'text-teal-600' },
    { label: 'Environments', value: stats?.environment_count ?? 0, icon: Monitor, color: 'text-blue-600' },
    { label: 'Test Function Sets', value: stats?.testfunction_count ?? 0, icon: Boxes, color: 'text-purple-500' },
    { label: 'Runs', value: stats?.run_count ?? 0, icon: PlayCircle, color: 'text-indigo-500' },
  ]

  const searchTargets = [
    { label: 'Experiments', value: 'experiment' as const },
    { label: 'Environments', value: 'environment' as const },
    { label: 'Test Sets', value: 'testfunctionset' as const },
  ]

  return (
    <div className="max-w-7xl mx-auto py-8 space-y-6">
      {/* Stats Cards */}
      <div className="grid grid-cols-4 gap-4">
        {statCards.map((stat) => (
          <Card key={stat.label} className="border">
            <CardContent className="pt-4 pb-4">
              <div className="text-xs uppercase text-muted-foreground tracking-wide">{stat.label}</div>
              <div className={`text-3xl font-bold ${stat.color}`}>{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Quick Search */}
      <Card className="border">
        <CardContent className="pt-4 pb-4">
          <div className="flex items-center gap-2">
            <div className="relative flex-1">
              <Search className="absolute left-2.5 top-2.5 h-4 w-4 text-muted-foreground" />
              <Input
                placeholder="Search experiments, environments, test functions..."
                value={searchQuery}
                onChange={(e) => setSearchQuery(e.target.value)}
                onKeyDown={(e) => e.key === 'Enter' && doSearch()}
                className="pl-8"
              />
            </div>
            <div className="flex gap-1">
              {searchTargets.map((t) => (
                <Button
                  key={t.value}
                  variant={searchTarget === t.value ? 'default' : 'outline'}
                  size="sm"
                  onClick={() => setSearchTarget(t.value)}
                >
                  {t.label}
                </Button>
              ))}
            </div>
          </div>
        </CardContent>
      </Card>

      {/* Recent Items */}
      <div className="grid grid-cols-2 gap-4">
        {/* Recent Experiments */}
        <Card className="border">
          <CardContent className="pt-4 pb-0">
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold">Recent Experiments</span>
              <Link to="/experiment" className="text-sm text-primary hover:underline">
                View all &rarr;
              </Link>
            </div>
          </CardContent>
          <Separator />
          <CardContent className="pt-0 pb-2">
            {recentExperiments.length > 0 ? (
              <div className="divide-y">
                {recentExperiments.map((exp) => (
                  <Link
                    key={exp.ulid}
                    to="/experiment/$name"
                    params={{ name: exp.name }}
                    className="flex items-center justify-between py-2.5 hover:bg-muted/50 -mx-2 px-2 rounded"
                  >
                    <div>
                      <div className="font-medium text-primary">{exp.name}</div>
                      <div className="text-xs text-muted-foreground">
                        by {exp.published_by} &middot; {formatDate(exp.published_at)}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      {exp.tags.slice(0, 2).map((tag) => (
                        <Badge key={tag.name} className={`${getTagColorClass(getTagScope(tag.name))} text-xs`}>
                          {tag.name}
                        </Badge>
                      ))}
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground py-3">No experiments yet</p>
            )}
          </CardContent>
        </Card>

        {/* Recent Environments */}
        <Card className="border">
          <CardContent className="pt-4 pb-0">
            <div className="flex items-center justify-between mb-2">
              <span className="font-bold">Recent Environments</span>
              <Link to="/environment" className="text-sm text-primary hover:underline">
                View all &rarr;
              </Link>
            </div>
          </CardContent>
          <Separator />
          <CardContent className="pt-0 pb-2">
            {recentEnvironments.length > 0 ? (
              <div className="divide-y">
                {recentEnvironments.map((env) => (
                  <Link
                    key={env.ulid}
                    to="/environment/$name"
                    params={{ name: env.name }}
                    className="flex items-center justify-between py-2.5 hover:bg-muted/50 -mx-2 px-2 rounded"
                  >
                    <div>
                      <div className="font-medium text-primary">{env.name}</div>
                      <div className="text-xs text-muted-foreground">
                        {env.os_info?.distribution} {env.os_info?.version}
                      </div>
                    </div>
                    <div className="flex gap-1">
                      {env.tags.slice(0, 2).map((tag) => (
                        <Badge key={tag.name} className={`${getTagColorClass(getTagScope(tag.name))} text-xs`}>
                          {tag.name}
                        </Badge>
                      ))}
                    </div>
                  </Link>
                ))}
              </div>
            ) : (
              <p className="text-sm text-muted-foreground py-3">No environments yet</p>
            )}
          </CardContent>
        </Card>
      </div>

      {/* Popular Tags */}
      {popularTags.length > 0 && (
        <Card className="border">
          <CardContent className="pt-4 pb-4">
            <div className="font-bold mb-3">Popular Tags</div>
            <div className="flex flex-wrap gap-2">
              {popularTags.map((tag) => (
                <Link
                  key={tag.name}
                  to="/experiment"
                  search={{ tags_scoped: tag.name }}
                  className="inline-flex"
                >
                  <Badge className={`${getTagColorClass(tag.scope)} cursor-pointer hover:opacity-80`}>
                    {tag.value}
                    <span className="ml-1.5 bg-white/20 rounded-full px-1.5 text-xs">{tag.count}</span>
                  </Badge>
                </Link>
              ))}
            </div>
          </CardContent>
        </Card>
      )}
    </div>
  )
}

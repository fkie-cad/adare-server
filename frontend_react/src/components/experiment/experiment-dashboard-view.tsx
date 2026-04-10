import { Link } from '@tanstack/react-router'
import { useExperimentDashboard } from '@/api/hooks/use-experiments'
import { Card, CardContent } from '@/components/ui/card'
import { Skeleton } from '@/components/ui/skeleton'

interface ExperimentDashboardViewProps {
  filters?: string
}

export function ExperimentDashboardView({ filters }: ExperimentDashboardViewProps) {
  const { data, isLoading } = useExperimentDashboard(filters)

  if (isLoading) {
    return (
      <div className="space-y-4">
        <div className="grid grid-cols-4 gap-4">
          {Array.from({ length: 4 }).map((_, i) => (
            <Card key={i}>
              <CardContent className="pt-4 pb-4">
                <Skeleton className="h-4 w-20 mb-2" />
                <Skeleton className="h-8 w-16" />
              </CardContent>
            </Card>
          ))}
        </div>
        <Card>
          <CardContent className="pt-4 pb-4 space-y-3">
            {Array.from({ length: 6 }).map((_, i) => (
              <Skeleton key={i} className="h-6 w-full" />
            ))}
          </CardContent>
        </Card>
      </div>
    )
  }

  if (!data || data.experiments.length === 0) {
    return (
      <Card>
        <CardContent className="pt-6 pb-6 text-center text-muted-foreground">
          No experiments match the current filters.
        </CardContent>
      </Card>
    )
  }

  const { experiments, summary } = data
  const maxTotal = Math.max(...experiments.map((e) => e.successful_run_count + e.failed_run_count))
  const perfectCount = experiments.filter((e) => e.failed_run_count === 0 && e.successful_run_count > 0).length

  const stats = [
    { label: 'Experiments', value: summary.total_experiments, color: 'text-primary' },
    { label: 'Total Runs', value: summary.total_runs, color: 'text-muted-foreground' },
    { label: 'Success Rate', value: `${summary.success_rate}%`, color: 'text-green-600' },
    { label: '100% Pass', value: perfectCount, color: 'text-primary' },
  ]

  return (
    <div className="space-y-4">
      {/* Summary stats */}
      <div className="grid grid-cols-4 gap-4">
        {stats.map((stat) => (
          <Card key={stat.label}>
            <CardContent className="pt-4 pb-4">
              <div className="text-xs uppercase text-muted-foreground tracking-wide">{stat.label}</div>
              <div className={`text-3xl font-bold ${stat.color}`}>{stat.value}</div>
            </CardContent>
          </Card>
        ))}
      </div>

      {/* Bar chart */}
      <Card>
        <CardContent className="pt-4 pb-4">
          <div className="space-y-1">
            {experiments.map((exp) => {
              const total = exp.successful_run_count + exp.failed_run_count
              const rate = total > 0 ? Math.round((exp.successful_run_count / total) * 100) : 0
              const barWidth = maxTotal > 0 ? (total / maxTotal) * 100 : 0

              return (
                <div key={exp.ulid} className="flex items-center gap-3 py-1 group hover:bg-muted/50 rounded px-2 -mx-2">
                  <Link
                    to="/experiment/$name"
                    params={{ name: exp.name }}
                    className="w-48 text-sm font-semibold truncate text-foreground hover:text-primary shrink-0"
                  >
                    {exp.name}
                  </Link>

                  <div className="flex-1 h-5 bg-muted rounded overflow-hidden">
                    <div className="h-full flex" style={{ width: `${barWidth}%` }}>
                      {exp.successful_run_count > 0 && (
                        <div
                          className="h-full bg-green-500"
                          style={{ width: `${(exp.successful_run_count / total) * 100}%` }}
                        />
                      )}
                      {exp.failed_run_count > 0 && (
                        <div
                          className="h-full bg-red-500"
                          style={{ width: `${(exp.failed_run_count / total) * 100}%` }}
                        />
                      )}
                    </div>
                  </div>

                  <div className="w-24 text-right text-xs tabular-nums shrink-0">
                    <span className="text-green-600">{exp.successful_run_count}</span>
                    <span className="text-muted-foreground">/</span>
                    <span className="text-red-600">{exp.failed_run_count}</span>
                    <span className={`ml-1 font-semibold ${rate >= 80 ? 'text-green-600' : rate >= 50 ? 'text-yellow-600' : 'text-red-600'}`}>
                      {rate}%
                    </span>
                  </div>
                </div>
              )
            })}
          </div>
        </CardContent>
      </Card>
    </div>
  )
}

import { useState } from 'react'
import { Loader2 } from 'lucide-react'
import { useRun } from '@/api/hooks/use-runs'
import { useUserProfile } from '@/api/hooks/use-user'
import { Card, CardContent } from '@/components/ui/card'
import { ProfileImage } from '@/components/profile/profile-image'
import { StatusIcon } from '@/components/shared/status-icon'
import { EventTimeline } from './event-timeline'
import { isActionEvent, isTestEvent } from '@/types/experiment'

interface RunDetailViewProps {
  ulid: string
}

function secondsToString(seconds: number): string {
  seconds = Math.round(seconds)
  const minutes = Math.floor((seconds % 3600) / 60)
  const remainingSeconds = seconds % 60
  return `${minutes}min ${remainingSeconds}s`
}

export function RunDetailView({ ulid }: RunDetailViewProps) {
  const { data: run, isLoading } = useRun(ulid)
  const { data: profile } = useUserProfile(run?.published_by ?? '')
  const [onlyShowTests, setOnlyShowTests] = useState(false)

  if (isLoading) {
    return (
      <div className="flex justify-center py-12">
        <Loader2 className="w-8 h-8 animate-spin" />
      </div>
    )
  }

  if (!run) {
    return (
      <Card>
        <CardContent className="py-6">
          <p className="text-lg">Run not found</p>
        </CardContent>
      </Card>
    )
  }

  const events = Array.isArray(run.events)
    ? onlyShowTests
      ? run.events.filter((e) => isTestEvent(e))
      : run.events.filter((e) => !(isActionEvent(e) && e.action_type === 'idle'))
    : []

  return (
    <Card>
      <CardContent className="space-y-6 pt-6">
        {/* Run number + Published by */}
        <div className="flex justify-between">
          <div>
            <div className="text-sm text-muted-foreground">run</div>
            <div className="text-2xl">#{run.run_number}</div>
            <div className="text-xs text-muted-foreground">{run.ulid}</div>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground">published by</div>
            {profile && <ProfileImage profile={profile} size="md" showTooltip linkToProfile />}
          </div>
        </div>

        {/* Experiment + Environment */}
        <div className="flex justify-between">
          <div>
            <div className="text-sm text-muted-foreground">experiment</div>
            <div className="text-2xl">{run.experiment}</div>
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground">environment</div>
            <div className="text-2xl">{run.environment}</div>
          </div>
        </div>

        {/* Status + Duration */}
        <div className="flex justify-between">
          <div>
            <div className="text-sm text-muted-foreground">result status</div>
            <StatusIcon status={run.result_status.name} size="w-8 h-8" />
          </div>
          <div className="text-right">
            <div className="text-sm text-muted-foreground">duration</div>
            <div className="text-2xl">{secondsToString(run.duration)}</div>
          </div>
        </div>

        {/* Events */}
        <Card>
          <CardContent className="pt-6">
            <div className="flex items-center gap-4 mb-4">
              <h3 className="text-xl font-semibold">Events</h3>
              <label className="flex items-center gap-2 text-sm cursor-pointer">
                <input
                  type="checkbox"
                  checked={onlyShowTests}
                  onChange={(e) => setOnlyShowTests(e.target.checked)}
                  className="rounded"
                />
                Only show tests
              </label>
            </div>
            <EventTimeline events={events} />
          </CardContent>
        </Card>
      </CardContent>
    </Card>
  )
}

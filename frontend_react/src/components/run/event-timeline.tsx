import {
  Search,
  MousePointer,
  Keyboard,
  Code,
  AlertCircle,
  HelpCircle,
  Pause,
  Play,
} from 'lucide-react'
import type { Event, ActionEvent, BaseEvent } from '@/types/experiment'
import {
  isActionEvent,
  isTestEvent,
  isErrorEvent,
} from '@/types/experiment'
import { cn } from '@/lib/utils'

interface EventTimelineProps {
  events: Event[]
}

export function EventTimeline({ events }: EventTimelineProps) {
  return (
    <div className="relative pl-8">
      {/* Timeline line */}
      <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-border" />

      {events.map((event) => {
        const dotColor = getDotColor(event)
        const Icon = getIcon(event)
        return (
          <div key={event.ulid} className="relative pb-4">
            {/* Dot */}
            <div
              className={cn(
                'absolute -left-5 w-6 h-6 rounded-full flex items-center justify-center',
                dotColor,
              )}
            >
              <Icon className="w-3.5 h-3.5 text-white" />
            </div>
            {/* Content */}
            <div className="ml-4">
              <EventContent event={event} />
            </div>
          </div>
        )
      })}
    </div>
  )
}

function parseActionData(actionData: string): Record<string, unknown> {
  if (!actionData) return {}
  try {
    return JSON.parse(actionData)
  } catch {
    return {}
  }
}

function ActionEventContent({ event }: { event: ActionEvent }) {
  const data = parseActionData(event.action_data)
  const actionType = event.action_type || 'action'

  switch (actionType) {
    case 'command':
      return (
        <span>
          command: <i>{(data.command as string) || event.action_id || 'unknown'}</i>
        </span>
      )
    case 'click':
      return (
        <span>
          click at: <i>{(data.target as string) || event.action_id || 'unknown'}</i>
        </span>
      )
    case 'keyboard':
      return (
        <span>
          press: <i>{(data.keys as string) || event.action_id || 'unknown'}</i>
        </span>
      )
    case 'find':
      return (
        <span>
          find: <i>{(data.objective as string) || event.action_id || 'unknown'}</i>
        </span>
      )
    case 'idle':
      return (
        <span>
          idle: <i>{(data.seconds as string) || '?'}s</i>
        </span>
      )
    default:
      return (
        <span>
          {actionType}: <i>{event.action_id || JSON.stringify(data).slice(0, 80)}</i>
        </span>
      )
  }
}

function EventContent({ event }: { event: Event }) {
  if (isTestEvent(event)) {
    return (
      <span>
        test: <i>{event.abstracttest.name}</i> ({event.abstracttest.testfunction.name})
      </span>
    )
  }
  if (isErrorEvent(event)) {
    return (
      <span className="text-red-600">
        error: {event.error_name} - {event.error_msg}
      </span>
    )
  }
  if (isActionEvent(event)) {
    return <ActionEventContent event={event} />
  }
  return <span>{(event as BaseEvent).category}</span>
}

function getDotColor(event: Event): string {
  if (isTestEvent(event)) {
    if (event.result?.status?.name === 'success') return 'bg-green-500'
    if (event.result?.status?.name === 'failed') return 'bg-red-500'
  }
  if (isErrorEvent(event)) return 'bg-red-500'
  if (event.success === true) return 'bg-green-500'
  if (event.success === false) return 'bg-red-500'
  return 'bg-muted-foreground'
}

function getIcon(event: Event) {
  if (isTestEvent(event)) return HelpCircle
  if (isErrorEvent(event)) return AlertCircle
  if (isActionEvent(event)) {
    const actionType = event.action_type
    if (actionType === 'command') return Code
    if (actionType === 'click') return MousePointer
    if (actionType === 'keyboard') return Keyboard
    if (actionType === 'find') return Search
    if (actionType === 'idle') return Pause
    return Play
  }
  return HelpCircle
}

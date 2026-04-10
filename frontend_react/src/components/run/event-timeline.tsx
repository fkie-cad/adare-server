import {
  Search,
  MousePointer,
  Keyboard,
  Code,
  AlertCircle,
  HelpCircle,
  Pause,
} from 'lucide-react'
import type { Event } from '@/types/experiment'
import {
  isGuiFindEvent,
  isGuiClickEvent,
  isGuiKeypressEvent,
  isCommandEvent,
  isTestEvent,
  isErrorEvent,
  isGuiIdleEvent,
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

function EventContent({ event }: { event: Event }) {
  if (isGuiFindEvent(event)) {
    return (
      <span>
        find: <i>{event.objective}</i> -&gt; {event.positions}
      </span>
    )
  }
  if (isGuiClickEvent(event)) {
    return (
      <span>
        click at: <i>{event.target}</i>
      </span>
    )
  }
  if (isGuiKeypressEvent(event)) {
    return (
      <span>
        press: <i>{event.keys}</i>
      </span>
    )
  }
  if (isCommandEvent(event)) {
    return (
      <span>
        command: <i>{event.command}</i>
      </span>
    )
  }
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
  return <span>{event.category}</span>
}

function getDotColor(event: Event): string {
  if (isTestEvent(event)) {
    if (event.result.status.name === 'success') return 'bg-green-500'
    if (event.result.status.name === 'failed') return 'bg-red-500'
  }
  if (isErrorEvent(event)) return 'bg-red-500'
  return 'bg-muted-foreground'
}

function getIcon(event: Event) {
  if (isGuiFindEvent(event)) return Search
  if (isGuiClickEvent(event)) return MousePointer
  if (isGuiIdleEvent(event)) return Pause
  if (isGuiKeypressEvent(event)) return Keyboard
  if (isCommandEvent(event)) return Code
  if (isErrorEvent(event)) return AlertCircle
  if (isTestEvent(event)) return HelpCircle
  return HelpCircle
}

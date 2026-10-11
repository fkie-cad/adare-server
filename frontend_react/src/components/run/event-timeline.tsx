import {
  Search,
  MousePointer,
  Keyboard,
  Code,
  AlertCircle,
  HelpCircle,
  Pause,
  Play,
  ChevronRight,
} from 'lucide-react'
import { useState, createElement, type ReactNode } from 'react'
import type { Event, ActionEvent, BaseEvent } from '@/types/experiment'
import {
  isActionEvent,
  isTestEvent,
  isErrorEvent,
} from '@/types/experiment'
import { Tooltip } from '@/components/ui/tooltip'
import { cn } from '@/lib/utils'

interface EventTimelineProps {
  events: Event[]
}

export function EventTimeline({ events }: EventTimelineProps) {
  return (
    <div className="relative pl-8">
      {/* Timeline line */}
      <div className="absolute left-3 top-0 bottom-0 w-0.5 bg-border" />

      {events.map((event) => (
        <EventRow key={event.ulid} event={event} />
      ))}
    </div>
  )
}

function EventRow({ event }: { event: Event }) {
  const [open, setOpen] = useState(false)
  const dotColor = getDotColor(event)
  const icon = getIcon(event)
  const failed = isFailedEvent(event)
  const hover = getHoverSummary(event)

  return (
    <div className="relative pb-4">
      {/* Dot */}
      <div
        className={cn(
          'absolute -left-5 w-6 h-6 rounded-full flex items-center justify-center',
          dotColor,
        )}
      >
        {createElement(icon, { className: 'w-3.5 h-3.5 text-white' })}
      </div>
      {/* Content — left bar appears only on failure */}
      <div
        className={cn(
          'ml-4 rounded-md border-l-2 pl-3 py-1',
          failed ? 'border-l-destructive bg-destructive/5' : 'border-l-transparent',
        )}
      >
        <Tooltip content={hover} side="right">
          <button
            type="button"
            aria-expanded={open}
            onClick={() => setOpen((v) => !v)}
            className="flex w-full items-baseline gap-2 text-left"
          >
            <ChevronRight
              className={cn(
                'mt-0.5 h-3.5 w-3.5 shrink-0 self-center text-muted-foreground transition-transform',
                open && 'rotate-90',
              )}
            />
            <span className="text-xs font-semibold uppercase tracking-wide text-muted-foreground">
              {getEventTypeLabel(event)}
            </span>
            <span className="min-w-0 flex-1">
              <EventContent event={event} />
            </span>
          </button>
        </Tooltip>
        {open && <EventDetail event={event} />}
      </div>
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
  // action_description is self-describing and sometimes repeats the type
  // (e.g. command events store "command: execute '<cmd>'"). Strip a leading
  // "<type>:" prefix so it isn't echoed after the type label we render.
  const rawDescription = (data.action_description as string) || ''
  const description = rawDescription.replace(
    new RegExp(`^${actionType}\\s*:\\s*`, 'i'),
    '',
  )

  // Primary line: the human-readable description of what the action does.
  // Falls back to type-specific detail, then to action_id.
  const primary =
    description ||
    ({
      command: data.command_executed as string,
      click: data.target_info ? JSON.stringify(data.target_info) : undefined,
      keyboard: data.combination ? (data.combination as string[]).join('+') : undefined,
      find: data.objective as string,
      idle: data.actual_duration != null ? `wait ${data.actual_duration}s` : undefined,
    } as Record<string, string | undefined>)[actionType] ||
    event.action_id ||
    'unknown'

  return (
    <span>
      <i>{primary}</i>
    </span>
  )
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
    if (event.result?.status?.name === 'success') return 'bg-success'
    if (event.result?.status?.name === 'failed') return 'bg-destructive'
  }
  if (isErrorEvent(event)) return 'bg-destructive'
  if (event.success === true) return 'bg-success'
  if (event.success === false) return 'bg-destructive'
  return 'bg-muted-foreground'
}

function isFailedEvent(event: Event): boolean {
  if (isTestEvent(event)) return event.result?.status?.name === 'failed'
  if (isErrorEvent(event)) return true
  return event.success === false
}

function getEventTypeLabel(event: Event): string {
  if (isActionEvent(event)) return event.action_type || 'action'
  if (isTestEvent(event)) return 'test'
  if (isErrorEvent(event)) return 'error'
  return (event as BaseEvent).category
}

function formatTimestamp(ts: string): string {
  if (!ts) return '-'
  const d = new Date(ts)
  if (Number.isNaN(d.getTime())) return ts
  return d.toLocaleString()
}

function formatDuration(ms: number | null | undefined): string {
  if (ms == null) return '-'
  if (ms < 1000) return `${ms} ms`
  return `${(ms / 1000).toFixed(2)} s`
}

/**
 * Concise one-line-per-field summary shown in the hover tooltip.
 * Each row is a `key: value` pair separated by newlines (rendered via
 * the Tooltip's whitespace-pre-line).
 */
function getHoverSummary(event: Event): string {
  const lines: string[] = []
  if (isTestEvent(event)) {
    lines.push(`test: ${event.abstracttest.name}`)
    lines.push(`function: ${event.abstracttest.testfunction.name}`)
    lines.push(`result: ${event.result?.status?.name ?? '-'}`)
    if (event.abstracttest.parameters.length > 0) {
      lines.push(
        `params: ${event.abstracttest.parameters.map((p) => `${p.parameter.name}=${p.value}`).join(', ')}`,
      )
    }
  } else if (isErrorEvent(event)) {
    lines.push(`error: ${event.error_name}`)
    lines.push(`message: ${event.error_msg}`)
  } else if (isActionEvent(event)) {
    const data = parseActionData(event.action_data)
    const type = event.action_type || 'action'
    lines.push(`type: ${type}`)
    if (event.action_id) lines.push(`action_id: ${event.action_id}`)
    const description = ((data.action_description as string) || '').replace(
      new RegExp(`^${type}\\s*:\\s*`, 'i'),
      '',
    )
    if (description) lines.push(`description: ${description}`)
    // Per-type specifics (real prod action_data schema).
    switch (type) {
      case 'command':
        if (data.command_executed) lines.push(`command: ${data.command_executed}`)
        if (data.return_code != null) lines.push(`return_code: ${data.return_code}`)
        if (data.output) {
          const out = String(data.output).trim().split('\n').slice(-2).join(' | ')
          lines.push(`output: ${out}`)
        }
        break
      case 'click':
        if (data.target_info) lines.push(`target: ${JSON.stringify(data.target_info)}`)
        break
      case 'keyboard':
        if (data.combination) {
          const combo = Array.isArray(data.combination) ? data.combination.join('+') : String(data.combination)
          lines.push(`keys: ${combo}`)
        }
        break
      case 'find':
        if (data.objective) lines.push(`objective: ${data.objective}`)
        break
      case 'idle':
        if (data.actual_duration != null) lines.push(`wait: ${data.actual_duration}s`)
        break
    }
  }
  lines.push(`time: ${formatTimestamp(event.timestamp)}`)
  if (event.execution_time != null) lines.push(`duration: ${formatDuration(event.execution_time)}`)
  return lines.join('\n')
}

/**
 * Full structured detail panel shown when a row is clicked open.
 */
function EventDetail({ event }: { event: Event }) {
  return (
    <div className="mt-2 space-y-2 rounded-md border bg-muted/30 p-3 text-xs">
      <DetailGroup title="General">
        <DetailRow label="category" value={event.category} />
        <DetailRow label="status" value={event.status?.name ?? '-'} />
        <DetailRow label="success" value={String(event.success)} />
        <DetailRow label="timestamp" value={formatTimestamp(event.timestamp)} />
        <DetailRow label="execution time" value={formatDuration(event.execution_time)} />
        <DetailRow label="event group" value={event.event_group_id || '-'} />
        <DetailRow label="event type" value={event.event_type_specific || '-'} />
        <DetailRow label="ulid" value={event.ulid} mono />
      </DetailGroup>

      {isTestEvent(event) && (
        <DetailGroup title="Test">
          <DetailRow label="abstract test" value={event.abstracttest.name} />
          {event.abstracttest.description && (
            <DetailRow label="description" value={event.abstracttest.description} />
          )}
          <DetailRow label="testfunction" value={event.abstracttest.testfunction.name} />
          <DetailRow label="set" value={event.abstracttest.testfunction.set} />
          <DetailRow label="result" value={event.result?.status?.name ?? '-'} />
          {event.result?.details && (
            <DetailRow label="result details" value={event.result.details} pre />
          )}
          {event.abstracttest.parameters.length > 0 && (
            <DetailRow
              label="parameters"
              value={event.abstracttest.parameters
                .map((p) => `${p.parameter.name}=${p.value}`)
                .join('\n')}
              pre
            />
          )}
        </DetailGroup>
      )}

      {isErrorEvent(event) && (
        <DetailGroup title="Error">
          <DetailRow label="error name" value={event.error_name} />
          <DetailRow label="error message" value={event.error_msg} pre />
        </DetailGroup>
      )}

      {isActionEvent(event) && (
        <DetailGroup title="Action">
          <DetailRow label="action type" value={event.action_type} />
          <DetailRow label="action id" value={event.action_id || '-'} mono />
          <ActionDataDetail event={event} />
        </DetailGroup>
      )}
    </div>
  )
}

function ActionDataDetail({ event }: { event: ActionEvent }) {
  const data = parseActionData(event.action_data)
  const entries = Object.entries(data)
  if (entries.length === 0) return null
  return (
    <div className="space-y-1">
      <div className="font-semibold text-muted-foreground">action data</div>
      <div className="space-y-1">
        {entries.map(([key, value]) => (
          <DetailRow
            key={key}
            label={key}
            value={typeof value === 'object' ? JSON.stringify(value, null, 2) : String(value)}
            pre={key === 'stdout' || typeof value === 'object'}
          />
        ))}
      </div>
    </div>
  )
}

function DetailGroup({ title, children }: { title: string; children: ReactNode }) {
  return (
    <div className="space-y-1">
      <div className="font-semibold text-muted-foreground">{title}</div>
      <div className="space-y-1">{children}</div>
    </div>
  )
}

function DetailRow({
  label,
  value,
  mono = false,
  pre = false,
}: {
  label: string
  value: string
  mono?: boolean
  pre?: boolean
}) {
  return (
    <div className="grid grid-cols-[max-content_1fr] gap-x-2">
      <span className="text-muted-foreground">{label}:</span>
      {pre ? (
        <pre
          className={cn(
            'm-0 max-h-48 overflow-auto whitespace-pre-wrap break-words rounded bg-background/60 p-1.5',
            mono && 'font-mono',
          )}
        >
          {value}
        </pre>
      ) : (
        <span className={cn('min-w-0 break-words', mono && 'font-mono text-[11px]')}>{value}</span>
      )}
    </div>
  )
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

import {
  Info,
  Check,
  X,
  Clock,
  CheckCircle,
  XCircle,
  HelpCircle,
} from 'lucide-react'
import type { LucideIcon } from 'lucide-react'

export const statusList = [
  'not assigned',
  'accepted',
  'rejected',
  'assigned',
  'success',
  'failed',
] as const
export type StatusType = (typeof statusList)[number]

export function isValidStatusType(value: string): value is StatusType {
  return (statusList as readonly string[]).includes(value)
}

export const statusColorMapping: Record<StatusType, string> = {
  'not assigned': 'text-muted-foreground',
  accepted: 'text-success',
  rejected: 'text-destructive',
  assigned: 'text-warning',
  success: 'text-success',
  failed: 'text-destructive',
}

export const statusBgColorMapping: Record<StatusType, string> = {
  'not assigned': 'bg-muted text-muted-foreground',
  accepted: 'bg-success/15 text-success',
  rejected: 'bg-destructive/15 text-destructive',
  assigned: 'bg-warning/15 text-warning',
  success: 'bg-success/15 text-success',
  failed: 'bg-destructive/15 text-destructive',
}

export const statusIconMapping: Record<StatusType, LucideIcon> = {
  'not assigned': Info,
  accepted: Check,
  rejected: X,
  assigned: Clock,
  success: CheckCircle,
  failed: XCircle,
}

export const defaultStatusIcon = HelpCircle

export const osList = ['windows', 'linux'] as const
export type OSListType = (typeof osList)[number]

export function isValidOSListType(value: string): value is OSListType {
  return (osList as readonly string[]).includes(value)
}

export const osColorMapping: Record<OSListType, string> = {
  windows: 'text-blue-600',
  linux: 'text-foreground',
}

export const dtypeList = ['int', 'float', 'str', 'bool', 'list'] as const

export const dtypeColorMapping: Record<(typeof dtypeList)[number], string> = {
  int: 'bg-indigo-500/15 text-indigo-600 dark:text-indigo-300',
  float: 'bg-blue-500/15 text-blue-600 dark:text-blue-300',
  str: 'bg-orange-500/15 text-orange-600 dark:text-orange-300',
  bool: 'bg-lime-500/15 text-lime-600 dark:text-lime-300',
  list: 'bg-cyan-500/15 text-cyan-600 dark:text-cyan-300',
}

export function isValidDtype(value: string): value is (typeof dtypeList)[number] {
  return (dtypeList as readonly string[]).includes(value)
}

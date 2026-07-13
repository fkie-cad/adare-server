// User
export interface User {
  username: string
  email: string
}

export interface Profile {
  user: User
  avatar: string
  teams: Team[]
  achievements: Achievement[]
}

export interface Achievement {
  name: string
  iconfile: string
  description: string
  count: number
}

export interface Team {
  id: number
  name: string
}

// Experiment
export interface Status {
  name: string
}

export interface Tag {
  name: string
}

export interface Label {
  name: string
}

export interface OsInfo {
  os: string
  distribution: string
  version: string
  language?: string
  architecture?: string
  details?: string
}

export interface RunCount {
  successful: number
  failed: number
}

export const categories = [
  'error',
  'command',
  'action',
  'test',
] as const

export interface BaseEvent {
  ulid: string
  category: string
  status: Status
  error: string
  timestamp: string
  success: boolean | null
  event_group_id: string
  event_type_specific: string
  execution_time: number | null
  duration?: number
}

export interface Result {
  status: Status
  details?: string
}

export interface TestEvent extends BaseEvent {
  category: 'test'
  result: Result
  abstracttest: AbstractTest
}

export interface ErrorEvent extends BaseEvent {
  category: 'error'
  error_name: string
  error_msg: string
}

export interface ActionEvent extends BaseEvent {
  category: 'action' | 'command'
  action_type: string
  action_id: string
  action_data: string
}

export type Event = TestEvent | ErrorEvent | ActionEvent

export function isTestEvent(event: Event): event is TestEvent {
  return event.category === 'test'
}

export function isErrorEvent(event: Event): event is ErrorEvent {
  return event.category === 'error'
}

export function isActionEvent(event: Event): event is ActionEvent {
  return event.category === 'action' || event.category === 'command'
}

export function isCommandEvent(event: Event): event is ActionEvent {
  return isActionEvent(event) && event.action_type === 'command'
}

export interface AbstractParameter {
  name: string
  dtype: string
  description: string
}

export interface Parameter {
  parameter: AbstractParameter
  value: string
}

export interface Testfunction {
  name: string
  description: string
  possible_parameters: AbstractParameter[]
  set: string
}

export interface AbstractTest {
  ulid: string
  name: string
  description: string
  testfunction: Testfunction
  parameters: Parameter[]
}

export interface Run {
  ulid: string
  run_number: number
  experiment: string
  environment: string
  published_by: string
  published_at: string
  timestamp_start: string
  timestamp_end: string
  status: Status
  result_status: Status
  events: Event[]
  duration: number
  adarevm_logfile?: string | null
  installations_logfile?: string | null
  packagedump_logfile?: string | null
  networkdrives_logfile?: string | null
}

export interface Recipe {
  profile: string
  iso: string
  iso_sha256: string
  template?: string
  setup_level?: number | null
  disk_size?: string
  ram_mb?: number | null
  cpus?: number | null
  arch?: string
}

export interface Environment {
  ulid: string
  name: string
  description: string
  vm: string
  vagrantbox: string
  recipe?: Recipe | null
  vm_sha256?: string
  published_by: string
  created_by: string
  published_at: string
  tags: Tag[]
  os_info: OsInfo
  postsetup_installations: string
  file: string
}

export interface Experiment {
  ulid: string
  name: string
  description: string
  published_by: string
  published_at: string
  created_by: string
  tags: Tag[]
  run_counts: RunCount
  playbook_file: string
  metadata_file: string
  abstract_tests: AbstractTest[]
}

export interface Request {
  title: string
  ulid: string
  description: string
  object: Record<string, unknown>
  objective_name: string
  action: string
  gitea_pr_status: string
  gitea_pr_url: string
  gitea_pr_number: number
  labels: string[]
  requester: { username: string; email: string; avatar: string }
  assignees: { username: string; email: string; avatar: string }[]
  reviewers: { username: string; email: string; avatar: string }[]
  last_change_date: string
  creation_date: string
}

export interface TestfunctionSet {
  name: string
  description: string
  published_by: string
  published_at: string
  created_by: string
  file: string
  requirements_file: string
  num_testfunctions: number
  testfunctions: Testfunction[]
}

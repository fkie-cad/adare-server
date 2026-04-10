// user

export interface User {
  username: string;
  email: string;
}

export interface Profile {
  user: User;
  avatar: string;
  teams: Team[];
  achievements: Achievement[];
}

interface Achievement {
  name: string;
  iconfile: string;
  description: string;
  count: number;
}

export interface Team {
  id: number;
  name: string;
}

// experiment
export interface Status {
  name: string;
}

export interface Tag {
  name: string;
  scope: string | null;
  value: string;
  color: string | null;
}

export interface Label {
  name: string;
}

export interface OsInfo {
  os: string;
  distribution: string;
  version: string;
  language?: string;
  architecture?: string;
  details?: string;
}

export interface RunCount {
  successful: number;
  failed: number;
}

export const categories = ['error','command', 'test', 'gui:find', 'gui:idle', 'gui:keypress', 'gui:click'] as const;

export interface BaseEvent {
  status: Status;
  ulid: string;
  category: typeof categories[number];
  error: string;
  group_id: number;
  timestamp: string;
}

export interface ErrorEvent extends BaseEvent {
  category: 'error';
  error_name: string;
  error_msg: string;
}

export interface CommandEvent extends BaseEvent {
  category: 'command';
  name: string;
  command: string;
  return_code: number;
  stdout: string;
}

export interface Result {
  status: Status;
}

export interface TestEvent extends BaseEvent {
  category: 'test';
  result: Result;
  abstracttest: AbstractTest;
}

export interface GuiFindEvent extends BaseEvent {
  category: 'gui:find';
  text: boolean;
  objective: string;
  success: boolean;
  positions: string;
}

export interface GuiClickEvent extends BaseEvent {
  category: 'gui:click';
  clicktype: string;
  modifiers: string;
  target: string
}

export interface GuiIdleEvent extends BaseEvent {
  category: 'gui:idle';
  seconds: number;
}

export interface GuiKeypressEvent extends BaseEvent {
  category: 'gui:keypress';
  keys: string;
}

export type Event = CommandEvent | TestEvent | GuiFindEvent | GuiIdleEvent | GuiKeypressEvent | GuiClickEvent | ErrorEvent;

export function isGuiIdleEvent(event: Event): event is GuiIdleEvent {
  return event.category === 'gui:idle';
}

export function isGuiKeypressEvent(event: Event): event is GuiKeypressEvent {
  return event.category === 'gui:keypress';
}

export function isGuiClickEvent(event: Event): event is GuiClickEvent {
  return event.category === 'gui:click';
}

export function isGuiFindEvent(event: Event): event is GuiFindEvent {
  return event.category === 'gui:find';
}

export function isTestEvent(event: Event): event is TestEvent {
  return event.category === 'test';
}

export function isCommandEvent(event: Event): event is CommandEvent {
  return event.category === 'command';
}

export function isErrorEvent(event: Event): event is ErrorEvent {
  return event.category === 'error';
}

export interface AbstractParameter {
  name: string;
  dtype: string;
  description: string;
}

export interface Parameter {
  parameter: AbstractParameter;
  value: string;
}

export interface Testfunction {
  name: string;
  description: string;
  possible_parameters: AbstractParameter[];
  set: string;
}

export interface AbstractTest {
  ulid: string;
  name: string;
  description: string;
  testfunction: Testfunction;
  parameters: Parameter[];
}

export interface Run {
  ulid: string;
  experiment: string;
  environment: string;
  published_by: string;
  published_at: string;
  timestamp_start: string;
  timestamp_end: string;
  status: Status;
  result_status: Status;
  events: Event[];
  duration: number;
  adarevm_logfile: string;
  installations_logfile: string;
  packagedump_logfile: string;
  networkdrives_logfile: string;
}

export interface Environment {
  ulid: string;
  name: string;
  description: string;
  vagrantbox: string;
  published_by: string;
  created_by: string;
  published_at: string;
  tags: Tag[];
  os_info: OsInfo;
  postsetup_installations: string;
  file: string;
}

export interface Experiment {
  ulid: string;
  name: string;
  description: string;
  published_by: string;
  published_at: string;
  created_by: string;
  tags: Tag[];
  run_counts: RunCount;
  action_file: string;
  testset_file: string;
  metadata_file: string;
  abstract_tests: AbstractTest[];
}

export interface Request {
  object_name: string;
  objective_name: string;
  action: string;
  status: Status;
  labels: Label[];
  requester: string;
  assignees: string[];
  reviewers: string[];
  last_change_date: string;
  creation_date: string;
}

export interface TestfunctionSet {
  name: string;
  description: string;
  published_by: string;
  published_at: string;
  created_by: string;
  tags: Tag[];
  file: string;
  requirements_file: string;
  num_testfunctions: number;
  testfunctions: Testfunction[];
}

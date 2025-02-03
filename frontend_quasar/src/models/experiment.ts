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
  successfull: number;
  failed: number;
}

export const categories = ['command', 'test', 'gui:find'] as const;

export interface BaseEvent {
  status: Status;
  ulid: string;
  category: typeof categories[number];
  error: string;
  group_id: number;
  timestamp: string;
}

export interface CommandEvent extends BaseEvent {
  category: 'command';
  name: string;
  command: string;
  return_code: number;
  stdout: string;
}

export interface TestEvent extends BaseEvent {
  category: 'test';
  abstract_test: AbstractTest;
}

export interface GuiFindEvent extends BaseEvent {
  category: 'gui:find';
  text: boolean;
  objective: string;
  success: boolean;
}

export type Event = CommandEvent | TestEvent | GuiFindEvent;

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
  file: string;
  requirements_file: string;
  num_testfunctions: number;
  testfunctions: Testfunction[];
}

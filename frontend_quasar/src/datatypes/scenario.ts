interface Scenario {
  uuid: string;
  name: string;
  description: string;
  publisher_name: string;
  publish_date: string;
  tags: string[];
  experiment: string[];
}

interface Parameter {
  name: string;
  dtype: string;
}

interface ParameterEntry {
  parameter: Parameter;
  value: string;
}

interface TestFunction {
  name: string
  test_name: string;
  test_description: string;
  possible_parameters: Parameter[];
}

interface Tool {
  name: string;
  command: string;
}

interface AbstractTest {
  uuid: string;
  name: string;
  description: string;
  testfunction: TestFunction;
  parameters: ParameterEntry[];
  tool?: Tool;
}

interface OsInfo {
  os: string;
  version: string;
  distribution: string;
  language?: string;
  architecture?: string;
  details?: string;
}

interface ExperimentRun {
  uuid: string;
  name: string;
}

interface RunCount {
  successful: number;
  failed: number;
}


interface RequestStatus {
  name: string;
}

interface Label {
  name: string;
}

interface ExternalUser {
  username: string;
  email: string;
  avatar: string;
}


interface Experiment {
    uuid: string;
    name: string;
    description: string;
    os_info: OsInfo;

    action_file: string;
    action_file_name: string;
    testset_file: string;
    testset_file_name: string;

    abstract_tests: AbstractTest[];
    experiment_runs: ExperimentRun[];

    published_by: ExternalUser;
    publish_date: string;

    tags: string[];

    // calculated fields
    run_counts: RunCount;

}


interface RequestCategory {
  type: 'scenario' | 'experiment';
  category: Scenario | Experiment;
}


interface Request {
  title: string;
  uuid: string;
  description: string;

  last_changed: string;

  category: RequestCategory;

  requestor: string;
  request_date: string;

  supervisor: string;
  supervisor_assigned_by: string;

  status: RequestStatus;
  labels: Label[];

}

interface ScenarioDict {
  [uuid: string]: Scenario;
}


interface ExperimentDict {
  [uuid: string]: Experiment;
}


interface RequestDict {
  [uuid: string]: Request;
}


export type { ScenarioDict, ExperimentDict, RequestDict, Request, Scenario, Experiment, TestFunction, Parameter, ParameterEntry, Tool, AbstractTest, OsInfo };

interface Scenario {
  uuid: string;
  name: string;
  description: string;
  publisher_name: string;
  publish_date: string;
  tags: string[];
  experiment: string[];
}

interface Experiment {
    uuid: string;
    name: string;
    description: string;

    abstract_tests: string[];

    publisher_name: string;
    publish_date: string;

    tags: string[];
}

interface ScenarioDict {
  [uuid: string]: Scenario;
}



interface ExperimentDict {
  [uuid: string]: Experiment;
}


export type { Scenario, ScenarioDict, ExperimentDict, Experiment };

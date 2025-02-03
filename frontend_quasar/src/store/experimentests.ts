import { defineStore } from 'pinia';
import { useExperimentStore } from 'src/store/experiment';

interface ExperimentTestState {
  experimentStore: ReturnType<typeof useExperimentStore>;
  experiment: string,
  filterSupported: boolean;
}

export const useExperimentTestsStore = defineStore('experimenttests', {
  state: (): ExperimentTestState => ({
    experimentStore: useExperimentStore(),
    experiment: '',
    filterSupported: false,
  }),

  actions: {
    async setExperiment(experiment: string) {
      this.experiment = experiment;
      await this.experimentStore.loadExperimentByName(experiment);
    },

    isFilterSupported() {
      return this.filterSupported;
    },

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    async fetchRows(query: string) {
      // do nothing since data is already fetched
    },

    // eslint-disable-next-line @typescript-eslint/no-unused-vars
    async fetchRowsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string) {
      // do nothing since data is already fetched
    },

    getRows() {
      return this.experimentStore.getExperimentByName(this.experiment)?.abstract_tests;
    },
  },
});

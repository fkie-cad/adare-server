import { defineStore } from 'pinia';
import { Experiment } from 'src/models/experiment';
import { fetchItems, fetchAdvancedItems, fetchFilterOptions } from 'src/utils/storeUtils';

interface ExperimentState {
  experiments: Record<string, Experiment>;
  filterSupported: boolean;
}

export const useExperimentStore = defineStore('experiment', {
  state: (): ExperimentState => ({
    experiments: {},
    filterSupported: false,
  }),

  actions: {
    async fetchExperiments(query: string) {
      this.experiments = await fetchItems('experiment', query);
    },

    async fetchExperimentsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string) {
      await fetchAdvancedItems('experiment', this.fetchExperiments, limit, offset, sortBy, descending, filterString);
    },

    isFilterSupported() {
      return this.filterSupported;
    },

    async fetchFilterOptions(query: string) {
      return await fetchFilterOptions('experiment', query);
    },

    async fetchRows(query: string) {
      await this.fetchExperiments(query);
    },

    async fetchRowsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string) {
      await this.fetchExperimentsAdvanced(limit, offset, sortBy, descending, filterString);
    },

    getRows() {
      return Object.values(this.experiments);
    },
  },
});

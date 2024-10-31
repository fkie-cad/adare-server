import { defineStore } from 'pinia';
import { Environment } from 'src/models/experiment';
import { fetchItems, fetchAdvancedItems, fetchFilterOptions } from 'src/utils/storeUtils';

interface EnvironmentState {
  environments: Record<string, Environment>;
  filterSupported: boolean;
}

export const useEnvironmentStore = defineStore('environment', {
  state: (): EnvironmentState => ({
    environments: {},
    filterSupported: false,
  }),

  actions: {
    async fetchEnvironments(query: string) {
      this.environments = await fetchItems('environment', query);
    },

    async fetchEnvironmentsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string) {
      await fetchAdvancedItems('environment', this.fetchEnvironments, limit, offset, sortBy, descending, filterString);
    },

    isFilterSupported() {
      return this.filterSupported;
    },

    async fetchFilterOptions(query: string) {
      return await fetchFilterOptions('environment', query);
    },

    async fetchRows(query: string) {
      await this.fetchEnvironments(query);
    },

    async fetchRowsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string) {
      await this.fetchEnvironmentsAdvanced(limit, offset, sortBy, descending, filterString);
    },

    getRows() {
      return Object.values(this.environments);
    },
  },
});

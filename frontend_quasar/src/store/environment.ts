import { defineStore } from 'pinia';
import { Environment } from 'src/models/experiment';
import { fetchItems, fetchAdvancedItems, fetchFilterOptions, ScopedFilterParams } from 'src/utils/storeUtils';
import { api } from 'src/boot/axios';

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

    async fetchEnvironmentsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string, scopedFilters?: ScopedFilterParams) {
      await fetchAdvancedItems('environment', this.fetchEnvironments, limit, offset, sortBy, descending, filterString, scopedFilters);
    },

    async loadEnvironmentByName(name: string) {
      const data = await api.get(`environment/environment_${name}/`).then(res => res.data);
      this.environments[data.ulid] = data;
      return data;
    },

    getEnvironmentByName(name: string) {
      return Object.values(this.environments).find((env) => env.name === name) || null;
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

    async fetchRowsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string, scopedFilters?: ScopedFilterParams) {
      await this.fetchEnvironmentsAdvanced(limit, offset, sortBy, descending, filterString, scopedFilters);
    },

    getRows() {
      return Object.values(this.environments);
    },
  },
});

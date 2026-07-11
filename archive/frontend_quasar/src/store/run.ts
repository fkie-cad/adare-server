import { defineStore } from 'pinia';
import { Run } from 'src/models/experiment';
import { fetchItems, fetchAdvancedItems, fetchFilterOptions } from 'src/utils/storeUtils';

interface RunState {
  runs: Record<string, Run>;
  filterSupported: boolean;
}

export const useRunStore = defineStore('run', {
  state: (): RunState => ({
    runs: {},
    filterSupported: false,
  }),

  actions: {
    async fetchRuns(query: string) {
      this.runs = await fetchItems('run', query);
    },

    async fetchRun(ulid: string) {
      await this.fetchRuns(`ulid=${ulid}`);
      const result = Object.values(this.runs).filter(run => run.ulid === ulid);
      if (result.length > 0) {
        this.runs[result[0].ulid] = result[0];
        return result[0];
      }
    },

    getRun(ulid: string) {
      return this.runs[ulid];
    },

    async fetchRunsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string) {
      await fetchAdvancedItems('run', this.fetchRuns, limit, offset, sortBy, descending, filterString);
    },

    isFilterSupported() {
      return this.filterSupported;
    },

    async fetchFilterOptions(query: string) {
      return await fetchFilterOptions('run', query);
    },

    async fetchRows(query: string) {
      await this.fetchRuns(query);
    },

    async fetchRowsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string) {
      await this.fetchRunsAdvanced(limit, offset, sortBy, descending, filterString);
    },

    getRows() {
      return Object.values(this.runs);
    },
  },
});

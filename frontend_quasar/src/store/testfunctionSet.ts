import { defineStore } from 'pinia';
import { TestfunctionSet } from 'src/models/experiment';
import { fetchItems, fetchAdvancedItems, fetchFilterOptions } from 'src/utils/storeUtils';

interface TestfunctionSetState {
  testfunctionSets: Record<string, TestfunctionSet>;
  filterSupported: boolean;
}

export const useTestfunctionSetStore = defineStore('testfunctionSet', {
  state: (): TestfunctionSetState => ({
    testfunctionSets: {},
    filterSupported: false,
  }),

  actions: {
    async fetchTestfunctionSets(query: string) {
      this.testfunctionSets = await fetchItems('testfunction', query);
    },

    async fetchTestfunctionSetsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string) {
      await fetchAdvancedItems('testfunctionSet', this.fetchTestfunctionSets, limit, offset, sortBy, descending, filterString);
    },

    isFilterSupported() {
      return this.filterSupported;
    },

    async fetchFilterOptions(query: string) {
      return await fetchFilterOptions('testfunctionSet', query);
    },

    async fetchRows(query: string) {
      await this.fetchTestfunctionSets(query);
    },

    async fetchRowsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string) {
      await this.fetchTestfunctionSetsAdvanced(limit, offset, sortBy, descending, filterString);
    },

    getRows() {
      return Object.values(this.testfunctionSets);
    },
  },
});

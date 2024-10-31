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
    const data = await fetchItems('testfunction', query);
    this.testfunctionSets = data.reduce((acc: Record<string, TestfunctionSet>, testfunctionSet: TestfunctionSet) => {
      acc[testfunctionSet.name] = testfunctionSet;
      return acc;
    }, {});
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

    getTestfunctionSet(name: string) {
      if (this.testfunctionSets == undefined) {
        return null;
      }
      if (name in this.testfunctionSets) {
        return this.testfunctionSets[name];
      }
      return null;
    },

    // used for DataTable
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

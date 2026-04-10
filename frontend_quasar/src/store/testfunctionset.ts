import { defineStore } from 'pinia';
import { TestfunctionSet } from 'src/models/experiment';
import { fetchItems, fetchAdvancedItems, fetchFilterOptions, ScopedFilterParams } from 'src/utils/storeUtils';

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

    async fetchTestfunctionSetsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string, scopedFilters?: ScopedFilterParams) {
      await fetchAdvancedItems('testfunction', this.fetchTestfunctionSets, limit, offset, sortBy, descending, filterString, scopedFilters);
    },

    isFilterSupported() {
      return this.filterSupported;
    },

    async fetchFilterOptions(query: string) {
      return await fetchFilterOptions('testfunction', query);
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

    async fetchRowsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string, scopedFilters?: ScopedFilterParams) {
      await this.fetchTestfunctionSetsAdvanced(limit, offset, sortBy, descending, filterString, scopedFilters);
    },

    getRows() {
      return this.testfunctionSets ? Object.values(this.testfunctionSets) : [];
    },
  },
});

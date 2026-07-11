import { defineStore } from 'pinia';
import { useTestfunctionSetStore } from 'src/store/testfunctionset';

interface TestfunctionState {
  testfunctionSetStore: ReturnType<typeof useTestfunctionSetStore>;
  testfunctionSet: string;
  filterSupported: boolean;
}

export const useTestfunctionStore = defineStore('testfunction', {
  state: (): TestfunctionState => ({
    testfunctionSetStore: useTestfunctionSetStore(),
    testfunctionSet: '',
    filterSupported: false,
  }),

  actions: {
    setTestfunctionSet(testfunctionSet: string) {
      this.testfunctionSet = testfunctionSet;
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
      return this.testfunctionSetStore.getTestfunctionSet(this.testfunctionSet)?.testfunctions;
    },


  },
});

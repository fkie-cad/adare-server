import { defineStore } from 'pinia';
import { useRunStore } from 'src/store/run';

interface RunEventState {
  runStore: ReturnType<typeof useRunStore>;
  run: string,
  filterSupported: boolean;
}

export const useRunEventStore = defineStore('runevents', {
  state: (): RunEventState => ({
    runStore: useRunStore(),
    run: '',
    filterSupported: false,
  }),

  actions: {
    async setRun(run: string) {
      this.run = run;
      await this.runStore.fetchRun(run);
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
      return this.runStore.getRun(this.run)?.events || [];
    },
  },
});

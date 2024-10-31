import { defineStore } from 'pinia';
import { Request } from 'src/models/experiment';
import { fetchItems, fetchAdvancedItems, fetchFilterOptions } from 'src/utils/storeUtils';

interface RequestState {
  requests: Record<string, Request>;
  filterSupported: boolean;
}

export const useRequestStore = defineStore('request', {
  state: (): RequestState => ({
    requests: {},
    filterSupported: false,
  }),

  actions: {
    async fetchRequests(query: string) {
      this.requests = await fetchItems('request', query);
    },

    async fetchRequestsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string) {
      await fetchAdvancedItems('request', this.fetchRequests, limit, offset, sortBy, descending, filterString);
    },

    isFilterSupported() {
      return this.filterSupported;
    },

    async fetchFilterOptions(query: string) {
      return await fetchFilterOptions('request', query);
    },

    async fetchRows(query: string) {
      await this.fetchRequests(query);
    },

    async fetchRowsAdvanced(limit?: number, offset?: number, sortBy?: string, descending?: boolean, filterString?: string) {
      await this.fetchRequestsAdvanced(limit, offset, sortBy, descending, filterString);
    },

    getRows() {
      return Object.values(this.requests);
    },
  },
});

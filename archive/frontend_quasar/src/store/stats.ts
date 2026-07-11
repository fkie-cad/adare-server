import { defineStore } from 'pinia';
import { Stats } from 'src/models/stats';
import { api } from 'boot/axios';

interface StatsState {
  stats: Stats;
}

export const useStatsStore = defineStore('stats', {
  state: (): StatsState => ({
    stats: {} as Stats,
  }),

  actions: {
    async fetchStats() {
      this.stats = await api.get('stats/').then(res => res.data);
    }
  },
});

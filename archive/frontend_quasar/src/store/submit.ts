import { defineStore } from 'pinia';
import { api } from 'src/boot/axios';

interface SubmitState {
  loading: boolean;
  error: string | null;
  lastResult: { pr_url: string; pr_number: number } | null;
}

export const useSubmitStore = defineStore('submit', {
  state: (): SubmitState => ({
    loading: false,
    error: null,
    lastResult: null,
  }),

  actions: {
    async submitExperiment(name: string, playbook: File, metadata: File) {
      this.loading = true;
      this.error = null;
      this.lastResult = null;
      try {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('playbook', playbook);
        formData.append('metadata', metadata);
        const response = await api.post('submit/experiment/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        this.lastResult = response.data;
      } catch (e: unknown) {
        const err = e as { response?: { data?: { error?: string } } };
        this.error = err.response?.data?.error || 'Failed to submit experiment';
      } finally {
        this.loading = false;
      }
    },

    async submitTestfunction(name: string, testfunction: File, requirements: File) {
      this.loading = true;
      this.error = null;
      this.lastResult = null;
      try {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('testfunction', testfunction);
        formData.append('requirements', requirements);
        const response = await api.post('submit/testfunction/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        this.lastResult = response.data;
      } catch (e: unknown) {
        const err = e as { response?: { data?: { error?: string } } };
        this.error = err.response?.data?.error || 'Failed to submit testfunction';
      } finally {
        this.loading = false;
      }
    },

    async submitEnvironment(name: string, environment: File) {
      this.loading = true;
      this.error = null;
      this.lastResult = null;
      try {
        const formData = new FormData();
        formData.append('name', name);
        formData.append('environment', environment);
        const response = await api.post('submit/environment/', formData, {
          headers: { 'Content-Type': 'multipart/form-data' },
        });
        this.lastResult = response.data;
      } catch (e: unknown) {
        const err = e as { response?: { data?: { error?: string } } };
        this.error = err.response?.data?.error || 'Failed to submit environment';
      } finally {
        this.loading = false;
      }
    },

    reset() {
      this.loading = false;
      this.error = null;
      this.lastResult = null;
    },
  },
});

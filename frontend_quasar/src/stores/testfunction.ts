import { defineStore } from 'pinia';
import axios from 'axios';
import API_URLS from 'src/api';
import { TestFunction } from 'src/datatypes/scenario';


export const useTestfunctionStore = defineStore('testfunction', {
  state: () => ({
    testfunctions: [] as TestFunction[],
  }),

  getters: {

  },

  actions: {
    GetTestfunctions() {
      return Object.values(this.testfunctions);
    },
    async LoadTestfunctionsAll() {
      await axios.get(API_URLS.TESTFUNCTION).then((response) => {
        this.testfunctions = response.data;
      });
    },
    async FilterTestfunctions(query: string) {
      let testfunction_list: TestFunction[] = [];
      await axios.get(API_URLS.TESTFUNCTION + query).then((response) => {
        testfunction_list = response.data;
      });
      return testfunction_list;
    }
  },



});

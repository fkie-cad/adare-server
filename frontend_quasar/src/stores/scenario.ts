import { defineStore } from 'pinia';
import axios from 'axios';
import API_URLS from 'src/api';
import { Scenario, ScenarioDict, ExperimentDict, Experiment } from 'src/datatypes/scenario';


export const useScenarioStore = defineStore('scenario', {
  state: () => ({
    scenarios: {} as ScenarioDict,
  }),

  getters: {
  },

  actions: {
    CleanUpScenario(){
      this.scenarios = {} as ScenarioDict
    },
    async LoadScenarioAll(){
      await axios.get('http://localhost:8000/api/scenario/').then(
        (response) => {
          for(const scenario_data of response.data){
            this.scenarios[scenario_data.uuid] = scenario_data
          }
        }
      )
    },
    async LoadScenario(uuid: string){
      await axios.get('http://localhost:8000/api/scenario/'+uuid+'/').then(
        (response) => {
          this.scenarios[uuid] = response.data
        }
      )
    },
    GetScenario(uuid: string){
      return this.scenarios[uuid]
    },
    GetScenarioList(){
      return Object.values(this.scenarios)
    },
    async FilterScenarioListRemote(query: string){
      let scenario_list: Scenario[] = []
      await axios.get('http://localhost:8000/api/scenario/'+query).then(
        (response) => {
          scenario_list = response.data
        }
      )
      return scenario_list
    },
  },



});

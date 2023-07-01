import { defineStore } from 'pinia';
import axios from 'axios';
import API_URLS from 'src/api';
import { Scenario, ScenarioDict, ExperimentDict, Experiment } from 'src/datatypes/scenario';


export const useScenarioStore = defineStore('scenario', {
  state: () => ({
    scenarios: {} as ScenarioDict,
    experiment: {} as ExperimentDict,
  }),

  getters: {
  },

  actions: {
    // SCEANRIO PART
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

    // EXPERIMENT PART
    async LoadExperimentAll(){
      await axios.get('http://localhost:8000/api/experiment/').then(
        (response) => {
          for(const experiment_data of response.data){
            this.experiment[experiment_data.uuid] = experiment_data
          }
        }
      )
    },
    async LoadExperiment(uuid: string){
      await axios.get('http://localhost:8000/api/experiment/'+uuid+'/').then(
        (response) => {
          this.experiment[uuid] = response.data
        }
      )
    },
    async LoadExperimentByScenario(scenario_uuid: string){
      await axios.get('http://localhost:8000/api/experiment/scenario_'+scenario_uuid).then(
        (response) => {
          for(const experiment_data of response.data){
            this.experiment[experiment_data.uuid] = experiment_data
            console.log(experiment_data)
          }
        }
      )
    },
    GetExperiment(uuid: string){
      return this.experiment[uuid]
    },
    GetExperimentList(){
      return Object.values(this.experiment)
    },
    async FilterExperimentListRemote(query: string){
      let experiment_list: Experiment[] = []
      await axios.get('http://localhost:8000/api/experiment/'+query).then(
        (response) => {
          experiment_list = response.data
        }
      )
      return experiment_list
    },
  },

});

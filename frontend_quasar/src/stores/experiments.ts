import { defineStore } from 'pinia';
import axios from 'axios';
import { ExperimentDict, Experiment } from 'src/datatypes/scenario';


export const useExperimentStore = defineStore('experiment', {
  state: () => ({
    experiment: {} as ExperimentDict,
  }),

  getters: {
  },

  actions: {
    CleanUpExperiment(){
      this.experiment = {} as ExperimentDict
    },
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
      await axios.get('http://localhost:8000/api/experiment/experiment_'+uuid+'/').then(
        (response) => {
          this.experiment[uuid] = response.data
        }
      )
    },
    async LoadExperimentByScenario(scenario_uuid: string){
      this.CleanUpExperiment()
      await axios.get('http://localhost:8000/api/experiment/scenario_'+scenario_uuid).then(
        (response) => {
          for(const experiment_data of response.data){
            this.experiment[experiment_data.uuid] = experiment_data
            this.experiment[experiment_data.uuid].action_file_name = 'actions_' + experiment_data.uuid + '.py'
            this.experiment[experiment_data.uuid].testset_file_name = 'testset_' + experiment_data.uuid + '.py'
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

import { defineStore } from 'pinia';
import axios from 'axios';
import { RequestDict } from 'src/datatypes/scenario';


export const useRequestStore = defineStore('request', {
  state: () => ({
    requests: {} as RequestDict
  }),

  getters: {
  },

  actions: {
    CleanUpScenario(){
      this.requests = {} as RequestDict
    },
    async LoadRequestsAll(){
      await axios.get('http://localhost:8000/api/request/').then(
        (response) => {
          for(const request_data of response.data){
            this.requests[request_data.uuid] = request_data
          }
        }
      )
    },
    GetRequest(uuid: string){
      return this.requests[uuid]
    },
    GetRequestList(){
      return Object.values(this.requests)
    }
  },



});

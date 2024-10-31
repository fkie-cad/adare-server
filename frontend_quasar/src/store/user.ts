import { defineStore } from 'pinia';
import { api } from 'src/boot/axios';
import { User } from 'src/models/experiment';

interface UserState {
  userDict: Record<string, User>;
}


export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    userDict: {},
  }),

  getters: {
  },

  actions: {
    GetUser(username: string) {
      return this.userDict[username]
    },
    clearUserDict(){
      this.userDict = {}
    },
    initializeUserDict(username: string){
      this.userDict[username] = {
        username: username,
        email: '',
        teams: [],
        avatar: '',
        achievements: [],
      }
    },
    async UpdateProfileInformation(username: string){
      if (!(username in this.userDict)) {
        this.initializeUserDict(username)
      }
      await api.get( 'user/'+ username + '/profile').then((response) => {
        this.userDict[username].email = response.data.user.email
        this.userDict[username].teams = response.data.teams
        this.userDict[username].avatar = response.data.avatar
      })
    },
    GetUserTeams(username: string) {
      return this.userDict[username].teams
    },
    GetUserAvatarThumbnail(username: string) {
      return this.userDict[username].avatar;
    },
    GetUserEmail(username: string) {
      if (!(username in this.userDict)) {
        this.initializeUserDict(username)
      }
      return this.userDict[username].email
    }
  },


});

import { defineStore } from 'pinia';
import { api } from 'src/boot/axios';
import { UserInfo } from 'src/models/user';

interface UserState {
  userDict: UserInfo;
}


export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    userDict: {} as UserInfo,
  }),

  getters: {
  },

  actions: {
    clearUserDict(){
      this.userDict = {} as UserInfo
    },
    initializeUserDict(username: string){
      this.userDict[username] = {
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
        console.log(response.data)
        this.userDict[username].email = response.data.user.email
        // this.userDict[username].achievements = response.data.achievements
        // // get all iconfile names and convert them to urls
        // for (let i = 0; i < this.userDict[username].achievements.length; i++) {
        //   this.userDict[username].achievements[i].iconfile = API_URLS.FILE_API + 'achievements/' + this.userDict[username].achievements[i].iconfile
        // }
        this.userDict[username].teams = response.data.teams
        this.userDict[username].avatar = response.data.avatar
      })
    },
    GetUserTeams(username: string) {
      return this.userDict[username].teams
    },
    // GetUserAchievements(username: string) {
    //   if (!(username in this.userDict)) {
    //     this.initializeUserDict(username)
    //   }
    //   return this.userDict[username].achievements
    // },
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

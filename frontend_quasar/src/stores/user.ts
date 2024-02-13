import { defineStore } from 'pinia';
import axios from 'axios';
import API_URLS from 'src/api';
import { Achievement, UserInfo } from 'src/datatypes/user';


export const useUserStore = defineStore('user', {
  state: () => ({
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
        groups: [],
        avatar: '',
        achievements: [],
      }
    },
    async UpdateProfileInformation(username: string){
      if (!(username in this.userDict)) {
        this.initializeUserDict(username)
      }
      await axios.get(API_URLS.USER_API + username + '/profile').then((response) => {
        console.log(response.data)
        this.userDict[username].email = response.data.user.email
        // this.userDict[username].achievements = response.data.achievements
        // // get all iconfile names and convert them to urls
        // for (let i = 0; i < this.userDict[username].achievements.length; i++) {
        //   this.userDict[username].achievements[i].iconfile = API_URLS.FILE_API + 'achievements/' + this.userDict[username].achievements[i].iconfile
        // }
        this.userDict[username].groups = response.data.groups
        this.userDict[username].avatar = response.data.avatar
      })
      console.log(this.userDict[username])
    },
    GetUserGroups(username: string) {
      if (!(username in this.userDict)) {
        this.initializeUserDict(username)
      }
      return this.userDict[username].groups
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

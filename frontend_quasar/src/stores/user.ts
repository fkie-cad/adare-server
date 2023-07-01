import { defineStore } from 'pinia';
import axios from 'axios';
import API_URLS from 'src/api';


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
        avatar_thumbnail_sm: '',
        avatar_thumbnail_md: '',
        avatar_thumbnail_lg: '',
        groups: [],
        achievements: [],
      }
    },
    async UpdateProfileInformation(username: string){
      if (!(username in this.userDict)) {
        this.initializeUserDict(username)
      }
      await axios.get(API_URLS.USER_API + username + '/profile').then((response) => {
        this.userDict[username].email = response.data.user.email
        this.userDict[username].achievements = response.data.achievements
        this.userDict[username].groups = response.data.groups
      })
      await axios.get(
          API_URLS.USER_API+username+'/profile/avatar',
      ).then((response) => {
        console.log(response.data)
        if (response.data.avatar_thumbnail_sm) {
          this.userDict[username].avatar_thumbnail_sm = API_URLS.SERVER_URL.slice(0,-1) + response.data.avatar_thumbnail_sm
        }
        if (response.data.avatar_thumbnail_md){
          this.userDict[username].avatar_thumbnail_md = API_URLS.SERVER_URL.slice(0,-1) + response.data.avatar_thumbnail_md
        }
        if (response.data.avatar_thumbnail_lg){
          this.userDict[username].avatar_thumbnail_lg = API_URLS.SERVER_URL.slice(0,-1) + response.data.avatar_thumbnail_lg
        }
      }).catch((error) => {
        console.log(error)
      })
    },
    GetUserGroups(username: string) {
      if (!(username in this.userDict)) {
        this.initializeUserDict(username)
      }
      return this.userDict[username].groups
    },
    GetUserAchievements(username: string) {
      if (!(username in this.userDict)) {
        this.initializeUserDict(username)
      }
      return this.userDict[username].achievements
    },
    GetUserAvatarThumbnail(username: string, size = 'md') {
      if (!(username in this.userDict)) {
        this.initializeUserDict(username)
      }
      if (size === 'sm'){
        return this.userDict[username].avatar_thumbnail_sm
      } else if (size === 'lg'){
        return this.userDict[username].avatar_thumbnail_lg
      } else if (size === 'md'){
        return this.userDict[username].avatar_thumbnail_md
      }
    },
    GetUserEmail(username: string) {
      if (!(username in this.userDict)) {
        this.initializeUserDict(username)
      }
      return this.userDict[username].email
    }
  },


});


interface UserInfo {
  [username: string]: {
    email: string;
    avatar_thumbnail_sm: string;
    avatar_thumbnail_md: string;
    avatar_thumbnail_lg: string;
    groups: [];
    achievements: [];
  };
}

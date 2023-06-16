import { defineStore } from 'pinia';
import axios from 'axios';
import API_URLS from 'src/api';


export const useUserStore = defineStore('user', {
  state: () => ({
    username: '',
    email: '',
    avatar_thumbnail: '',
    groups: [],
    achievements: [],
  }),

  getters: {
    GetUser (state) {
      return state;
    },
    GetUserUsername (state) {
      return state.username;
    },
    GetUserEmail (state) {
      return state.email;
    },
    GetUserUserAvatarThumbnail (state) {
      return state.avatar_thumbnail;
    },
    GetUserGroups (state) {
      return state.groups;
    },
    GetUserAchievements (state) {
      return state.achievements;
    }
  },

  actions: {
    UpdateUserUsername(username: string){
      this.username = username
    },
    UpdateUserEmail(email: string){
      this.email = email
    },
    UpdateUserAvatarThumbnail(avatar_thumbnail_url: string){
      this.avatar_thumbnail = avatar_thumbnail_url
    },
    UpdateUserGroups(groups: []){
      this.groups = groups
    },
    UpdateUserAchievements(achievements: []){
      this.achievements = achievements
    },
    RemoveUserAvatarThumbnail(){
      this.avatar_thumbnail = ''
    },
    ResetUser(){
      this.username = ''
      this.email = ''
      this.avatar_thumbnail = ''
      this.groups = []
      this.achievements = []
    },
    async UpdateProfileInformation(){
      await axios.get(
        API_URLS.USER_API+'profile/',
      ).then((response) => {
        this.UpdateUserEmail(response.data.user.email)
        this.UpdateUserGroups(response.data.groups)
        this.UpdateUserUsername(response.data.user.username)
        if (response.data.achievements) {
          this.UpdateUserAchievements(response.data.achievements)
        }
      }).catch((error) => {
        console.log(error)
      })
      await axios.get(
        API_URLS.USER_API+'profile/avatar/',
      ).then((response) => {
        if (response.data.avatar_thumbnail){
          this.UpdateUserAvatarThumbnail(API_URLS.SERVER_URL.slice(0,-1) + response.data.avatar_thumbnail)
        }
      }).catch((error) => {
        console.log(error)
      })
      console.log(this.$state)
    }
  }
});

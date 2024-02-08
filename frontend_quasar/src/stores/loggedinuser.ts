import { defineStore } from 'pinia';
import axios from 'axios';
import API_URLS from 'src/api';
import { useLoginStore } from 'src/stores/login';
import { Achievement, UserInfo } from 'src/datatypes/user';

export const useLoggedInUserStore = defineStore('userloggedin', {
  state: () => ({
    username: '',
    email: '',
    teams: [],
    achievements: [] as Achievement[],
    avatar: '',
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
    GetUserTeams (state) {
      return state.teams;
    },
    GetUserAchievements (state) {
      return state.achievements;
    },
    IsSupervisor (state) {
      const groups: string[] = state.teams;
      return groups.includes('supervisor') || groups.includes('admin');
    }
  },

  actions: {
    ResetUser(){
      this.username = ''
      this.email = ''
      this.teams = []
      this.achievements = []
      this.avatar = ''
    },

    async UpdateProfileInformation(){
      const LoginStore= useLoginStore();
      if (!LoginStore.IsLoggedIn) {
        return
      }
      await axios.get(
        API_URLS.USER_API+'profile/',
      ).then((response) => {
        console.log(response.data)
        this.email = response.data.user.email
        this.teams = response.data.teams
        this.username = response.data.user.username
        this.avatar = response.data.avatar
        // this.achievements = response.data.achievements
        // get all iconfile names and convert them to urls
        // for (let i = 0; i < this.achievements.length; i++) {
        //   this.achievements[i].iconfile = API_URLS.FILE_API + 'achievements/' + this.achievements[i].iconfile
        // }
      }).catch((error) => {
        console.log(error)
      })
    },

  }
});



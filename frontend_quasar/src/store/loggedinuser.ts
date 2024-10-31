import { defineStore } from 'pinia';
import { useLoginStore } from 'src/store/login';
import { Achievement, Team } from 'src/models/user';
import { api } from 'src/boot/axios';

export const useLoggedInUserStore = defineStore('userloggedin', {
  state: () => ({
    username: '',
    email: '',
    teams: [] as Team[],
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
      const groups: Team[] = state.teams;
      for (let i = 0; i < groups.length; i++) {
        if (groups[i].name === 'supervisor' || groups[i].name === 'admin') {
          return true;
        }
      }
      return false;
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
      await api.get('user/profile/',
      ).then((response) => {
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



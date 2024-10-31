import { defineStore } from 'pinia';
import { useLoginStore } from 'src/store/login';
import { api } from 'src/boot/axios';
import { User } from 'src/models/experiment';

export interface LoggedInUserState {
  user: User;
}

export const useLoggedInUserStore = defineStore('userloggedin', {
  state: (): LoggedInUserState => ({
    user: {
      username: '',
      email: '',
      teams: [],
      achievements: [],
      avatar: ''
    }
  }),

  getters: {
    GetUser (state) {
      return state.user;
    },
    IsSupervisor (state) {
      for (let i = 0; i < state.user.teams.length; i++) {
        if (state.user.teams[i].name === 'supervisor' || state.user.teams[i].name === 'admin') {
          return true;
        }
      }
      return false;
    }
  },

  actions: {
    ResetUser(){
      this.user = {
        username: '',
        email: '',
        teams: [],
        achievements: [],
        avatar: ''
      }
    },

    async UpdateProfileInformation(){
      const LoginStore= useLoginStore();
      if (!LoginStore.IsLoggedIn) {
        return
      }
      await api.get('user/profile/',
      ).then((response) => {
        this.user = response.data;
      }).catch((error) => {
        console.log(error)
      })
    },

  }
});



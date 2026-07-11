import { defineStore } from 'pinia';
import { api } from 'src/boot/axios';
import { Profile } from 'src/models/experiment';
import { useLoginStore } from 'src/store/login';

interface UserState {
  userProfiles: Record<string, Profile>;
  loggedInUserProfile: Profile | null;
}


export const useUserStore = defineStore('user', {
  state: (): UserState => ({
    userProfiles: {},
    loggedInUserProfile: null,
  }),

  getters: {
    isSupervisor (state) {
      if (!state.loggedInUserProfile) {
        return false;
      }
      for (let i = 0; i < state.loggedInUserProfile.teams.length; i++) {
        if (state.loggedInUserProfile.teams[i].name === 'supervisor' || state.loggedInUserProfile.teams[i].name === 'admin') {
          return true;
        }
      }
      return false;
    }
  },

  actions: {
    getProfile(username: string) {
      if (username in this.userProfiles) {
        return this.userProfiles[username];
      } else if (this.loggedInUserProfile && this.loggedInUserProfile.user.username === username) {
        return this.loggedInUserProfile;
      }
      else {
        return null;
      }
    },

    clearUserProfiles() {
      this.userProfiles = {};
    },

    async fetchProfile(username: string) {
      // check if username is undefined
      if (username === undefined) {
        return;
      }
      await api.get('user/' + username + '/profile').then((response) => {
        this.userProfiles[username] = response.data;
      }).catch((error) => {
        console.log(error);
      });
    },

    async loadLoggedInUserProfile() {
      const LoginStore= useLoginStore();
      if (!LoginStore.isLoggedIn) {
        this.loggedInUserProfile = null;
        return null;
      }
      await api.get('user/profile/').then((response) => {
        this.loggedInUserProfile = response.data;
        return this.loggedInUserProfile;
      }).catch((error) => {
        console.log(error);
      });
    },

    removeLoggedInUserProfile() {
      this.loggedInUserProfile = null;
    }
  },

});

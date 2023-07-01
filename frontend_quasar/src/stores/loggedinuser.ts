import { defineStore } from 'pinia';
import axios from 'axios';
import API_URLS from 'src/api';


export const useLoggedInUserStore = defineStore('userloggedin', {
  state: () => ({
    username: '',
    email: '',
    avatar_thumbnail_sm: '',
    avatar_thumbnail_md: '',
    avatar_thumbnail_lg: '',
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
    GetUserGroups (state) {
      return state.groups;
    },
    GetUserAchievements (state) {
      return state.achievements;
    },
    IsSupervisor (state) {
      const groups: string[] = state.groups;
      return groups.includes('supervisor');
    }
  },

  actions: {
    ResetUser(){
      this.username = ''
      this.email = ''
      this.avatar_thumbnail_sm = ''
      this.avatar_thumbnail_md = ''
      this.avatar_thumbnail_lg = ''
      this.groups = []
      this.achievements = []
    },
    async UploadUserAvatar(file: File|null){
      if (file != null) {
        const formData = new FormData();
        formData.append('avatar', file as File);
        await axios.put(
          API_URLS.USER_API + 'profile/avatar/',
          formData,
          {
            headers: {
              'Content-Type': 'multipart/form-data'
            }
          }
        )
        await this.UpdateProfileInformation()
      }
    },

    async RemoveUserAvatar(){
      await axios.delete(
        API_URLS.USER_API + 'profile/avatar/',
      )
      this.avatar_thumbnail_sm = ''
      this.avatar_thumbnail_md = ''
      this.avatar_thumbnail_lg = ''
      await this.UpdateProfileInformation()
    },

    async UpdateProfileInformation(){
      await axios.get(
        API_URLS.USER_API+'profile/',
      ).then((response) => {
        this.email = response.data.user.email
        this.groups = response.data.groups
        this.username = response.data.user.username
        if (response.data.achievements) {
          this.achievements = response.data.achievements
        }
      }).catch((error) => {
        console.log(error)
      })
      await axios.get(
        API_URLS.USER_API+'profile/avatar/',
      ).then((response) => {
        if (response.data.avatar_thumbnail_sm) {
          this.avatar_thumbnail_sm = API_URLS.SERVER_URL.slice(0, -1) + response.data.avatar_thumbnail_sm
        }
        if (response.data.avatar_thumbnail_md) {
          this.avatar_thumbnail_md = API_URLS.SERVER_URL.slice(0, -1) + response.data.avatar_thumbnail_md
        }
        if (response.data.avatar_thumbnail_lg) {
          this.avatar_thumbnail_lg = API_URLS.SERVER_URL.slice(0, -1) + response.data.avatar_thumbnail_lg
        }
      }).catch((error) => {
        console.log(error)
      })
    },
    GetUserAvatarThumbnail (size: string) {
      if (size == 'lg') {
        return this.avatar_thumbnail_lg;
      }
      else if (size == 'md') {
        return this.avatar_thumbnail_md;
      }
      else if (size == 'sm') {
        return this.avatar_thumbnail_sm;
      }
    },
  }
});

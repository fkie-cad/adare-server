import { defineStore } from 'pinia';
import axios from 'axios';
import API_URLS from 'src/api';
import { useLoginStore } from 'src/stores/login';
import { Achievement, UserInfo } from 'src/datatypes/user';

export const useLoggedInUserStore = defineStore('userloggedin', {
  state: () => ({
    username: '',
    email: '',
    groups: [],
    achievements: [] as Achievement[],
    updatetrigger: 0,
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
      return groups.includes('supervisor') || groups.includes('admin');
    }
  },

  actions: {
    ResetUser(){
      this.username = ''
      this.email = ''
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
      }
      this.TriggerUpdate()
    },

    TriggerUpdate(){
      if (this.updatetrigger > 1000) {
        this.updatetrigger = 0
      } else {
        this.updatetrigger += 1
      }
    },

    async RemoveUserAvatar(){
      await axios.delete(
        API_URLS.USER_API + 'profile/avatar/',
      )
      this.TriggerUpdate()
    },

    async UpdateProfileInformation(){
      const LoginStore= useLoginStore();
      if (!LoginStore.IsLoggedIn) {
        return
      }
      await axios.get(
        API_URLS.USER_API+'profile/',
      ).then((response) => {
        this.email = response.data.user.email
        this.groups = response.data.groups
        this.username = response.data.user.username
        this.achievements = response.data.achievements
        // get all iconfile names and convert them to urls
        for (let i = 0; i < this.achievements.length; i++) {
          this.achievements[i].iconfile = API_URLS.FILE_API + 'achievements/' + this.achievements[i].iconfile
        }
      }).catch((error) => {
        console.log(error)
      })
    },

    GetUserAvatarThumbnail (size: string):string {
      if (this.username === '') {
        return ''
      }
      return API_URLS.FILE_API+'avatar/'+this.username+'/thumbnail/' + size + '/?trigger='+this.updatetrigger.toString()+'/';
    },
  }
});



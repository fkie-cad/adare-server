import { defineStore } from 'pinia';
import axios from 'axios';
import API_URLS from 'src/api'
import {useLoggedInUserStore} from 'stores/loggedinuser';


export const useLoginStore = defineStore('login', {
  state: () => ({
    loggedIn: false,
    loginUser : '',
    loginToken: '',
  }),

  getters: {
    GetLoginUser (state) {
      return state.loginUser;
    },
    IsLoggedIn (state) {
      return state.loggedIn;
    },
    GetLoginToken(state){
      return state.loginToken
    }
  },

  actions: {
    SetLoginTokenVars(){
      if (localStorage.getItem('LoginToken') && localStorage.getItem('LoginUser') && localStorage.getItem('LoginTokenExpiration')) {
        this.loggedIn = true
        this.loginUser = localStorage.getItem('LoginUser') || ''
        this.loginToken = localStorage.getItem('LoginToken') || ''
        axios.defaults.headers.common['Authorization'] = 'Token ' + this.loginToken
      } else{
        this.loggedIn = false
        this.loginUser = ''
        this.loginToken = ''
        axios.defaults.headers.common['Authorization'] = ''
      }
    },
    SetLoginToken(user: string, token: string, expirationDate: string){
      localStorage.setItem('LoginUser', user)
      localStorage.setItem('LoginToken', token)
      localStorage.setItem('LoginTokenExpiration', new Date(expirationDate).toISOString())
      this.SetLoginTokenVars()
    },
    RemoveLoginToken(){
      localStorage.removeItem('LoginUser')
      localStorage.removeItem('LoginToken')
      localStorage.removeItem('LoginTokenExpiration')
      this.SetLoginTokenVars()
    },
    InitLogin(){
      const expiry = localStorage.getItem('LoginTokenExpiration')
      if (!expiry) {
        this.RemoveLoginToken()
        this.SetLoginTokenVars()
        return
      }
      const expiry_data = new Date(expiry)
      if (expiry_data <= new Date()) {
        this.RemoveLoginToken()
      }
      this.SetLoginTokenVars()
    },
    Logout(){
      this.RemoveLoginToken()
      const LoggedInUserStore= useLoggedInUserStore()
      LoggedInUserStore.ResetUser()
    }
  }
});

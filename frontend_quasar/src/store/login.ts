import { defineStore } from 'pinia';
import {useUserStore} from 'src/store/user';


export const useLoginStore = defineStore('login', {
  state: () => ({
    loggedIn: false,
    loginUser : '',
    loginToken: '',
  }),

  getters: {
    getLoginUser (state) {
      return state.loginUser;
    },
    isLoggedIn (state) {
      return state.loggedIn;
    },
    getLoginToken(state){
      return state.loginToken
    }
  },

  actions: {
    setLoginTokenVars(){
      if (localStorage.getItem('LoginToken') && localStorage.getItem('LoginUser') && localStorage.getItem('LoginTokenExpiration')) {
        this.loggedIn = true
        this.loginUser = localStorage.getItem('LoginUser') || ''
        this.loginToken = localStorage.getItem('LoginToken') || ''
      } else{
        this.loggedIn = false
        this.loginUser = ''
        this.loginToken = ''
      }
    },
    setLoginToken(user: string, token: string, expirationDate: string){
      localStorage.setItem('LoginUser', user)
      localStorage.setItem('LoginToken', token)
      localStorage.setItem('LoginTokenExpiration', new Date(expirationDate).toISOString())
      this.setLoginTokenVars()
    },
    removeLoginToken(){
      localStorage.removeItem('LoginUser')
      localStorage.removeItem('LoginToken')
      localStorage.removeItem('LoginTokenExpiration')
      this.setLoginTokenVars()
    },
    initLogin(){
      const expiry = localStorage.getItem('LoginTokenExpiration')
      if (!expiry) {
        this.removeLoginToken()
        this.setLoginTokenVars()
        return
      }
      const expiry_data = new Date(expiry)
      if (expiry_data <= new Date()) {
        this.removeLoginToken()
      }
      this.setLoginTokenVars()
    },
    logout(){
      this.removeLoginToken()
      const userStore = useUserStore()
      userStore.removeLoggedInUserProfile()
    }
  }
});

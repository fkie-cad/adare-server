import { create } from 'zustand'

interface AuthState {
  isLoggedIn: boolean
  loginUser: string
  loginToken: string
  initLogin: () => void
  setLoginToken: (user: string, token: string, expirationDate: string) => void
  removeLoginToken: () => void
  logout: () => void
}

export const useAuthStore = create<AuthState>((set) => ({
  isLoggedIn: false,
  loginUser: '',
  loginToken: '',

  initLogin: () => {
    const token = localStorage.getItem('LoginToken')
    const user = localStorage.getItem('LoginUser')
    const expiry = localStorage.getItem('LoginTokenExpiration')

    if (!token || !user || !expiry) {
      set({ isLoggedIn: false, loginUser: '', loginToken: '' })
      return
    }

    if (new Date(expiry) <= new Date()) {
      localStorage.removeItem('LoginToken')
      localStorage.removeItem('LoginUser')
      localStorage.removeItem('LoginTokenExpiration')
      set({ isLoggedIn: false, loginUser: '', loginToken: '' })
      return
    }

    set({ isLoggedIn: true, loginUser: user, loginToken: token })
  },

  setLoginToken: (user: string, token: string, expirationDate: string) => {
    localStorage.setItem('LoginUser', user)
    localStorage.setItem('LoginToken', token)
    localStorage.setItem('LoginTokenExpiration', new Date(expirationDate).toISOString())
    set({ isLoggedIn: true, loginUser: user, loginToken: token })
  },

  removeLoginToken: () => {
    localStorage.removeItem('LoginUser')
    localStorage.removeItem('LoginToken')
    localStorage.removeItem('LoginTokenExpiration')
    set({ isLoggedIn: false, loginUser: '', loginToken: '' })
  },

  logout: () => {
    localStorage.removeItem('LoginUser')
    localStorage.removeItem('LoginToken')
    localStorage.removeItem('LoginTokenExpiration')
    set({ isLoggedIn: false, loginUser: '', loginToken: '' })
  },
}))

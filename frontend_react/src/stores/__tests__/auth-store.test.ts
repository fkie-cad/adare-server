import { describe, it, expect, beforeEach } from 'vitest'
import { useAuthStore } from '../auth-store'

describe('auth-store', () => {
  beforeEach(() => {
    localStorage.clear()
    useAuthStore.setState({ isLoggedIn: false, loginUser: '', loginToken: '' })
  })

  it('starts logged out', () => {
    const state = useAuthStore.getState()
    expect(state.isLoggedIn).toBe(false)
    expect(state.loginUser).toBe('')
    expect(state.loginToken).toBe('')
  })

  it('sets login token and user', () => {
    const future = new Date(Date.now() + 86400000).toISOString()
    useAuthStore.getState().setLoginToken('testuser', 'abc123', future)

    const state = useAuthStore.getState()
    expect(state.isLoggedIn).toBe(true)
    expect(state.loginUser).toBe('testuser')
    expect(state.loginToken).toBe('abc123')
    expect(localStorage.getItem('LoginToken')).toBe('abc123')
    expect(localStorage.getItem('LoginUser')).toBe('testuser')
  })

  it('removes login token on logout', () => {
    const future = new Date(Date.now() + 86400000).toISOString()
    useAuthStore.getState().setLoginToken('testuser', 'abc123', future)
    useAuthStore.getState().logout()

    const state = useAuthStore.getState()
    expect(state.isLoggedIn).toBe(false)
    expect(localStorage.getItem('LoginToken')).toBeNull()
  })

  it('initLogin restores valid session from localStorage', () => {
    const future = new Date(Date.now() + 86400000).toISOString()
    localStorage.setItem('LoginToken', 'tok123')
    localStorage.setItem('LoginUser', 'bob')
    localStorage.setItem('LoginTokenExpiration', future)

    useAuthStore.getState().initLogin()

    const state = useAuthStore.getState()
    expect(state.isLoggedIn).toBe(true)
    expect(state.loginUser).toBe('bob')
  })

  it('initLogin clears expired session', () => {
    const past = new Date(Date.now() - 86400000).toISOString()
    localStorage.setItem('LoginToken', 'tok123')
    localStorage.setItem('LoginUser', 'bob')
    localStorage.setItem('LoginTokenExpiration', past)

    useAuthStore.getState().initLogin()

    const state = useAuthStore.getState()
    expect(state.isLoggedIn).toBe(false)
    expect(localStorage.getItem('LoginToken')).toBeNull()
  })
})

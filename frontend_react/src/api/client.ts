import axios from 'axios'
import { API_BASE } from './endpoints'

export const api = axios.create({
  baseURL: API_BASE,
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
})

// Add auth token to requests
api.interceptors.request.use((config) => {
  const token = localStorage.getItem('LoginToken')
  const user = localStorage.getItem('LoginUser')
  const expiry = localStorage.getItem('LoginTokenExpiration')

  if (token && user && expiry) {
    config.headers['Authorization'] = `Token ${token}`
  } else {
    config.headers['Authorization'] = ''
  }

  return config
})

// Refresh CSRF on 403 (retry once only)
api.interceptors.response.use(
  (response) => response,
  async (err) => {
    const status = err.response?.status
    const config = err.config

    if (status === 403 && config && !config._csrfRetry) {
      config._csrfRetry = true
      await api.get('csrf/')
      return api(config)
    }

    return Promise.reject(err)
  },
)

// Clear token on 401
api.interceptors.response.use(
  (response) => response,
  (error) => {
    if (error.response?.status === 401) {
      localStorage.removeItem('LoginToken')
      localStorage.removeItem('LoginUser')
      localStorage.removeItem('LoginTokenExpiration')
    }
    return Promise.reject(error)
  },
)

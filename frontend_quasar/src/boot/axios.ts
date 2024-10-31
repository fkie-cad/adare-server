import { boot } from 'quasar/wrappers';
import axios, { AxiosInstance } from 'axios';


// for production
export const SERVER_URL = 'https://adare.seclab-bonn.de/'
// export const FRONTEND_URL = 'https://adare.seclab-bonn.de/'

// for local development
// export const SERVER_URL = 'http://127.0.0.1:8000/'
export const FRONTEND_URL = 'http://localhost:9000/'

// Create an Axios instance
const api: AxiosInstance = axios.create({
  baseURL: SERVER_URL+'api/',
  withCredentials: true,
  xsrfCookieName: 'csrftoken',
  xsrfHeaderName: 'X-CSRFToken',
});

api.interceptors.response.use(response => response, async err => {
  const status = err.response ? err.response.status : null

  if (status === 403) {
    // Refresh our session token
    await axios.get('csrf')

    // Return a new request using the original request's configuration
    return axios(err.response.config)
  }

  return Promise.reject(err)
})

api.interceptors.request.use((config) => {
  const token = localStorage.getItem('LoginToken');
  const user = localStorage.getItem('LoginUser');
  const tokenExpiration = localStorage.getItem('LoginTokenExpiration');
  console.log(token, user, tokenExpiration)

  // Check if token, user, and expiration exist and if the token is still valid
  if (token && user && tokenExpiration) {
    config.headers['Authorization'] = `Token ${token}`;
  } else {
    config.headers['Authorization'] = '';
  }

  return config;
}, (error) => {
  return Promise.reject(error);
});


export default boot(({ app }) => {
  // For use inside Vue files (Options API) through this.$axios and this.$api
  app.config.globalProperties.$axios = axios;
  app.config.globalProperties.$api = api;
});

export { api };

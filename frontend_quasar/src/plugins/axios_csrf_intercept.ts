import axios from 'axios'
import API_URLS from 'src/api/index'

axios.defaults.xsrfCookieName = 'csrftoken'
axios.defaults.xsrfHeaderName = 'X-CSRFToken'
axios.defaults.withCredentials = true

axios.interceptors.response.use(response => response, async err => {
  const status = err.response ? err.response.status : null

  if (status === 403) {
    // Refresh our session token
    await axios.get(API_URLS.CSRF_API)

    // Return a new request using the original request's configuration
    return axios(err.response.config)
  }

  return Promise.reject(err)
})

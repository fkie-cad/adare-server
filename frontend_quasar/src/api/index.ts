// for production
// const SERVER_URL = 'https://adare.seclab-bonn.de/'
// const FRONTEND_URL = 'https://adare.seclab-bonn.de/'

// for local development
const SERVER_URL = 'http://127.0.0.1:8000/'
const FRONTEND_URL = 'http://localhost:9000/'

const API_URL = SERVER_URL + 'api/'

const AUTH_API = API_URL + 'auth/'
const GITEA_OAUTH_API = AUTH_API + 'gitea/'
const GITEA_OAUTH_URL_API = GITEA_OAUTH_API + 'callback/'
const GITEA_OAUTH_API_REDIRECT_URI = FRONTEND_URL + 'login/oauth'
//const GITEA_OAUTH_API_REDIRECT_URI = SERVER_URL + 'auth/o/gitea/'
const CSRF_API = API_URL + 'csrf/'
const USER_API = API_URL + 'user/'
const EXPERIMENT_API = API_URL + 'experiment/'
const SCENARIO_API = API_URL + 'scenario/'
const LIST_EXPERIMENTS = EXPERIMENT_API + 'list/'
const TESTFUNCTION = API_URL + 'testfunction/'
const FILE_API = API_URL + 'file/'

export default {
  SERVER_URL: SERVER_URL,
  API: API_URL,
  CSRF_API: CSRF_API,
  USER_API: USER_API,
  EXPERIMENT_API: EXPERIMENT_API,
  SCENARIO_API: SCENARIO_API,
  LIST_EXPERIMENTS: LIST_EXPERIMENTS,
  TESTFUNCTION: TESTFUNCTION,
  FILE_API: FILE_API,
  AUTH_API: AUTH_API,
  GITEA_OAUTH_API: GITEA_OAUTH_API,
  GITEA_OAUTH_URL_API: GITEA_OAUTH_URL_API,
  GITEA_REDIRECT_URI: GITEA_OAUTH_API_REDIRECT_URI
}

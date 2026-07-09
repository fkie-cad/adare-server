// All API endpoints are relative — Vite proxy handles /api → Django :8000
export const API_BASE = '/api/'
export const FRONTEND_URL = `${window.location.origin}/`

export const endpoints = {
  experiments: 'experiment/',
  runs: 'run/',
  environments: 'environment/',
  testfunctionSets: 'testfunction/',
  requests: 'request/',
  stats: 'stats/',
  userProfile: 'user/profile/',
  userProfileByName: (username: string) => `user/${username}/profile`,
  csrf: 'csrf/',
  authGiteaCallback: 'auth/gitea/callback/',
  authGitea: 'auth/gitea/',
  submitExperiment: 'submit/experiment/',
  submitTestfunction: 'submit/testfunction/',
  submitEnvironment: 'submit/environment/',
  authDev: 'auth/dev/',
  testfunctionSetDownload: (name: string) => `download/testfunction_${name}/`,
  experimentDashboard: 'experiment/dashboard/',
  filterOptions: (endpoint: string) => `${endpoint}/filteroptions/`,
  achievementIcon: (name: string) => `file/achievements/${name}`,
} as const

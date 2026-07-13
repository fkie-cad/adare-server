import {
  createRootRouteWithContext,
  createRoute,
  redirect,
  Outlet,
} from '@tanstack/react-router'
import type { QueryClient } from '@tanstack/react-query'
import { MainLayout } from '@/components/layout/main-layout'

import HomePage from '@/pages/home'
import LoginPage from '@/pages/login'
import OauthCallbackPage from '@/pages/oauth-callback'
import ExperimentListPage from '@/pages/experiment-list'
import ExperimentDetailPage from '@/pages/experiment-detail'
import RunListPage from '@/pages/run-list'
import RunDetailPage from '@/pages/run-detail'
import EnvironmentListPage from '@/pages/environment-list'
import TestfunctionSetListPage from '@/pages/testfunction-set-list'
import TestfunctionSetDetailPage from '@/pages/testfunction-set-detail'
import RequestListPage from '@/pages/request-list'
import ProfileSelfPage from '@/pages/profile-self'
import ProfileUserPage from '@/pages/profile-user'
import SubmitExperimentPage from '@/pages/submit-experiment'
import SubmitTestfunctionPage from '@/pages/submit-testfunction'
import SubmitEnvironmentPage from '@/pages/submit-environment'
import EnvironmentDetailPage from '@/pages/environment-detail'
import EditExperimentPage from '@/pages/edit-experiment'
import EditEnvironmentPage from '@/pages/edit-environment'
import EditTestfunctionPage from '@/pages/edit-testfunction'
import NotFoundPage from '@/pages/not-found'

interface RouterContext {
  queryClient: QueryClient
}

function requireAuth() {
  const token = localStorage.getItem('LoginToken')
  const expiry = localStorage.getItem('LoginTokenExpiration')

  if (!token) {
    throw redirect({ to: '/login' })
  }

  // Check token expiration
  if (expiry && new Date(expiry) <= new Date()) {
    localStorage.removeItem('LoginToken')
    localStorage.removeItem('LoginUser')
    localStorage.removeItem('LoginTokenExpiration')
    throw redirect({ to: '/login' })
  }
}

const rootRoute = createRootRouteWithContext<RouterContext>()({
  component: MainLayout,
})

const indexRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/',
  beforeLoad: () => {
    const token = localStorage.getItem('LoginToken')
    throw redirect({ to: token ? '/home' : '/login' })
  },
})

const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/home',
  beforeLoad: requireAuth,
  component: HomePage,
})

// Login routes
const loginRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/login',
  component: Outlet,
})

const loginIndexRoute = createRoute({
  getParentRoute: () => loginRoute,
  path: '/',
  component: LoginPage,
})

const oauthCallbackRoute = createRoute({
  getParentRoute: () => loginRoute,
  path: '/oauth',
  component: OauthCallbackPage,
})

// Experiment routes
const experimentRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/experiment',
  beforeLoad: requireAuth,
  component: Outlet,
})

const experimentListRoute = createRoute({
  getParentRoute: () => experimentRoute,
  path: '/',
  component: ExperimentListPage,
})

const experimentDetailRoute = createRoute({
  getParentRoute: () => experimentRoute,
  path: '/$name',
  component: ExperimentDetailPage,
})

const experimentEditRoute = createRoute({
  getParentRoute: () => experimentRoute,
  path: '/$name/edit',
  component: EditExperimentPage,
})

// Run routes
const runRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/run',
  beforeLoad: requireAuth,
  component: Outlet,
})

const runListRoute = createRoute({
  getParentRoute: () => runRoute,
  path: '/',
  component: RunListPage,
})

const runDetailRoute = createRoute({
  getParentRoute: () => runRoute,
  path: '/$ulid',
  component: RunDetailPage,
})

// Environment routes
const environmentRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/environment',
  beforeLoad: requireAuth,
  component: Outlet,
})

const environmentListRoute = createRoute({
  getParentRoute: () => environmentRoute,
  path: '/',
  component: EnvironmentListPage,
})

const environmentDetailRoute = createRoute({
  getParentRoute: () => environmentRoute,
  path: '/$name',
  component: EnvironmentDetailPage,
})

const environmentEditRoute = createRoute({
  getParentRoute: () => environmentRoute,
  path: '/$name/edit',
  component: EditEnvironmentPage,
})

// Testfunction set routes
const testfunctionSetRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/testfunctionset',
  beforeLoad: requireAuth,
  component: Outlet,
})

const testfunctionSetListRoute = createRoute({
  getParentRoute: () => testfunctionSetRoute,
  path: '/',
  component: TestfunctionSetListPage,
})

const testfunctionSetDetailRoute = createRoute({
  getParentRoute: () => testfunctionSetRoute,
  path: '/$name',
  component: TestfunctionSetDetailPage,
})

const testfunctionSetEditRoute = createRoute({
  getParentRoute: () => testfunctionSetRoute,
  path: '/$name/edit',
  component: EditTestfunctionPage,
})

// Request
const requestListRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/request',
  beforeLoad: requireAuth,
  component: RequestListPage,
})

// Profile
const profileSelfRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/profile',
  beforeLoad: requireAuth,
  component: ProfileSelfPage,
})

const profileUserRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/user/$username',
  beforeLoad: requireAuth,
  component: ProfileUserPage,
})

// Submit routes
const submitExperimentRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/submit/experiment',
  beforeLoad: requireAuth,
  component: SubmitExperimentPage,
})

const submitTestfunctionRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/submit/testfunction',
  beforeLoad: requireAuth,
  component: SubmitTestfunctionPage,
})

const submitEnvironmentRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/submit/environment',
  beforeLoad: requireAuth,
  component: SubmitEnvironmentPage,
})

// Catch-all
const notFoundRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '*',
  component: NotFoundPage,
})

export const routeTree = rootRoute.addChildren([
  indexRoute,
  homeRoute,
  loginRoute.addChildren([loginIndexRoute, oauthCallbackRoute]),
  experimentRoute.addChildren([
    experimentListRoute,
    experimentDetailRoute,
    experimentEditRoute,
  ]),
  runRoute.addChildren([runListRoute, runDetailRoute]),
  environmentRoute.addChildren([
    environmentListRoute,
    environmentDetailRoute,
    environmentEditRoute,
  ]),
  testfunctionSetRoute.addChildren([
    testfunctionSetListRoute,
    testfunctionSetDetailRoute,
    testfunctionSetEditRoute,
  ]),
  requestListRoute,
  profileSelfRoute,
  profileUserRoute,
  submitExperimentRoute,
  submitTestfunctionRoute,
  submitEnvironmentRoute,
  notFoundRoute,
])

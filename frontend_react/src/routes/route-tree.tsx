import {
  createRootRouteWithContext,
  createRoute,
  lazyRouteComponent,
  redirect,
  Outlet,
} from '@tanstack/react-router'
import type { QueryClient } from '@tanstack/react-query'
import { MainLayout } from '@/components/layout/main-layout'

// Landing, list and auth pages stay in the entry bundle.
import HomePage from '@/pages/home'
import LoginPage from '@/pages/login'
import OauthCallbackPage from '@/pages/oauth-callback'
import ExperimentListPage from '@/pages/experiment-list'
import RunListPage from '@/pages/run-list'
import EnvironmentListPage from '@/pages/environment-list'
import TestfunctionSetListPage from '@/pages/testfunction-set-list'
import RequestListPage from '@/pages/request-list'
import NotFoundPage from '@/pages/not-found'

// Detail, edit, submit and profile pages are code-split: each loads its own
// chunk the first time its route renders. Route definitions (and their
// beforeLoad auth guards) stay eager; only the components are deferred.
const ExperimentDetailPage = lazyRouteComponent(() => import('@/pages/experiment-detail'))
const RunDetailPage = lazyRouteComponent(() => import('@/pages/run-detail'))
const EnvironmentDetailPage = lazyRouteComponent(() => import('@/pages/environment-detail'))
const TestfunctionSetDetailPage = lazyRouteComponent(() => import('@/pages/testfunction-set-detail'))
const EditExperimentPage = lazyRouteComponent(() => import('@/pages/edit-experiment'))
const EditEnvironmentPage = lazyRouteComponent(() => import('@/pages/edit-environment'))
const EditTestfunctionPage = lazyRouteComponent(() => import('@/pages/edit-testfunction'))
const SubmitExperimentPage = lazyRouteComponent(() => import('@/pages/submit-experiment'))
const SubmitTestfunctionPage = lazyRouteComponent(() => import('@/pages/submit-testfunction'))
const SubmitEnvironmentPage = lazyRouteComponent(() => import('@/pages/submit-environment'))
const ProfileSelfPage = lazyRouteComponent(() => import('@/pages/profile-self'))
const ProfileUserPage = lazyRouteComponent(() => import('@/pages/profile-user'))

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
    throw redirect({ to: '/home' })
  },
})

const homeRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/home',
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
  beforeLoad: requireAuth,
  component: EditExperimentPage,
})

// Run routes
const runRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/run',
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
  beforeLoad: requireAuth,
  component: EditEnvironmentPage,
})

// Testfunction set routes
const testfunctionSetRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/testfunctionset',
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
  beforeLoad: requireAuth,
  component: EditTestfunctionPage,
})

// Request
const requestListRoute = createRoute({
  getParentRoute: () => rootRoute,
  path: '/request',
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

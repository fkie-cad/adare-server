import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/login',
  },
  {
    path: '/home',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/HomePage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        },
        props: true,
      },
    ],
  },
  {
    path: '/logfile/:experimentrunulid',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/LogfilePage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        },
        props: true,
      },
    ],
  },
  {
    path: '/environment',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/EnvironmentListPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        }
      },
    ],
  },
  {
    path: '/testfunctionset',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/TestfunctionsetListPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        }
      },
    ],
  },
  {
    path: '/experiment',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/ExperimentListPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        }
      },
    ],
  },
  {
    path: '/experimentdetails/:ulid',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/ExperimentPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        },
        props: true,
      },
    ],
  },
  {
    path: '/testfunction/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/TestfunctionWikiPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        },
        props: true,
      },
    ],
  },
  {
    path: '/login',
    component: () => import('layouts/MainLayout.vue'),
    children: [
        {
          path: '',
          components: {
            main: () => import('pages/LoginPage.vue'),
            header: () => import('components/HeaderDefault.vue'),
          }
        },
        {
          path: 'oauth',
          components: {
            main: () => import('pages/OauthWaítingPage.vue'),
            header: () => import('components/HeaderDefault.vue'),
          }
        }
    ],
  },
  {
    path: '/profile/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/ProfilePageSelf.vue'),
          header: () => import('components/HeaderDefault.vue'),
        }
      },
    ],
  },
  {
    path: '/user/:username',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/ProfilePage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        },
        props: true,
      },
    ],
  },
  {
    path: '/requests/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/RequestsListPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        }
      }
    ],
  },
  {
    path: '/requests/:ulid',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/RequestsPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        },
        props: true,
      }
    ],
  },
  {
    path: '/experiment/:ulid',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/ExperimentPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        },
        props: true,
      }
    ],
  },
  {
    path: '/runs/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/RunListPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        }
      }
    ],
  },

  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;

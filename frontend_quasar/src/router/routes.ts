import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    redirect: '/scenario',
  },

  {
    path: '/scenario',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/ScenarioPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        }
      },
    ],
  },
  {
    path: '/scenario/:uuid',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/ScenarioExperimentPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        },
        props: true,
      },
    ],
  },
  {
    path: '/experiments',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/ExperimentPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        }
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
          main: () => import('pages/RequestsPage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        }
      }
    ],
  },
  {
    path: '/experiment/:uuid',
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


  // Always leave this as last one,
  // but you can also remove it
  {
    path: '/:catchAll(.*)*',
    component: () => import('pages/ErrorNotFound.vue'),
  },
];

export default routes;

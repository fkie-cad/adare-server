import { RouteRecordRaw } from 'vue-router';

const routes: RouteRecordRaw[] = [
  {
    path: '/',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/IndexPage.vue'),
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
    path: '/profile',
    component: () => import('layouts/MainLayout.vue'),
    children: [
      {
        path: '',
        components: {
          main: () => import('pages/ProfilePage.vue'),
          header: () => import('components/HeaderDefault.vue'),
        }
      },
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

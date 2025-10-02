import { createRouter, createWebHistory } from 'vue-router';

export const router = createRouter({
  history: createWebHistory(import.meta.env.BASE_URL),
  routes: [
    {
      path: '/dashboard',
      name: 'home',
      component: () => import('@/pages').then((module) => module.Home),
      meta: {
        title: 'Главная страница',
        layout: 'default',
      },
    },
    {
      path: '/dashboard/:slug',
      name: 'region',
      component: () => import('@/pages').then((module) => module.Slug),
      meta: {
        title: 'Подробная информация по региону',
        layout: 'default',
      },
    },
    {
      path: '/',
      name: 'auth',
      component: () => import('@/pages').then((module) => module.Auth),
      meta: {
        title: 'Авторизация',
        layout: 'auth',
      },
    },
    {
      path: '/loaddata',
      name: 'loaddata',
      component: () => import('@/pages').then((module) => module.LoadData),
      meta: {
        title: 'Загрузка данных',
        layout: 'load',
      },
    },
  ],
});

router.beforeEach((to, _from, next) => {
  const lct = localStorage.getItem('lct');

  const role = lct ? JSON.parse(lct).role : null;

  if (role === null && to.name !== 'auth') {
    return next({ name: 'auth' });
  } else if (role === 'admin' && to.name === 'auth') {
    return next({ name: 'home' });
  } else if (role === 'user' && (to.name === 'auth' || to.name === 'home')) {
    return next({ name: 'loaddata' });
  }

  const title = to.meta.title;
  document.title = title;
  next();
});

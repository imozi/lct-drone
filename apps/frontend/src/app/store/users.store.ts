import { defineStore } from 'pinia';
import { shallowRef } from 'vue';
import { useRouter } from 'vue-router';

export const useUsersStore = defineStore('users', () => {
  const router = useRouter();

  const admin = shallowRef({
    login: 'admin',
    password: 'Admin123321',
  });

  const user = shallowRef({
    login: 'user',
    password: 'User123321',
  });

  const checkAdmin = (login: string, password: string) => {
    const isValid = login === admin.value.login && password === admin.value.password;

    if (isValid) {
      localStorage.setItem('lct', JSON.stringify({ role: 'admin' }));
    }

    return isValid;
  };
  const checkUser = (login: string, password: string) => {
    const isValid = login === user.value.login && password === user.value.password;

    if (isValid) {
      localStorage.setItem('lct', JSON.stringify({ role: 'user' }));
    }

    return isValid;
  };

  const getRole = () => {
    const lct = localStorage.getItem('lct');

    return lct ? JSON.parse(lct).role : null;
  };

  const logaut = () => {
    localStorage.removeItem('lct');
    router.push({ name: 'auth', replace: true });
  };

  return {
    admin,
    user,
    checkAdmin,
    checkUser,
    logaut,
    getRole,
  };
});

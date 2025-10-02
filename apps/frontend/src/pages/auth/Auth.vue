<script setup lang="ts">
import { UserOutlined, LockOutlined } from '@ant-design/icons-vue';
import { Form, FormItem, Input, InputPassword, Button, Tabs, TabPane, App } from 'ant-design-vue';
import { reactive, computed, ref } from 'vue';
import { useRouter } from 'vue-router';

import { useUsersStore } from '@/app/store';

interface FormState {
  username: string;
  password: string;
}

const router = useRouter();
const { message } = App.useApp();

const { checkAdmin, checkUser } = useUsersStore();

const isSending = ref<boolean>(false);
const formStateSystem = reactive<FormState>({
  username: '',
  password: '',
});

const formStateLoad = reactive<FormState>({
  username: '',
  password: '',
});

const onSystemFinish = async () => {
  try {
    isSending.value = true;
    await new Promise((resolve, reject) => {
      setTimeout(() => {
        const isValid = checkAdmin(formStateSystem.username, formStateSystem.password);

        if (!isValid) {
          return reject(false);
        }

        resolve(isValid);
      }, 1000);
    });

    isSending.value = false;
    router.push({ path: '/dashboard', replace: true });
  } catch (e) {
    isSending.value = false;
    message.error('Неверный логин или пароль');
    formStateSystem.username = '';
    formStateSystem.password = '';
  }
};

const onLoadFinish = async () => {
  try {
    isSending.value = true;
    await new Promise((resolve, reject) => {
      setTimeout(() => {
        const isValid = checkUser(formStateLoad.username, formStateLoad.password);

        if (!isValid) {
          return reject(false);
        }

        resolve(isValid);
      }, 1000);
    });

    isSending.value = false;
    router.push({ path: '/loaddata', replace: true });
  } catch (e) {
    isSending.value = false;
    message.error('Неверный логин или пароль');
    formStateLoad.username = '';
    formStateLoad.password = '';
  }
};

const disabledSystem = computed(() => {
  return !(formStateSystem.username && formStateSystem.password);
});

const disabledLoad = computed(() => {
  return !(formStateLoad.username && formStateLoad.password);
});
</script>

<template>
  <div class="main-wrapper flex h-screen">
    <div class="m-auto overflow-hidden rounded-2xl bg-white shadow-lg">
      <div class="grid grid-cols-2">
        <div class="p-5">
          <Tabs>
            <TabPane key="1" tab="Войти в систему">
              <div class="flex h-full flex-col items-center justify-center">
                <div class="text-xl font-medium">
                  <p>Войдите в систему</p>
                </div>
                <div class="text-slate-100">
                  <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 100 100">
                    <path
                      fill="currentColor"
                      d="M19.53 28.49a3.85 3.85 0 0 0-3.533 2.343C6.706 31.364-.029 32.257 0 32.955c.027.693 6.712.997 15.928.724c.32.862.936 1.58 1.738 2.027H16.17v2.742h-1.83a.874.874 0 0 0-.875.874v1.954c0 .483.391.874.874.874h12.316c3.103.73 3.45 1.843 5.774 3.88c-.38 2.113-.94 4.42-1.378 6.414v16.973a2.092 2.092 0 1 0 4.185 0V61.21c-.048-6.9 1.066-9.69 4.905-15.031l.965-.448c0 4.146 2.866 4.395 6.908 5.32h-3.036c-.924 0-1.674.75-1.674 1.675v10c0 .924.75 1.674 1.674 1.674h10.044c.924 0 1.674-.75 1.674-1.674v-10c0-.925-.75-1.674-1.674-1.674h-3.033c4.041-.928 6.905-1.176 6.905-5.321l.965.448c4.857 5.026 4.905 8.447 4.905 15.03v8.207a2.092 2.092 0 0 0 4.185 0V52.444c-.513-2.191-1.062-4.487-1.58-6.762c2.199-2.155 3.101-2.64 5.956-3.532h12.336a.874.874 0 0 0 .874-.874v-1.954a.874.874 0 0 0-.874-.874H83.83v-2.742h-1.496a3.85 3.85 0 0 0 1.738-2.027c9.216.273 15.901-.031 15.928-.724c.029-.698-6.706-1.59-15.997-2.122a3.852 3.852 0 0 0-6.943-.302c-9.307-.283-16.103.018-16.142.716c-.029.693 6.615 1.58 15.827 2.112a3.85 3.85 0 0 0 1.839 2.347h-1.496v2.742C67.654 38.426 60.352 33.685 50 33.49c-10.003.212-18.38 4.958-27.088 4.958v-2.742h-1.496a3.85 3.85 0 0 0 1.839-2.347c9.212-.532 15.856-1.42 15.827-2.112c-.039-.698-6.835-1-16.142-.716a3.85 3.85 0 0 0-3.41-2.04M50 53.503c2.347 0 4.276 1.929 4.276 4.276S52.347 62.055 50 62.055s-4.278-1.93-4.278-4.277s1.93-4.276 4.278-4.276m0 2.51c-.99 0-1.767.776-1.767 1.766s.777 1.766 1.767 1.766s1.765-.776 1.765-1.766s-.775-1.765-1.765-1.765"
                      color="currentColor"
                    />
                  </svg>
                </div>
                <div class="w-full p-5">
                  <Form name="normal_login" :model="formStateSystem" autocomplete="off" @finish="onSystemFinish">
                    <FormItem>
                      <Input size="large" v-model:value="formStateSystem.username" placeholder="Логин">
                        <template #prefix>
                          <UserOutlined />
                        </template>
                      </Input>
                    </FormItem>
                    <FormItem>
                      <InputPassword size="large" v-model:value="formStateSystem.password" placeholder="Пароль">
                        <template #prefix>
                          <LockOutlined />
                        </template>
                      </InputPassword>
                    </FormItem>
                    <FormItem>
                      <Button
                        size="large"
                        class="flex w-full items-center"
                        :disabled="disabledSystem"
                        type="primary"
                        html-type="submit"
                        :loading="isSending"
                      >
                        Войти
                      </Button>
                    </FormItem>
                  </Form>
                </div>
              </div>
            </TabPane>
            <TabPane key="2" tab="Войти для загрузки данных">
              <div class="flex h-full flex-col items-center justify-center">
                <div class="text-xl font-medium">
                  <p>Загрузка данных</p>
                </div>
                <div class="text-slate-100">
                  <svg xmlns="http://www.w3.org/2000/svg" width="100" height="100" viewBox="0 0 20 20">
                    <path
                      fill="currentColor"
                      d="M16.88 9.1A4 4 0 0 1 16 17H5a5 5 0 0 1-1-9.9V7a3 3 0 0 1 4.52-2.59A4.98 4.98 0 0 1 17 8c0 .38-.04.74-.12 1.1M11 11h3l-4-4l-4 4h3v3h2z"
                    />
                  </svg>
                </div>
                <div class="w-full p-5">
                  <Form name="normal_login" :model="formStateLoad" autocomplete="off" @finish="onLoadFinish">
                    <FormItem>
                      <Input size="large" v-model:value="formStateLoad.username" placeholder="Логин">
                        <template #prefix>
                          <UserOutlined />
                        </template>
                      </Input>
                    </FormItem>
                    <FormItem>
                      <InputPassword size="large" v-model:value="formStateLoad.password" placeholder="Пароль">
                        <template #prefix>
                          <LockOutlined />
                        </template>
                      </InputPassword>
                    </FormItem>
                    <FormItem>
                      <Button
                        size="large"
                        class="flex w-full items-center"
                        :disabled="disabledLoad"
                        type="primary"
                        html-type="submit"
                        :loading="isSending"
                      >
                        Войти
                      </Button>
                    </FormItem>
                  </Form>
                </div>
              </div>
            </TabPane>
          </Tabs>
        </div>
        <div class="max-w-96">
          <img src="/login-drone.webp" alt="" />
        </div>
      </div>
    </div>
  </div>
</template>

<style lang="scss"></style>

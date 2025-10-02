import { axios } from '@lct/services';
import { createApp } from 'vue';

import { pinia } from './providers/pinia';
import { router } from './providers/router';
import { App } from './ui';

import '@/app/assets/styles.css';
import 'maplibre-gl/dist/maplibre-gl.css';

export const app = createApp(App);

app.use(router);
app.use(pinia);
app.provide('axios', axios);

app.mount('#portal');

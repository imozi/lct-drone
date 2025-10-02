/// <reference types="vite/client" />
import 'vue-router';

interface ImportMetaEnv {
  readonly VITE_BACKEND_URL: string;
  readonly VITE_TILESSERVER_URL: string;
  readonly VITE_ADMIN_USERNAME: string;
  readonly VITE_ADMIN_PASSWORD: string;
}

export type AppLayout = 'default' | 'auth' | 'load';

declare module 'vue-router' {
  interface RouteMeta {
    title: string;
    layout: AppLayout;
  }
}

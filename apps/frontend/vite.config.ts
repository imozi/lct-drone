import { fileURLToPath, URL } from 'node:url';

import tailwindcss from '@tailwindcss/vite';
import vue from '@vitejs/plugin-vue';
import { defineConfig } from 'vite';

// https://vite.dev/config/
export default defineConfig({
  plugins: [vue(), tailwindcss()],
  publicDir: './src/shared/public',
  resolve: {
    alias: {
      '@': fileURLToPath(new URL('./src', import.meta.url)),
      '@lct/ui': fileURLToPath(new URL('../../packages/ui/src', import.meta.url)),
      '@lct/services': fileURLToPath(new URL('../../packages/services/src', import.meta.url)),
    },
  },
});

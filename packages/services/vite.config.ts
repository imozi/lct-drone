import { fileURLToPath } from 'node:url';

import vue from '@vitejs/plugin-vue';
import { defineConfig } from 'vite';
import dts from 'vite-plugin-dts';

export default defineConfig({
  plugins: [
    vue(),
    dts({
      include: ['src'],
      outDir: 'dist',
      insertTypesEntry: true,
    }),
  ],
  build: {
    lib: {
      entry: fileURLToPath(new URL('./src/index.ts', import.meta.url)),
      name: 'lctui',
      fileName: (_, name) => `${name}.mjs`,
      formats: ['es'],
    },
    rollupOptions: {
      external: ['vue', 'tailwindcss', 'tailwind-variants', 'tailwind-merge'],
    },
  },
});

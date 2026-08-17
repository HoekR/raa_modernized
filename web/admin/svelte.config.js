import adapter from '@sveltejs/adapter-static';
import { vitePreprocess } from '@sveltejs/vite-plugin-svelte';

/** @type {import('@sveltejs/kit').Config} */
const adminBase = process.env.ADMIN_BASE_PATH || '';

const config = {
  preprocess: vitePreprocess(),
  kit: {
    adapter: adapter({
      pages: 'build',
      assets: 'build',
      fallback: 'index.html',
      precompress: false,
    }),
    alias: {
      '@raa/shared': '../shared/src',
    },
    paths: {
      base: adminBase,
    },
  },
};

export default config;

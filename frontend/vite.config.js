// frontend/vite.config.js
import { sveltekit } from '@sveltejs/kit/vite';
import { defineConfig } from 'vite';

export default defineConfig({
  plugins: [sveltekit()],
  server: {
    proxy: {
      '/api': { target: 'http://api:8000', changeOrigin: true }
    }
  },
  test: {
    environment: 'happy-dom',
    setupFiles: ['./src/lib/vitest.setup.js']
  }
});

import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: 'autoUpdate',
      includeAssets: ['favicon.ico'],
      manifest: {
        name: 'Blue Velvet',
        short_name: 'Velvet',
        description:
          'A Progressive Web App built with React, Vite, and TypeScript',
        theme_color: '#ffffff',
      },
    }),
  ],
  server: {
    proxy: {
      // In dev, forward same-origin /api requests to the FastAPI backend.
      // No rewrite: the backend paths already start with /api.
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
      },
    },
  },
});

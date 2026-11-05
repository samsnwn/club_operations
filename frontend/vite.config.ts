import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig(() => {
  const backendURL = process.env.BACKEND_URL ?? 'http://localhost:8080';

  return {
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
        // Host dev uses http://localhost:8080; Docker overrides BACKEND_URL.
        '/api': {
          target: backendURL,
          changeOrigin: true,
        },
      },
    },
  };
});

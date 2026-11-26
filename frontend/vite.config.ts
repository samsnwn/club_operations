import tailwindcss from '@tailwindcss/vite';
import react from '@vitejs/plugin-react';
import { defineConfig } from 'vite';
import { VitePWA } from 'vite-plugin-pwa';

export default defineConfig(() => {
  const backendURL = process.env.BACKEND_URL ?? 'http://localhost:8080';
  // LAN address served by the dev HTTPS proxy (infra/.env); Vite rejects
  // unknown hostnames, while localhost and IPs stay allowed by default.
  const publicHost = process.env.PUBLIC_HOST;

  return {
    plugins: [
      react(),
      tailwindcss(),
      VitePWA({
        registerType: 'autoUpdate',
        includeAssets: ['favicon.svg', 'apple-touch-icon-180x180.png'],
        manifest: {
          name: 'Blue Velvet',
          short_name: 'Velvet',
          description: 'Club operations for Blue Velvet',
          // Night theme is the primary design target (docs/design-system.md).
          theme_color: '#080b18',
          background_color: '#080b18',
          icons: [
            {
              src: 'favicon.svg',
              sizes: 'any',
              type: 'image/svg+xml',
              purpose: 'any',
            },
            {
              src: 'pwa-192x192.png',
              sizes: '192x192',
              type: 'image/png',
              purpose: 'any',
            },
            {
              src: 'pwa-512x512.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'any',
            },
            {
              src: 'maskable-icon-512x512.png',
              sizes: '512x512',
              type: 'image/png',
              purpose: 'maskable',
            },
          ],
        },
        workbox: {
          // Navigations still fall back to index.html, but never for /api:
          // API paths must reach the server (or fail) instead of the shell.
          navigateFallbackDenylist: [/^\/api\//],
        },
      }),
    ],
    server: {
      ...(publicHost ? { allowedHosts: [publicHost] } : {}),
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

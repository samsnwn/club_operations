import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'
import { VitePWA } from "vite-plugin-pwa";

export default defineConfig({
  plugins: [
    react(),
    VitePWA({
      registerType: "autoUpdate",
      includeAssets: ["favicon.ico", "apple-touch-icon.png", "masked-icon.svg"],
      manifest: {
        name: "Blue Velvet",
        short_name: "Velvet",
        description:
          "A Progressive Web App built with React, Vite, and TypeScript",
        theme_color: "#ffffff",
      },
    }),
  ],
});

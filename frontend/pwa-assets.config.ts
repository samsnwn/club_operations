import {
  defineConfig,
  minimal2023Preset,
} from '@vite-pwa/assets-generator/config';

// Night background (docs/design-system.md), matching the manifest colours.
const night = { background: '#080b18' };

// minimal-2023 without favicon.ico and the 64px icon: the SVG favicon stays
// the browser icon, and the maskable and Apple icons sit on Night.
export default defineConfig({
  headLinkOptions: { preset: '2023' },
  preset: {
    ...minimal2023Preset,
    transparent: {
      ...minimal2023Preset.transparent,
      sizes: [192, 512],
      favicons: [],
    },
    maskable: { ...minimal2023Preset.maskable, resizeOptions: night },
    apple: { ...minimal2023Preset.apple, resizeOptions: night },
  },
  images: ['public/favicon.svg'],
});

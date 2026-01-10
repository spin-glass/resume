// @ts-check
import { defineConfig } from 'astro/config';
import tailwindcss from '@tailwindcss/vite';
import mdx from '@astrojs/mdx';
import vercel from '@astrojs/vercel';

const isVercel = process.env.VERCEL === '1';
const site = 'https://spin-glass.github.io';
const base = isVercel ? '/' : '/resume';

// https://astro.build/config
export default defineConfig({
  site,
  base,
  adapter: vercel({
    webAnalytics: {
      enabled: true,
    },
  }),
  integrations: [mdx()],
  vite: {
    plugins: [tailwindcss()]
  }
});

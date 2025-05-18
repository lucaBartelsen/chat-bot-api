// vite.config.js
// Place this file in the root of your project

import { defineConfig } from 'vite';
import react from '@vitejs/plugin-react';
import tailwindcss from '@tailwindcss/vite';
import { resolve } from 'path';

export default defineConfig({
  plugins: [
    react(),
    tailwindcss({
      // The path to your Tailwind config file
      config: './tailwind.config.css',
    }),
  ],
  resolve: {
    alias: {
      '@': resolve(__dirname, './src'),
    },
  },
  server: {
    port: 8080,
    open: true,
  },
  build: {
    outDir: 'dist',
    minify: 'terser',
    sourcemap: false,
  }
});
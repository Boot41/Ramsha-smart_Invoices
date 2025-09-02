import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'
import tailwindcss from '@tailwindcss/vite'
import { resolve } from 'path'

export default defineConfig({
  plugins: [
    react(),
    tailwindcss(),
  ],
  build: {
    sourcemap: false,
  },
  resolve: {
    alias: {
      '@': resolve(__dirname, 'src'),
      '@client-api': resolve(__dirname, 'api'),
      '@types': resolve(__dirname, 'types'),
      '@hooks': resolve(__dirname, 'hooks'),
      '@stores': resolve(__dirname, 'stores'),
    },
  },
  server: {
    port: 5174,
    proxy: {
      // Proxy specific API routes to backend
      '^/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        secure: false,
      },
    },
  },
})
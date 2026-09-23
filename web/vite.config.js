import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// In dev the browser hits /api which Vite proxies to the api container.
export default defineConfig({
  plugins: [react()],
  server: {
    host: true,
    port: 5173,
    proxy: {
      '/api': { target: 'http://localhost:8000', changeOrigin: true },
    },
  },
})

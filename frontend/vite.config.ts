import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],
  server: {
    // Same-origin /api in dev, so the browser never needs CORS for the API
    proxy: {
      '/api': 'http://localhost:8000',
    },
  },
})

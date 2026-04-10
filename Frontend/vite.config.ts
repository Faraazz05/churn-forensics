import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

// https://vitejs.dev/config/
export default defineConfig({
  base: '/churn-forensics/',
  plugins: [react()],
  build: {
    rollupOptions: {
      output: {
        manualChunks(id) {
          if (id.includes('node_modules')) {
            if (id.includes('react') || id.includes('react-dom') || id.includes('react-router-dom')) return 'vendor';
            if (id.includes('@tanstack/react-query')) return 'query';
            if (id.includes('recharts')) return 'charts';
            if (id.includes('framer-motion')) return 'motion';
            if (id.includes('axios')) return 'axios';
          }
        }
      }
    }
  },
  server: {
    proxy: {
      '/health':    'http://localhost:3000',
      '/predict':   'http://localhost:3000',
      '/explain':   'http://localhost:3000',
      '/upload':    'http://localhost:3000',
      '/segments':  'http://localhost:3000',
      '/drift':     'http://localhost:3000',
      '/insights':  'http://localhost:3000',
      '/models':    'http://localhost:3000',
      '/customers': 'http://localhost:3000',
      '/watchlist': 'http://localhost:3000',
      '/report':    'http://localhost:3000',
      '/pipeline':  'http://localhost:3000',
      '/logs':      'http://localhost:3000',
      '/uploads':   'http://localhost:3000',
      '/docs':      'http://localhost:3000',
    }
  }
})

import { defineConfig } from 'vite'
import react from '@vitejs/plugin-react'

export default defineConfig({
  plugins: [react()],
  server: {
    port: 5173,
    proxy: {
      '/api': {
        target: 'http://localhost:8000',
        changeOrigin: true,
        // Agrega trailing slash a rutas raíz (/api/ventas → /api/ventas/)
        // así el backend no hace un 307 redirect que el browser sigue sin Authorization header
        rewrite: (path) => {
          const [pathname, query] = path.split('?')
          const segments = pathname.split('/').filter(Boolean)
          if (segments.length === 2 && !pathname.endsWith('/')) {
            return pathname + '/' + (query ? '?' + query : '')
          }
          return path
        },
      },
    },
  },
})

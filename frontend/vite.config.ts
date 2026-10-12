/// <reference types="vitest/config" />
import react from '@vitejs/plugin-react'
import { defineConfig, loadEnv } from 'vite'

// O .env fica na raiz do projeto (um nível acima). Só variáveis que começam com VITE_ são
// lidas aqui; DATABASE_URL e outras nunca chegam ao frontend.
const PASTA_DO_ENV = '..'

export default defineConfig(({ mode }) => {
  const env = loadEnv(mode, PASTA_DO_ENV, 'VITE_')
  const urlDaApi = env.VITE_API_URL || 'http://localhost:8000'

  return {
    envDir: PASTA_DO_ENV,
    plugins: [react()],
    server: {
      port: 5173,
      // A página chama /api/... e o Vite repassa para o backend (ADR-006). Assim o navegador
      // conversa com um endereço só e o backend não precisa liberar CORS.
      proxy: {
        '/api': {
          target: urlDaApi,
          changeOrigin: true,
          rewrite: (caminho) => caminho.replace(/^\/api/, ''),
        },
      },
    },
    build: {
      // Uso local: um arquivo só, sem dividir o código. O aviso de tamanho não se aplica.
      chunkSizeWarningLimit: 1500,
    },
    test: {
      environment: 'jsdom',
      setupFiles: ['./src/testes/preparar.ts'],
      css: false,
    },
  }
})

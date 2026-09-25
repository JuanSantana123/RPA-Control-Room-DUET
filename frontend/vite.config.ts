import react from '@vitejs/plugin-react'
import { defineConfig } from 'vite'

// ============================================================
// DUET CORE - VITE
// ============================================================
//
// Configuração do servidor de desenvolvimento do frontend.
//
// allowedHosts:
// Autoriza o hostname privado oficial utilizado pelo DUET
// dentro da rede privada.
//
// Não utilizamos "true" aqui porque isso liberaria qualquer
// hostname. Mantemos somente os nomes explicitamente permitidos.
// ============================================================

// https://vite.dev/config/
export default defineConfig({
  plugins: [react()],

  server: {
    allowedHosts: [
      'duet-core',
    ],
  },
})
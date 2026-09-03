import axios from "axios";

/**
 * ============================================================
 * CONFIGURAÇÃO DA API
 * ============================================================
 *
 * Define a URL base do nosso backend FastAPI.
 *
 * Durante o desenvolvimento:
 *
 * React/Vite  → http://localhost:5173
 * FastAPI     → http://localhost:9000
 *
 * Todas as chamadas feitas através deste cliente Axios
 * utilizarão esta URL como base.
 * ============================================================
 */
const api = axios.create({
  baseURL: "http://localhost:9000",
});

/**
 * Exporta o cliente Axios configurado.
 *
 * Assim, as páginas e componentes do React não precisam
 * repetir a URL do Control Room.
 *
 * Exemplo:
 *
 * api.get("/agents")
 * api.get("/executions")
 * api.post("/agents/VM_001/execution/run")
 */
export default api;
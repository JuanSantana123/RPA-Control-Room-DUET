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
    // Endereço da API do Control Room.
    // Usa automaticamente o mesmo host/IP pelo qual o frontend foi acessado.
    // Ex.:
    // - localhost:5173       -> localhost:9000
    // - 172.25.32.1:5173     -> 172.25.32.1:9000
    baseURL: `${window.location.protocol}//${window.location.hostname}:9000`,

    // Permite que o navegador envie os cookies
    // de sessão nas requisições para a API.
    //
    // Sem isso, o cookie HttpOnly criado no login
    // não será enviado pelo Axios nas próximas chamadas.
    withCredentials: true
});
 
export default api;
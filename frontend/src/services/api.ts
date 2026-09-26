import axios from "axios";
import { runtimeConfig } from "../config/runtime";

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
    baseURL: runtimeConfig.apiBaseUrl,

    // Impede que falhas de rede mantenham formulários indefinidamente
    // no estado de envio. Operações específicas podem sobrescrever esse
    // valor quando possuírem um contrato de longa duração.
    timeout: runtimeConfig.apiTimeoutMs,

    // Permite que o navegador envie os cookies
    // de sessão nas requisições para a API.
    //
    // Sem isso, o cookie HttpOnly criado no login
    // não será enviado pelo Axios nas próximas chamadas.
    withCredentials: true,
    headers: {
        Accept: "application/json",
    },
});

api.interceptors.request.use((config) => {
    const requestId = typeof crypto.randomUUID === "function"
        ? crypto.randomUUID()
        : `${Date.now()}-${Math.random().toString(16).slice(2)}`;

    config.headers.set("X-Client-Request-ID", requestId);
    return config;
});
 
export default api;

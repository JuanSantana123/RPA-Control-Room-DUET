// ============================================================
// DUET CORE - RUNTIME CONFIGURATION
// ============================================================
//
// Responsabilidade:
//
// - resolver a URL pública da API do Control Room;
// - permitir configuração por ambiente sem hardcode;
// - suportar desenvolvimento local;
// - suportar instalações On-Premise;
// - suportar DUET Cloud / SaaS;
// - resolver configurações que podem ser alteradas sem
//   recompilar o frontend.
//
// Ordem de prioridade:
//
// 1. Configuração carregada em runtime pelo servidor;
// 2. Variáveis Vite utilizadas durante desenvolvimento/build;
// 3. Fallback seguro conforme o ambiente.
//
// Nenhuma funcionalidade do frontend deve conhecer:
// - IP do servidor;
// - domínio do cliente;
// - porta interna do FastAPI;
// - endereço Cloud.
//
// Tudo deve consumir runtimeConfig.
// ============================================================


// ============================================================
// VALORES PADRÃO
// ============================================================

// A porta 9000 existe somente como fallback de desenvolvimento.
//
// Ela NÃO deve ser considerada porta pública de produção.
const DEFAULT_DEVELOPMENT_API_PORT =
    "9000";


const DEFAULT_API_TIMEOUT_MS =
    60_000;


const MIN_API_TIMEOUT_MS =
    5_000;


const MAX_API_TIMEOUT_MS =
    300_000;


// ============================================================
// CONFIGURAÇÃO INJETADA EM RUNTIME
// ============================================================
//
// Permite que uma instalação do DUET forneça:
//
// window.__DUET_RUNTIME_CONFIG__ = {
//     apiBaseUrl: "https://api.duet.com",
//     apiTimeoutMs: 60000,
// };
//
// Isso permite utilizar o mesmo build do frontend em
// ambientes diferentes.
//
// Exemplo:
//
// CLOUD:
//     https://app.duet.com
//
// ON-PREMISE:
//     https://duet.cliente.local
//
// sem necessidade de recompilar o React.
// ============================================================

declare global {

    interface Window {

        __DUET_RUNTIME_CONFIG__?: {

            apiBaseUrl?:
                string;

            apiTimeoutMs?:
                number | string;
        };
    }
}


// ============================================================
// NORMALIZAÇÃO DE URL HTTP
// ============================================================

function normalizeHttpUrl(
    value: string
): string | undefined {

    try {

        // Também aceita caminhos relativos.
        //
        // Exemplo:
        //
        // /api
        //
        // será convertido para:
        //
        // https://servidor-atual/api
        const url =
            new URL(
                value,
                window.location.origin
            );


        if (
            url.protocol !== "http:" &&
            url.protocol !== "https:"
        ) {

            return undefined;
        }


        return url
            .toString()
            .replace(
                /\/$/,
                ""
            );

    } catch {

        return undefined;
    }
}


// ============================================================
// API BASE URL
// ============================================================

function resolveApiBaseUrl(): string {

    // ========================================================
    // 1. CONFIGURAÇÃO EM RUNTIME
    // ========================================================
    //
    // É a configuração preferencial para instalações reais.
    //
    // Permite reutilizar o mesmo build em Cloud e On-Premise.
    // ========================================================

    const runtimeUrl =
        window
            .__DUET_RUNTIME_CONFIG__
            ?.apiBaseUrl
            ?.trim();


    const normalizedRuntimeUrl =
        runtimeUrl
            ? normalizeHttpUrl(
                runtimeUrl
            )
            : undefined;


    if (normalizedRuntimeUrl) {

        return normalizedRuntimeUrl;
    }


    // ========================================================
    // 2. CONFIGURAÇÃO VITE
    // ========================================================
    //
    // Continua suportada para desenvolvimento, CI/CD e
    // ambientes cujo endereço seja definido durante o build.
    // ========================================================

    const viteConfiguredUrl =
        import.meta.env
            .VITE_DUET_API_URL
            ?.trim();


    const normalizedViteUrl =
        viteConfiguredUrl
            ? normalizeHttpUrl(
                viteConfiguredUrl
            )
            : undefined;


    if (normalizedViteUrl) {

        return normalizedViteUrl;
    }


    // ========================================================
    // 3. DESENVOLVIMENTO LOCAL
    // ========================================================
    //
    // Durante npm run dev:
    //
    // Frontend:
    //     http://localhost:5173
    //
    // Backend:
    //     http://localhost:9000
    //
    // A porta 9000 fica restrita ao ambiente de desenvolvimento.
    // ========================================================

    if (import.meta.env.DEV) {

        return (
            `${window.location.protocol}//` +
            `${window.location.hostname}:` +
            DEFAULT_DEVELOPMENT_API_PORT
        );
    }


    // ========================================================
    // 4. PRODUÇÃO - SAME ORIGIN
    // ========================================================
    //
    // Em produção o padrão passa a ser:
    //
    // https://duet.empresa.com/api
    //
    // O reverse proxy decide internamente onde está o FastAPI:
    //
    // /api
    //   ↓
    // FastAPI :9000
    //
    // Dessa maneira a porta interna nunca é exposta ao usuário.
    // ========================================================

    return normalizeHttpUrl(
        "/api"
    ) as string;
}


// ============================================================
// API TIMEOUT
// ============================================================

function resolveApiTimeout(): number {

    // Configuração dinâmica possui prioridade.
    const runtimeTimeout =
        Number(
            window
                .__DUET_RUNTIME_CONFIG__
                ?.apiTimeoutMs
        );


    if (
        Number.isFinite(
            runtimeTimeout
        ) &&
        runtimeTimeout > 0
    ) {

        return Math.min(
            MAX_API_TIMEOUT_MS,
            Math.max(
                MIN_API_TIMEOUT_MS,
                runtimeTimeout
            )
        );
    }


    // Depois utilizamos a configuração Vite.
    const viteTimeout =
        Number(
            import.meta.env
                .VITE_DUET_API_TIMEOUT_MS
        );


    if (
        !Number.isFinite(
            viteTimeout
        )
    ) {

        return DEFAULT_API_TIMEOUT_MS;
    }


    return Math.min(
        MAX_API_TIMEOUT_MS,
        Math.max(
            MIN_API_TIMEOUT_MS,
            viteTimeout
        )
    );
}


// ============================================================
// CONFIGURAÇÃO PÚBLICA DO FRONTEND
// ============================================================

export const runtimeConfig =
    Object.freeze({

        apiBaseUrl:
            resolveApiBaseUrl(),

        apiTimeoutMs:
            resolveApiTimeout(),
    });


// ============================================================
// WEBSOCKET BASE URL
// ============================================================
//
// Mantém exatamente a mesma origem pública da API.
//
// Exemplos:
//
// https://duet.com/api
//      ↓
// wss://duet.com/api
//
// http://localhost:9000
//      ↓
// ws://localhost:9000
// ============================================================

export function getWebSocketBaseUrl(): string {

    return runtimeConfig
        .apiBaseUrl
        .replace(
            /^http/,
            "ws"
        );
}
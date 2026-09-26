const DEFAULT_API_PORT = "9000";
const DEFAULT_API_TIMEOUT_MS = 60_000;
const MIN_API_TIMEOUT_MS = 5_000;
const MAX_API_TIMEOUT_MS = 300_000;

function normalizeHttpUrl(value: string): string | undefined {
    try {
        const url = new URL(value, window.location.origin);

        if (url.protocol !== "http:" && url.protocol !== "https:") {
            return undefined;
        }

        return url.toString().replace(/\/$/, "");
    } catch {
        return undefined;
    }
}

function resolveApiBaseUrl(): string {
    const configuredUrl = import.meta.env.VITE_DUET_API_URL?.trim();
    const normalizedConfiguredUrl = configuredUrl
        ? normalizeHttpUrl(configuredUrl)
        : undefined;

    if (normalizedConfiguredUrl) {
        return normalizedConfiguredUrl;
    }

    return `${window.location.protocol}//${window.location.hostname}:${DEFAULT_API_PORT}`;
}

function resolveApiTimeout(): number {
    const configuredTimeout = Number(import.meta.env.VITE_DUET_API_TIMEOUT_MS);

    if (!Number.isFinite(configuredTimeout)) {
        return DEFAULT_API_TIMEOUT_MS;
    }

    return Math.min(
        MAX_API_TIMEOUT_MS,
        Math.max(MIN_API_TIMEOUT_MS, configuredTimeout),
    );
}

export const runtimeConfig = Object.freeze({
    apiBaseUrl: resolveApiBaseUrl(),
    apiTimeoutMs: resolveApiTimeout(),
});

export function getWebSocketBaseUrl(): string {
    return runtimeConfig.apiBaseUrl.replace(/^http/, "ws");
}

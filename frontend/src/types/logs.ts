// ============================================================
// DUET CORE - LOGS - TYPES
// ============================================================
//
// Contratos TypeScript utilizados pela área de Logs.
//
// Responsabilidade:
// - representar um registro retornado por GET /logs.
//
// Este módulo NÃO:
// - executa chamadas HTTP;
// - possui estado React;
// - controla polling;
// - renderiza interface.
// ============================================================


// ============================================================
// LOG
// ============================================================

export interface SystemLog {
    timestamp: string;
    level: string;
    message: string;

    event?: string | null;
    service?: string | null;

    category?: string | null;
    component?: string | null;
    status?: string | null;

    actor_user_id?: number | null;
    actor_username?: string | null;

    action?: string | null;

    resource_type?: string | null;
    resource_id?: string | number | null;
    resource_name?: string | null;

    client_ip?: string | null;

    request_id?: string | null;

    http_method?: string | null;
    endpoint?: string | null;
    http_status?: number | null;
    duration_ms?: number | null;

    error_type?: string | null;
    error_message?: string | null;

    trace_id?: string | null;
    span_id?: string | null;
}
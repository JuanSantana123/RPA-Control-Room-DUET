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
}
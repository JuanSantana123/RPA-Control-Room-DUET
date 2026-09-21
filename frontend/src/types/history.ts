// ============================================================
// DUET CORE - HISTORY - TYPES
// ============================================================
//
// Contratos TypeScript utilizados pela área de histórico.
//
// Responsabilidade:
// - representar uma execução finalizada retornada por:
//   GET /executions/history
//
// Este módulo NÃO:
// - executa chamadas HTTP;
// - formata dados;
// - possui estado React;
// - renderiza interface.
// ============================================================


// ============================================================
// EXECUÇÃO DO HISTÓRICO
// ============================================================

export interface HistoryExecution {
    id: number;

    robot_name: string | null;

    // Nome completo da pasta, incluindo subpastas.
    folder_name: string | null;

    // Dados do usuário que iniciou a execução.
    user_id: number | null;
    username: string | null;
    user_name: string | null;

    agent_name: string | null;

    started_at: string | null;
    finished_at: string | null;

    status: string;

    error_message: string | null;
}
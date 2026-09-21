// ============================================================
// DUET CORE - DASHBOARD - TYPES
// ============================================================
//
// Contratos TypeScript utilizados exclusivamente pelo
// Dashboard do Control Room.
//
// Responsabilidade:
// - representar as estatísticas retornadas pelo Dashboard;
// - representar as execuções exibidas como ativas.
//
// Estes tipos NÃO:
// - executam chamadas HTTP;
// - formatam dados;
// - controlam estado da interface.
// ============================================================


// ============================================================
// ESTATÍSTICAS
// ============================================================
//
// Retorno utilizado pelo endpoint:
//
// GET /dashboard/stats
// ============================================================

export interface DashboardStats {
    total_agents: number;
    agents_online: number;
    total_robots: number;
}


// ============================================================
// EXECUÇÃO
// ============================================================
//
// Estrutura utilizada pelo Dashboard a partir de:
//
// GET /executions
// ============================================================

export interface DashboardExecution {
    id: number;
    robot_id: number;
    robot_name: string;
    filename: string;
    agent_id: string;
    agent_name: string;
    status: string;
    started_at: string | null;
    finished_at: string | null;
    error_message: string | null;
}
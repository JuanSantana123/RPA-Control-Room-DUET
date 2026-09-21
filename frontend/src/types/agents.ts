// ============================================================
// DUET CORE - AGENTS - TYPES
// ============================================================
//
// Contratos TypeScript utilizados pela área de Devices/Agents.
//
// Responsabilidade:
// - representar um Agent retornado pelo Control Room;
// - representar os dados locais utilizados no cadastro;
// - representar os ambientes operacionais suportados.
//
// Este módulo NÃO:
// - executa chamadas HTTP;
// - possui estado React;
// - renderiza componentes;
// - contém regras operacionais.
// ============================================================


// ============================================================
// AMBIENTE DO AGENT
// ============================================================
//
// Valores persistidos pelo backend.
//
// development:
//     Desenvolvimento / Homologação.
//
// production:
//     Produção.
// ============================================================

export type AgentEnvironment =
    | "development"
    | "production";


// ============================================================
// AGENT
// ============================================================
//
// Representa um Agent retornado pelo Control Room.
//
// Origem:
// GET /agents
// ============================================================

export interface Agent {
    agent_id: string;
    name: string;
    host: string;
    port: number;
    rpa_directory: string | null;
    status: string;

    // Ambiente operacional administrado pelo Control Room.
    environment: AgentEnvironment;

    // Status atual da sessão Windows.
    session_status: string;

    // Usuário atualmente conectado na sessão Windows.
    username: string | null;
}


// ============================================================
// NEW AGENT
// ============================================================
//
// Representa os dados informados pela interface durante
// o cadastro.
//
// O ambiente é escolhido pelo usuário antes da criação.
// ============================================================

export interface NewAgentForm {
    port: string;

    // Ambiente inicial da nova máquina.
    environment: AgentEnvironment;
}
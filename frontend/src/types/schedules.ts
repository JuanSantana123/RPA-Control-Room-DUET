// ============================================================
// DUET CORE - SCHEDULES - TYPES
// ============================================================
//
// Contratos TypeScript utilizados pela área de Agendamentos.
//
// Responsabilidade:
// - representar Robots disponíveis para agendamento;
// - representar Agents disponíveis para agendamento;
// - representar um Schedule retornado pelo Control Room.
//
// Este módulo NÃO:
// - executa chamadas HTTP;
// - contém estado React;
// - possui regras do Scheduler;
// - renderiza componentes.
//
// Os contratos foram extraídos diretamente de
// pages/Schedules.tsx sem alteração dos campos existentes.
// ============================================================


// ============================================================
// ROBOT OPTION
// ============================================================

// Representa um robô disponível para agendamento.
export interface RobotOption {
    id: number;
    name: string;
}


// ============================================================
// AGENT OPTION
// ============================================================

// Representa um Agent disponível para agendamento.
export interface AgentOption {
    agent_id: string;
    name: string;
    status: string;
}


// ============================================================
// SCHEDULE
// ============================================================

// Representa um agendamento retornado pela API.
export interface Schedule {
    id: number;

    robot_id: number;
    robot_name: string;

    agent_id: string | null;
    agent_name: string;

    tipo: string;

    data_inicio: string | null;
    horario: string;

    dias_semana: string | null;

    intervalo_ativo: boolean;
    intervalo_valor: number | null;
    intervalo_unidade: string | null;
    horario_fim: string | null;

    proxima_execucao: string | null;

    ativo: boolean;
}
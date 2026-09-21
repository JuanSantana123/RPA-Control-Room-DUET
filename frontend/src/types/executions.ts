// ============================================================
// DUET CORE - EXECUTIONS - TYPES
// ============================================================
//
// Contratos compartilhados do domínio de Execuções.
//
// Este módulo centraliza as estruturas utilizadas pela página
// de Execuções, hooks e componentes visuais.
//
// Responsabilidade:
// - representar uma execução retornada pelo Control Room.
//
// Este arquivo NÃO:
// - realiza chamadas HTTP;
// - contém estado React;
// - formata dados;
// - renderiza componentes.
//
// A interface abaixo preserva o contrato anteriormente
// declarado diretamente em pages/Executions.tsx.
// ============================================================


/**
 * Representa uma execução de Robot registrada pelo
 * Control Room.
 */
export interface Execution {

    // Identificação da execução.
    id: number;


    // ========================================================
    // ROBOT
    // ========================================================

    // Identificação permanente do Robot.
    robot_id: number;

    // Nome do Robot.
    robot_name: string;

    // Nome do arquivo/pacote executado.
    filename: string;


    // ========================================================
    // AGENT
    // ========================================================

    // Identificação técnica do Agent responsável.
    agent_id: string;

    // Nome apresentado para o Agent.
    agent_name: string;


    // ========================================================
    // USUÁRIO
    // ========================================================

    // Usuário que iniciou a execução.
    user_id: number | null;

    // Username/login do usuário.
    username: string | null;

    // Nome amigável do usuário.
    user_name: string | null;


    // ========================================================
    // LOCALIZAÇÃO DO ROBOT
    // ========================================================

    // Caminho completo da pasta onde o Robot está cadastrado.
    // null representa a pasta raiz.
    folder_name: string | null;


    // ========================================================
    // PROCESSO / STATUS
    // ========================================================

    // PID do processo no Agent, quando disponível.
    pid: number | null;

    // Status atual da execução.
    status: string;


    // ========================================================
    // DATAS
    // ========================================================

    // Momento em que a execução foi iniciada.
    started_at: string | null;

    // Momento em que a execução foi finalizada.
    finished_at: string | null;


    // ========================================================
    // ERRO
    // ========================================================

    // Mensagem registrada quando ocorre erro.
    error_message: string | null;
}
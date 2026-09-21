// ============================================================
// DUET CORE - AGENTS - LIST
// ============================================================
//
// Painel responsável pela apresentação da coleção de
// Devices/Agents cadastrados.
//
// Responsabilidade:
// - apresentar quantidade de Devices;
// - apresentar estado de carregamento;
// - apresentar estado vazio;
// - renderizar os AgentCards;
// - encaminhar ações de download e exclusão.
//
// Este componente NÃO:
// - carrega Agents;
// - executa chamadas HTTP;
// - modifica a coleção;
// - cadastra Devices;
// - controla mensagens globais de erro.
//
// A origem dos dados permanece em useAgentsData.ts.
// ============================================================

import {
    Monitor,
} from "lucide-react";

import AgentCard
    from "./AgentCard";

import type {
    Agent,
} from "../../types/agents";


// ============================================================
// PROPS
// ============================================================

interface AgentsListProps {
    agents: Agent[];
    loading: boolean;
    error: string;
        onEnvironmentChange:
        (
            agentId: string,
            environment:
                "development" |
                "production"
        ) => void | Promise<void>;

    onDownload:
        (
            agentId: string
        ) => void | Promise<void>;

    onDelete:
        (
            agentId: string,
            agentName: string
        ) => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function AgentsList({
    agents,
    loading,
    error,
    onEnvironmentChange,
    onDownload,
    onDelete,
}: AgentsListProps) {

    return (
        <section className="content-panel agents-list-panel">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="content-panel-header">

                <div>

                    <h2>
                        Devices cadastrados
                    </h2>

                    <p>
                        Devices disponíveis para execução das automações.
                    </p>

                </div>


                <div className="panel-header-meta">

                    <span className="panel-count">
                        {agents.length}
                    </span>

                    <span className="panel-count-label">
                        cadastrados
                    </span>

                </div>

            </div>


            {/* ==================================================
                CARREGAMENTO
                ================================================== */}

            {loading && (

                <div className="panel-loading">
                    Carregando Devices...
                </div>

            )}


            {/* ==================================================
                ESTADO VAZIO
                ================================================== */}

            {!loading &&
                !error &&
                agents.length === 0 && (

                    <div className="panel-empty-state">

                        <div className="panel-empty-icon">

                            <Monitor
                                size={26}
                                strokeWidth={1.6}
                            />

                        </div>


                        <h3>
                            Nenhum Device cadastrado
                        </h3>


                        <p>
                            Cadastre o primeiro Device para começar a executar robôs.
                        </p>

                    </div>

                )}


            {/* ==================================================
                GRID
                ================================================== */}

            {!loading &&
                !error &&
                agents.length > 0 && (

                    <div className="agents-grid">

                        {agents.map(
                            (agent) => (

                                <AgentCard
                                    key={
                                        agent.agent_id
                                    }
                                    agent={
                                        agent
                                    }

                                    onEnvironmentChange={
                                        onEnvironmentChange
                                    }
                                    onDownload={
                                        onDownload
                                    }
                                    onDelete={
                                        onDelete
                                    }
                                />

                            )
                        )}

                    </div>

                )}

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default AgentsList;
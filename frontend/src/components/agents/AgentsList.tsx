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

import { CardGridSkeleton }
    from "../ui/Skeletons";

import type {
    Agent,
} from "../../types/agents";
import EmptyState from "../ui/EmptyState";


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


    onDisplayChange:
        (
            agentId: string,
            width: number,
            height: number,
            scale: number
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
    onDisplayChange,
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
                        Dispositivos cadastrados
                    </h2>

                    <p>
                        Dispositivos disponíveis para execução das automações.
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
                <CardGridSkeleton count={3} />

            )}


            {/* ==================================================
                ESTADO VAZIO
                ================================================== */}

            {!loading &&
                !error &&
                agents.length === 0 && (

                    <EmptyState
                        icon={<Monitor />}
                        title="Nenhum dispositivo cadastrado"
                        description="Cadastre o primeiro dispositivo para começar a executar automações com segurança."
                    />

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
                                    onDisplayChange={
                                        onDisplayChange
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

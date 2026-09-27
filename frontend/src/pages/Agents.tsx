// ============================================================

import { useMemo, useState } from "react";
import { MonitorCheck, RefreshCw, TriangleAlert, Wrench } from "lucide-react";
// DUET CORE - AGENTS PAGE
// ============================================================
//
// Página principal da área de Devices/Agents.
//
// Responsabilidade:
// - compor a interface da feature;
// - conectar os dados aos componentes visuais;
// - encaminhar as operações fornecidas pelo hook;
// - apresentar mensagens globais de erro.
//
// A lógica operacional foi distribuída para:
//
// useAgentsData
// - carregamento dos Agents;
// - cadastro;
// - exclusão;
// - download;
// - estado do formulário;
// - loading e erros.
//
// Componentes:
// - AgentsHeader;
// - AgentCreatePanel;
// - AgentsList;
// - AgentCard.
//
// Esta página NÃO deve concentrar:
// - chamadas HTTP;
// - implementação de cards;
// - implementação do formulário;
// - regras de cadastro;
// - manipulação do download;
// - regras de exclusão.
//
// Dessa forma, Agents.tsx permanece como camada de
// composição/orquestração da feature.
// ============================================================

import AgentsHeader
    from "../components/agents/AgentsHeader";

import AgentCreatePanel
    from "../components/agents/AgentCreatePanel";

import AgentsList
    from "../components/agents/AgentsList";

import {
    useAgentsData,
} from "../hooks/agents/useAgentsData";
import FeedbackBanner from "../components/ui/FeedbackBanner";
import SearchField from "../components/ui/SearchField";
import PremiumSelect from "../components/ui/PremiumSelect";
import { IconButton } from "../components/ui/Button";
import { useAuth } from "../context/useAuth";


// ============================================================
// PÁGINA DE AGENTS
// ============================================================

function Agents() {

    const { can } = useAuth();
    const canCreateAgents = can("Agents:create");
    const canEditAgents = can("Agents:edit");
    const canDeleteAgents = can("Agents:delete");
    const canBootstrapAgents = can("Agents:bootstrap");

    // ========================================================
    // DADOS / OPERAÇÕES
    // ========================================================
    //
    // Toda a responsabilidade operacional da feature fica
    // encapsulada no hook.
    //
    // A página apenas distribui estado e callbacks para os
    // componentes responsáveis pela apresentação.
    // ========================================================

    const {
        agents,
        loading,
        error,
        errorKind,
        clearError,

        newAgent,
        setNewAgent,

        creatingAgent,
        updatingAvailability,
        refreshing,
        lastUpdated,

        cadastrarAgent,
        alterarAmbienteAgent,
        alterarDisponibilidadeAgent,
        alterarDisplayAgent,
        excluirAgent,
        baixarAgent,
        carregarAgents,
    } = useAgentsData();

    const [search, setSearch] = useState("");
    const [availabilityFilter, setAvailabilityFilter] = useState("all");

    const filteredAgents = useMemo(() => {
        const normalizedSearch = search.trim().toLocaleLowerCase("pt-BR");
        return agents.filter((agent) => {
            const matchesSearch = !normalizedSearch || [agent.name, agent.agent_id, agent.host]
                .some((value) => value?.toLocaleLowerCase("pt-BR").includes(normalizedSearch));
            const matchesAvailability = availabilityFilter === "all"
                || (availabilityFilter === "available" && agent.accepting_work && agent.health_state === "healthy")
                || (availabilityFilter === "maintenance" && !agent.accepting_work)
                || (availabilityFilter === "attention" && agent.health_state !== "healthy");
            return matchesSearch && matchesAvailability;
        });
    }, [agents, availabilityFilter, search]);

    const availableCount = agents.filter(
        (agent) => agent.accepting_work && agent.health_state === "healthy"
    ).length;
    const maintenanceCount = agents.filter((agent) => !agent.accepting_work).length;
    const attentionCount = agents.filter((agent) => agent.health_state !== "healthy").length;
    const syncStatusLabel = lastUpdated
        ? `Atualizado às ${lastUpdated.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit", second: "2-digit" })}`
        : "Aguardando primeira leitura";


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="page-container agents-page">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <AgentsHeader />


            {/* ==================================================
                MENSAGEM DE ERRO
                ================================================== */}

            {error && (
                <FeedbackBanner
                    tone="error"
                    title="Não foi possível concluir a operação"
                    message={error}
                    hint={errorKind === "create"
                        ? "O formulário foi preservado. A mensagem permanecerá visível até você fechar ou repetir o cadastro."
                        : agents.length > 0
                            ? "O último estado válido permanece visível enquanto você tenta novamente."
                            : "Verifique a conexão com o Control Room e tente novamente."}
                    action={errorKind === "create" ? {
                        label: "Repetir cadastro",
                        onClick: cadastrarAgent,
                        busy: creatingAgent,
                    } : errorKind === "catalog" ? {
                        label: "Atualizar catálogo",
                        onClick: carregarAgents,
                        busy: refreshing,
                    } : undefined}
                    onDismiss={clearError}
                />
            )}


            {/* ==================================================
                CADASTRO
                ================================================== */}

            {canCreateAgents && <AgentCreatePanel
                newAgent={
                    newAgent
                }
                setNewAgent={
                    setNewAgent
                }
                creatingAgent={
                    creatingAgent
                }
                onCreate={
                    cadastrarAgent
                }
            />}

            <section className="agents-operations" aria-labelledby="agents-operations-title">
                <div className="agents-operations__summary">
                    <div>
                        <span>Capacidade disponível</span>
                        <strong>{availableCount}</strong>
                        <small>online e aceitando trabalho</small>
                    </div>
                    <div>
                        <span>Em manutenção</span>
                        <strong>{maintenanceCount}</strong>
                        <small>reservas pausadas conscientemente</small>
                    </div>
                    <div>
                        <span>Requer atenção</span>
                        <strong>{attentionCount}</strong>
                        <small>heartbeat atrasado, ausente ou offline</small>
                    </div>
                </div>
                <div className="agents-operations__toolbar">
                    <div>
                        <h2 id="agents-operations-title">Visão operacional dos Devices</h2>
                        <p>Encontre rapidamente a máquina adequada e controle novas reservas.</p>
                    </div>
                    <SearchField
                        label="Pesquisar Devices"
                        value={search}
                        placeholder="Pesquisar por nome, ID ou host…"
                        onValueChange={setSearch}
                    />
                    <div className="agents-availability-filter">
                        <label htmlFor="agents-availability-filter">Disponibilidade</label>
                        <PremiumSelect
                            id="agents-availability-filter"
                            value={availabilityFilter}
                            onChange={(event) => setAvailabilityFilter(event.target.value)}
                        >
                            <option value="all">Todos os Devices</option>
                            <option value="available">Disponíveis</option>
                            <option value="maintenance">Em manutenção</option>
                            <option value="attention">Requer atenção</option>
                        </PremiumSelect>
                    </div>
                    <div className="agents-operations__legend" aria-label="Legenda operacional">
                        <span><MonitorCheck size={14} /> Disponível</span>
                        <span><Wrench size={14} /> Manutenção</span>
                        <span><TriangleAlert size={14} /> Atenção</span>
                        <span className="agents-refresh-status" aria-live="polite">
                            {refreshing ? "Atualizando…" : syncStatusLabel}
                        </span>
                        <IconButton
                            size="sm"
                            label="Atualizar Devices agora"
                            tooltip="Atualizar saúde dos Devices"
                            busy={refreshing}
                            icon={<RefreshCw size={15} aria-hidden="true" />}
                            onClick={carregarAgents}
                        />
                    </div>
                </div>
            </section>


            {/* ==================================================
                LISTAGEM
                ================================================== */}

            <AgentsList
                agents={
                    filteredAgents
                }
                loading={
                    loading
                }
                error={
                    error
                }
                hasFilters={Boolean(search.trim()) || availabilityFilter !== "all"}
                canCreate={canCreateAgents}
                canEdit={canEditAgents}
                canDelete={canDeleteAgents}
                canBootstrap={canBootstrapAgents}
                onEnvironmentChange={
                    alterarAmbienteAgent
                }
                onDisplayChange={
                    alterarDisplayAgent
                }
                updatingAvailability={updatingAvailability}
                onAvailabilityChange={alterarDisponibilidadeAgent}
                onDownload={
                    baixarAgent
                }


                onDelete={
                    excluirAgent
                }
            />

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default Agents;

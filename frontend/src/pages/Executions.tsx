// ============================================================
// DUET CORE - EXECUTIONS
// ============================================================
//
// Página responsável pela composição da área de Execuções.
//
// A implementação foi distribuída por responsabilidade:
//
// - useExecutionsData:
//   carregamento, polling e ações operacionais.
//
// - useExecutionFilters:
//   estado e processamento dos filtros.
//
// - components/executions:
//   apresentação visual da página.
//
// Executions.tsx permanece como camada de orquestração,
// conectando dados, filtros, ações e componentes.
//
// A página NÃO deve concentrar:
// - chamadas HTTP;
// - polling;
// - formatação;
// - implementação interna da tabela;
// - implementação interna do modal.
// ============================================================

import {
    useState,
} from "react";

import type {
    Execution,
} from "../types/executions";

import {
    useExecutionsData,
} from "../hooks/executions/useExecutionsData";

import {
    useExecutionFilters,
} from "../hooks/executions/useExecutionFilters";

import ExecutionsHeader from "../components/executions/ExecutionsHeader";
import ExecutionsSummary from "../components/executions/ExecutionsSummary";
import ExecutionsFilters from "../components/executions/ExecutionsFilters";
import ExecutionsTable from "../components/executions/ExecutionsTable";
import ExecutionDetailsModal from "../components/executions/ExecutionDetailsModal";
import FeedbackBanner from "../components/ui/FeedbackBanner";
import { calcularTempoDeFila } from "../utils/executionFormatters";



function Executions() {

    // ========================================================
    // DADOS E AÇÕES OPERACIONAIS
    // ========================================================
    //
    // Toda comunicação com o backend e o polling automático
    // permanecem encapsulados em useExecutionsData.
    // ========================================================

    const {
        executions,
        loading,
        refreshing,
        error,
        queueWarningSeconds,

        parandoExecucao,
        cancelandoExecucao,
        updatingPriority,

        carregarExecucoes,
        pararExecucao,
        cancelarExecucao,
        alterarPrioridade,
    } = useExecutionsData();


    // ========================================================
    // FILTROS
    // ========================================================
    //
    // O hook recebe a coleção completa e devolve tanto os
    // estados dos filtros quanto a coleção visível.
    // ========================================================

    const {
        filtroRobo,
        setFiltroRobo,

        filtroAgent,
        setFiltroAgent,

        robos,
        agents,

        execucoesFiltradas,

        limparFiltros,
    } = useExecutionFilters(
        executions
    );


    // ========================================================
    // EXECUÇÃO SELECIONADA
    // ========================================================
    //
    // Este estado continua na página porque representa apenas
    // navegação visual: qual execução está aberta no modal.
    // ========================================================

    const [
        execucaoSelecionadaId,
        setExecucaoSelecionadaId,
    ] = useState<number | null>(
        null
    );

    const execucaoSelecionada = executions.find(
        (execution) => execution.id === execucaoSelecionadaId
    ) ?? null;


    // ========================================================
    // RESUMO
    // ========================================================
    //
    // Mantém a regra original:
    // "Em execução" considera a coleção completa, enquanto
    // "Execuções visíveis" considera o resultado dos filtros.
    // ========================================================

    const runningExecutionsCount =
        executions.filter(
            (execution) =>
                execution.status ===
                "running"
        ).length;

    const queuedExecutions = executions.filter(
        (execution) => execution.status === "queued"
    );

    const delayedExecutionsCount = queuedExecutions.filter(
        (execution) => calcularTempoDeFila(execution.queued_at).seconds > queueWarningSeconds
    ).length;


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <section className="executions-page">

            {/* =================================================
                CABEÇALHO
            ================================================= */}

            <ExecutionsHeader
                refreshing={refreshing}
                onRefresh={
                    carregarExecucoes
                }
            />


            {/* =================================================
                RESUMO OPERACIONAL
            ================================================= */}

            <ExecutionsSummary
                visibleExecutionsCount={
                    execucoesFiltradas.length
                }
                agentsCount={
                    agents.length
                }
                runningExecutionsCount={
                    runningExecutionsCount
                }
                queuedExecutionsCount={queuedExecutions.length}
                delayedExecutionsCount={delayedExecutionsCount}
            />


            {/* =================================================
                FILTROS
            ================================================= */}

            <ExecutionsFilters
                filtroRobo={
                    filtroRobo
                }
                filtroAgent={
                    filtroAgent
                }
                robos={
                    robos
                }
                agents={
                    agents
                }
                onFiltroRoboChange={
                    setFiltroRobo
                }
                onFiltroAgentChange={
                    setFiltroAgent
                }
                onClearFilters={
                    limparFiltros
                }
            />


            {/* =================================================
                ERRO DE CARREGAMENTO
            =================================================
                
                Esta mensagem permanece na página porque é uma
                composição visual entre o estado do hook e a
                interface geral.
            ================================================= */}

            {error && (
                <FeedbackBanner
                    tone="error"
                    title="Não foi possível atualizar as execuções"
                    message={error}
                    hint="A lista existente foi preservada e pode estar desatualizada."
                    action={{
                        label: "Atualizar agora",
                        onClick: carregarExecucoes,
                        busy: refreshing,
                    }}
                />
            )}


            {/* =================================================
                TABELA
            ================================================= */}

            <ExecutionsTable
                executions={
                    execucoesFiltradas
                }
                loading={
                    loading
                }
                parandoExecucao={
                    parandoExecucao
                }
                cancelandoExecucao={
                    cancelandoExecucao
                }
                queueWarningSeconds={queueWarningSeconds}
                onViewDetails={
                    (execution: Execution) => setExecucaoSelecionadaId(execution.id)
                }
                onStopExecution={
                    pararExecucao
                }
                onCancelExecution={
                    cancelarExecucao
                }
            />


            {/* =================================================
                DETALHES
            ================================================= */}

            {execucaoSelecionada && (

                <ExecutionDetailsModal
                    execution={
                        execucaoSelecionada
                    }
                    onClose={() =>
                        setExecucaoSelecionadaId(
                            null
                        )
                    }
                    stopping={parandoExecucao === execucaoSelecionada.id}
                    cancelling={cancelandoExecucao === execucaoSelecionada.id}
                    updatingPriority={updatingPriority === execucaoSelecionada.id}
                    queueWarningSeconds={queueWarningSeconds}
                    onStopExecution={pararExecucao}
                    onCancelExecution={cancelarExecucao}
                    onUpdatePriority={alterarPrioridade}
                />
            )}

        </section>
    );
}


export default Executions;

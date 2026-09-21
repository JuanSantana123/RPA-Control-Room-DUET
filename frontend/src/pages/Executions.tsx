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

import {
    AlertCircle,
} from "lucide-react";

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
        error,

        parandoExecucao,
        cancelandoExecucao,

        carregarExecucoes,
        pararExecucao,
        cancelarExecucao,
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
        execucaoSelecionada,
        setExecucaoSelecionada,
    ] = useState<Execution | null>(
        null
    );


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


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <section className="executions-page">

            {/* =================================================
                CABEÇALHO
            ================================================= */}

            <ExecutionsHeader
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

                <div className="execution-error-alert">

                    <AlertCircle size={17} />

                    {error}

                </div>
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
                onViewDetails={
                    setExecucaoSelecionada
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
                        setExecucaoSelecionada(
                            null
                        )
                    }
                />
            )}

        </section>
    );
}


export default Executions;
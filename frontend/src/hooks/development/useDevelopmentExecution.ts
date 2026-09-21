// ============================================================
// USE DEVELOPMENT EXECUTION
// ============================================================
//
// Responsabilidade:
//     Centraliza o fluxo de execução de um AutomationProject
//     diretamente a partir da área de Desenvolvimento.
//
// O hook controla:
//     - projeto selecionado para execução;
//     - Agents disponíveis;
//     - Agent selecionado;
//     - carregamento dos Agents;
//     - execução atualmente em andamento;
//     - erro exclusivo do modal;
//     - mensagem de sucesso/fila exibida na página;
//     - abertura e fechamento do modal;
//     - disparo da execução.
//
// Fluxo:
//     1. Usuário solicita executar um projeto.
//     2. O hook consulta os Agents disponíveis.
//     3. Se existir somente um Agent realmente pronto,
//        ele é pré-selecionado.
//     4. Usuário confirma a execução.
//     5. O backend monta o snapshot do workspace.
//     6. O Control Room envia a execução ao Agent.
//     7. O hook informa se a execução iniciou ou entrou na fila.
//
// Arquitetura:
//     Este hook concentra estado e orquestração do fluxo
//     de execução da área Development.
//
// Este arquivo NÃO deve:
//     - renderizar componentes;
//     - navegar para o Studio;
//     - controlar Kanban;
//     - alterar projetos;
//     - controlar Release;
//     - controlar Lixeira.
//
// O ExecutionModal continua sendo exclusivamente visual.
// ============================================================

import {
    useState,
} from "react";


import api
    from "../../services/api";


import {
    getApiErrorMessage,
} from "../../utils/apiErrors";


import type {
    DevelopmentProject,
    ExecutionAgent,
} from "../../types/development";


// ============================================================
// PARÂMETROS
// ============================================================

interface UseDevelopmentExecutionParams {

    // Permissão efetiva calculada pelo Development.tsx.
    //
    // A regra atual exige:
    //
    // Development:edit
    // +
    // Executions:execute
    canExecuteDevelopment:
        boolean;
}


// ============================================================
// RETORNO
// ============================================================

interface UseDevelopmentExecutionResult {

    // Projeto atualmente selecionado para execução.
    projectToExecute:
        DevelopmentProject | null;


    // Agents retornados pelo backend.
    executionAgents:
        ExecutionAgent[];


    // Agent atualmente escolhido no modal.
    selectedExecutionAgentId:
        string;


    // Consulta dos Agents em andamento.
    loadingExecutionAgents:
        boolean;


    // ID do projeto cujo POST de execução está em andamento.
    executingProjectId:
        number | null;


    // Erro exclusivo do modal.
    executionError:
        string;


    // Confirmação exibida na página depois que a execução
    // é aceita pelo Control Room ou adicionada à fila.
    executionMessage:
        string;


    // Abre o fluxo de execução e carrega os Agents.
    openExecutionModal:
        (
            project: DevelopmentProject
        ) => Promise<void>;


    // Fecha o modal quando nenhuma execução está sendo enviada.
    closeExecutionModal:
        () => void;


    // Altera o Agent selecionado e limpa erros anteriores.
    changeExecutionAgent:
        (
            agentId: string
        ) => void;


    // Envia a execução para o Control Room.
    executeDevelopmentProject:
        () => Promise<void>;
}


// ============================================================
// HOOK
// ============================================================

function useDevelopmentExecution({
    canExecuteDevelopment,
}: UseDevelopmentExecutionParams): UseDevelopmentExecutionResult {

    // ========================================================
    // ESTADOS
    // ========================================================

    // Projeto para o qual o seletor de Agent está aberto.
    const [
        projectToExecute,
        setProjectToExecute,
    ] =
        useState<DevelopmentProject | null>(
            null
        );


    // Agents disponíveis para execução.
    const [
        executionAgents,
        setExecutionAgents,
    ] =
        useState<ExecutionAgent[]>([]);


    // Agent atualmente escolhido.
    const [
        selectedExecutionAgentId,
        setSelectedExecutionAgentId,
    ] =
        useState("");


    // Loading da consulta de Agents.
    const [
        loadingExecutionAgents,
        setLoadingExecutionAgents,
    ] =
        useState(false);


    // Projeto cujo POST de execução está em andamento.
    const [
        executingProjectId,
        setExecutingProjectId,
    ] =
        useState<number | null>(
            null
        );


    // Erro mostrado exclusivamente dentro do modal.
    const [
        executionError,
        setExecutionError,
    ] =
        useState("");


    // Mensagem apresentada na página após a execução
    // ser aceita ou colocada na fila.
    const [
        executionMessage,
        setExecutionMessage,
    ] =
        useState("");


    // ========================================================
    // ABRIR MODAL
    // ========================================================

    const openExecutionModal = async (
        project: DevelopmentProject
    ) => {

        if (!canExecuteDevelopment) {
            return;
        }


        // Abre imediatamente o modal para o projeto selecionado.
        setProjectToExecute(
            project
        );


        // Limpa dados de uma abertura anterior.
        setExecutionAgents([]);
        setSelectedExecutionAgentId("");
        setExecutionError("");
        setExecutionMessage("");


        try {

            setLoadingExecutionAgents(
                true
            );


            // Consulta somente Agents elegíveis ao fluxo
            // de execução de automações.
            const response =
                await api.get(
                    "/agents/execution/available-agents"
                );


            const agents:
                ExecutionAgent[] =
                    response.data?.agents || [];


            setExecutionAgents(
                agents
            );


            // ====================================================
            // PRÉ-SELEÇÃO SEGURA
            // ====================================================
            //
            // Quando existe exatamente um Agent online e com
            // sessão pronta, ele é automaticamente selecionado.
            //
            // Havendo múltiplas máquinas possíveis, nenhuma
            // escolha é feita silenciosamente.
            // ====================================================

            const readyAgents =
                agents.filter(
                    (agent) =>
                        agent.status === "online" &&
                        agent.session_status === "ready"
                );


            if (
                readyAgents.length === 1
            ) {

                setSelectedExecutionAgentId(
                    readyAgents[0].agent_id
                );
            }

        } catch (err: any) {

            console.error(
                "Erro ao carregar Agents para execução:",
                err
            );


            setExecutionError(
                getApiErrorMessage(
                    err,
                    "Não foi possível carregar os Agents disponíveis."
                )
            );

        } finally {

            setLoadingExecutionAgents(
                false
            );
        }
    };


    // ========================================================
    // FECHAR MODAL
    // ========================================================

    const closeExecutionModal = () => {

        // Não permite fechar enquanto o POST de execução
        // estiver sendo processado.
        if (
            executingProjectId !== null
        ) {
            return;
        }


        setProjectToExecute(
            null
        );


        setExecutionAgents([]);
        setSelectedExecutionAgentId("");
        setExecutionError("");
    };


    // ========================================================
    // ALTERAR AGENT
    // ========================================================

    const changeExecutionAgent = (
        agentId: string
    ) => {

        setSelectedExecutionAgentId(
            agentId
        );


        // Mantém o comportamento atual do Development.tsx:
        // trocar o Agent limpa eventual erro anterior.
        setExecutionError(
            ""
        );
    };


    // ========================================================
    // EXECUTAR PROJETO
    // ========================================================

    const executeDevelopmentProject =
        async () => {

            if (
                !canExecuteDevelopment ||
                !projectToExecute ||
                !selectedExecutionAgentId ||
                executingProjectId !== null
            ) {
                return;
            }


            try {

                setExecutingProjectId(
                    projectToExecute.id
                );


                setExecutionError("");
                setExecutionMessage("");


                const response =
                    await api.post(
                        `/development/projects/${projectToExecute.id}/execution/run`,
                        {
                            agent_id:
                                selectedExecutionAgentId,
                        }
                    );


                const responseStatus =
                    response.data?.status;


                // ====================================================
                // VALIDAÇÃO DO RESULTADO
                // ====================================================
                //
                // O fluxo atual pode responder HTTP 200 e ainda assim
                // indicar status="error".
                //
                // Portanto a validação não depende somente do status
                // HTTP retornado pelo Axios.
                // ====================================================

                if (
                    responseStatus !== "success" &&
                    responseStatus !== "queued"
                ) {

                    throw new Error(
                        response.data?.message ||
                        "O Control Room não conseguiu iniciar a execução."
                    );
                }


                const projectName =
                    projectToExecute.name;


                const agentId =
                    response.data?.agent_id ||
                    selectedExecutionAgentId;


                const pid =
                    response.data
                        ?.execution
                        ?.pid;


                // ====================================================
                // MENSAGEM PARA O USUÁRIO
                // ====================================================

                if (
                    responseStatus === "queued"
                ) {

                    setExecutionMessage(
                        `Projeto "${projectName}" adicionado à fila do Agent ${agentId}.`
                    );

                } else {

                    setExecutionMessage(
                        `Projeto "${projectName}" iniciado no Agent ${agentId}` +
                        (
                            pid
                                ? ` (PID ${pid}).`
                                : "."
                        )
                    );
                }


                // ====================================================
                // FECHAR MODAL APÓS SUCESSO
                // ====================================================

                setProjectToExecute(
                    null
                );


                setExecutionAgents([]);
                setSelectedExecutionAgentId("");
                setExecutionError("");

            } catch (err: any) {

                console.error(
                    "Erro ao executar projeto de Desenvolvimento:",
                    err
                );


                setExecutionError(
                    getApiErrorMessage(
                        err,
                        "Não foi possível executar o projeto."
                    )
                );

            } finally {

                setExecutingProjectId(
                    null
                );
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO DO HOOK
    // ========================================================

    return {
        projectToExecute,
        executionAgents,
        selectedExecutionAgentId,
        loadingExecutionAgents,
        executingProjectId,
        executionError,
        executionMessage,

        openExecutionModal,
        closeExecutionModal,
        changeExecutionAgent,
        executeDevelopmentProject,
    };
}


export default useDevelopmentExecution;
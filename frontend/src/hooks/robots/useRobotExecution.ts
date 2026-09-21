// ============================================================
// DUET CORE - ROBOTS - EXECUTION HOOK
// ============================================================
//
// Responsabilidade:
// - carregar os Agents disponíveis para execução manual;
// - controlar qual Agent está selecionado;
// - executar um Robot no Agent escolhido;
// - controlar qual Robot está sendo enviado para execução.
//
// Este hook NÃO:
// - carrega Robots;
// - gerencia pastas;
// - consulta Libraries;
// - renderiza elementos visuais.
//
// Integrações:
// - GET  /agents/execution/available-agents
// - POST /agents/{agent_id}/execution/run
//
// Segurança:
// - o frontend envia somente robot_id;
// - user_id é identificado pelo Control Room;
// - agent_token nunca passa pelo frontend.
//
// Este módulo preserva a lógica anteriormente existente
// diretamente em Robots.tsx.
// ============================================================

import {
    useEffect,
    useState,
} from "react";

import api from "../../services/api";

import type {
    ExecutionAgent,
    Robot,
} from "../../types/robots";


export function useRobotExecution() {

    // ========================================================
    // ESTADOS
    // ========================================================

    const [
        executionAgents,
        setExecutionAgents,
    ] = useState<ExecutionAgent[]>([]);


    const [
        selectedExecutionAgent,
        setSelectedExecutionAgent,
    ] = useState<string>("");


    const [
        executingRobotId,
        setExecutingRobotId,
    ] = useState<number | null>(
        null
    );


    // ========================================================
    // CARREGAR AGENTS DISPONÍVEIS
    // ========================================================
    //
    // Este endpoint exige somente a permissão necessária
    // para execução. O usuário não precisa possuir permissão
    // administrativa de Agents.
    // ========================================================

    useEffect(() => {

        api.get(
            "/agents/execution/available-agents"
        )
            .then((response) => {

                // Mantém exatamente o fallback existente.
                setExecutionAgents(
                    response.data.agents || []
                );


                // Se houver somente um Agent disponível,
                // ele é selecionado automaticamente.
                if (
                    response.data.agents &&
                    response.data.agents.length === 1
                ) {

                    setSelectedExecutionAgent(
                        response.data
                            .agents[0]
                            .agent_id
                    );
                }
            })
            .catch((err) => {

                console.error(
                    "Erro ao carregar Agents disponíveis para execução:",
                    err
                );
            });

    }, []);


    // ========================================================
    // EXECUTAR ROBOT
    // ========================================================

    const executarRobo = async (
        robot: Robot
    ) => {

        // Mantém os logs existentes no fluxo original.
        console.log(
            "ROBÔ SELECIONADO PARA EXECUÇÃO:",
            robot
        );

        console.log(
            "ID ENVIADO PARA EXECUÇÃO:",
            robot.id
        );


        // Nenhuma execução é enviada sem Agent selecionado.
        if (!selectedExecutionAgent) {

            alert(
                "Selecione um Agent para executar o robô."
            );

            return;
        }


        // Desabilita somente o Robot que está sendo enviado.
        setExecutingRobotId(
            robot.id
        );


        try {

            const response =
                await api.post(
                    `/agents/${selectedExecutionAgent}/execution/run`,
                    {
                        robot_id:
                            robot.id,
                    }
                );


            console.log(
                "Resposta da execução:",
                response.data
            );


            alert(
                response.data.message ||
                "Robô enviado para execução."
            );

        } catch (err: any) {

            console.error(
                "Erro ao executar robô:",
                err
            );


            const mensagem =
                err.response?.data?.message ||
                err.response?.data?.detail ||
                "Erro ao executar o robô.";


            alert(mensagem);

        } finally {

            setExecutingRobotId(null);
        }
    };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        executionAgents,

        selectedExecutionAgent,
        setSelectedExecutionAgent,

        executingRobotId,

        executarRobo,
    };
}
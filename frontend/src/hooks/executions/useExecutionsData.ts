// ============================================================
// DUET CORE - EXECUTIONS - DATA HOOK
// ============================================================
//
// Responsabilidade:
// - carregar as execuções registradas pelo Control Room;
// - manter atualização automática a cada 5 segundos;
// - enviar comando de parada para uma execução em andamento;
// - cancelar uma execução que ainda está na fila;
// - controlar estados de loading e erro dessas operações.
//
// Integrações:
// - GET  /executions
// - POST /agents/{agent_id}/execution/stop
// - POST /executions/{execution_id}/cancel
//
// Este hook NÃO:
// - controla filtros;
// - seleciona execução para o modal;
// - formata datas ou duração;
// - renderiza componentes.
//
// A lógica foi extraída de pages/Executions.tsx sem alterar
// o comportamento funcional existente.
// ============================================================

import {
    useEffect,
    useState,
} from "react";

import api from "../../services/api";

import type {
    Execution,
} from "../../types/executions";


export function useExecutionsData() {

    // ========================================================
    // ESTADOS PRINCIPAIS
    // ========================================================

    const [
        executions,
        setExecutions,
    ] = useState<Execution[]>([]);


    const [
        loading,
        setLoading,
    ] = useState(true);


    const [
        error,
        setError,
    ] = useState("");


    // ID da execução que está recebendo comando de parada.
    const [
        parandoExecucao,
        setParandoExecucao,
    ] = useState<number | null>(
        null
    );


    // ID da execução que está sendo cancelada da fila.
    const [
        cancelandoExecucao,
        setCancelandoExecucao,
    ] = useState<number | null>(
        null
    );


    // ========================================================
    // CARREGAR EXECUÇÕES
    // ========================================================

    const carregarExecucoes =
        async () => {

            try {

                const response =
                    await api.get(
                        "/executions"
                    );


                // Mantém exatamente o fallback existente.
                setExecutions(
                    response.data.executions ??
                    []
                );


                setError("");

            } catch (err) {

                console.error(
                    "Erro ao carregar execuções:",
                    err
                );


                setError(
                    "Não foi possível carregar as execuções."
                );

            } finally {

                setLoading(false);
            }
        };


    // ========================================================
    // POLLING
    // ========================================================
    //
    // Executa imediatamente ao abrir a página e depois
    // atualiza os dados automaticamente a cada 5 segundos.
    //
    // O intervalo é destruído quando o componente consumidor
    // deixa de existir.
    // ========================================================

    useEffect(() => {

        carregarExecucoes();


        const intervalo =
            window.setInterval(
                carregarExecucoes,
                5000
            );


        return () => {

            window.clearInterval(
                intervalo
            );
        };

    }, []);


    // ========================================================
    // PARAR EXECUÇÃO
    // ========================================================

    const pararExecucao =
        async (
            executionId: number,
            agentId: string
        ) => {

            const confirmar =
                window.confirm(
                    `Deseja realmente parar a execução #${executionId}?`
                );


            if (!confirmar) {
                return;
            }


            try {

                setParandoExecucao(
                    executionId
                );


                // O endpoint de parada identifica o Agent pela URL
                // e recebe o ID da execução através de query parameter.
                //
                // Resultado da requisição:
                //
                // POST /agents/{agent_id}/execution/stop?execution_id=123
                //
                // O segundo parâmetro é o body da requisição.
                // Como esse endpoint não precisa de body, enviamos null.
                //
                // O terceiro parâmetro contém a configuração do Axios,
                // onde "params" é convertido automaticamente em query string.
                const response =
                    await api.post(
                        `/agents/${agentId}/execution/stop`,
                        null,
                        {
                            params: {
                                execution_id: executionId,
                            },
                        }
                    );


                const data =
                    response.data;


                if (
                    response.status < 200 ||
                    response.status >= 300 ||
                    data.status !== "success"
                ) {

                    window.alert(
                        data.message ||
                        data.error ||
                        "Não foi possível parar a execução."
                    );


                    return;
                }


                await carregarExecucoes();

            } catch (err) {

                console.error(
                    "Erro ao enviar comando de stop:",
                    err
                );


                window.alert(
                    "Não foi possível comunicar com o Control Room."
                );

            } finally {

                setParandoExecucao(
                    null
                );
            }
        };


    // ========================================================
    // CANCELAR EXECUÇÃO DA FILA
    // ========================================================

    const cancelarExecucao =
        async (
            executionId: number
        ) => {

            const confirmar =
                window.confirm(
                    `Deseja realmente cancelar a execução #${executionId} da fila?`
                );


            if (!confirmar) {
                return;
            }


            try {

                setCancelandoExecucao(
                    executionId
                );


                const response =
                    await api.post(
                        `/executions/${executionId}/cancel`
                    );


                const data =
                    response.data;


                if (
                    response.status < 200 ||
                    response.status >= 300 ||
                    data.status !== "success"
                ) {

                    window.alert(
                        data.message ||
                        data.error ||
                        "Não foi possível cancelar a execução."
                    );


                    return;
                }


                await carregarExecucoes();

            } catch (err) {

                console.error(
                    "Erro ao cancelar execução:",
                    err
                );


                window.alert(
                    "Não foi possível comunicar com o Control Room."
                );

            } finally {

                setCancelandoExecucao(
                    null
                );
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        executions,
        loading,
        error,

        parandoExecucao,
        cancelandoExecucao,

        carregarExecucoes,
        pararExecucao,
        cancelarExecucao,
    };
}
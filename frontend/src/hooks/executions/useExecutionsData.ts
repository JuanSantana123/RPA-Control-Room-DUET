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
    useRef,
    useState,
} from "react";

import api from "../../services/api";
import { useInteraction } from "../../context/useInteraction";
import { usePollingTask } from "../async/usePollingTask";
import { getApiErrorMessage } from "../../utils/apiErrors";

import type {
    Execution,
} from "../../types/executions";


export function useExecutionsData() {

    const { confirm, notify } = useInteraction();

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

    const [refreshing, setRefreshing] = useState(false);
    const [queueWarningSeconds, setQueueWarningSeconds] = useState(900);
    const requestSequence = useRef(0);

    // ========================================================
    // STOP EM ANDAMENTO
    // ========================================================
    //
    // Mantém o ID da execução cuja parada já foi aceita pelo
    // Agent, mas cujo resultado final ainda não chegou ao
    // Control Room.
    //
    // Usamos useRef porque o polling precisa consultar o valor
    // atual sem depender do ciclo de renderização do React.
    // ========================================================

    const stoppingExecutionRef =
        useRef<number | null>(
            null
        );


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

    const [updatingPriority, setUpdatingPriority] = useState<number | null>(null);


    // ========================================================
    // CARREGAR EXECUÇÕES
    // ========================================================

    const carregarExecucoesComSinal =
        async (signal?: AbortSignal) => {

            const requestId = ++requestSequence.current;

            if (!loading) {
                setRefreshing(true);
            }

            try {

                const response =
                    await api.get(
                        "/executions",
                        { signal },
                    );

                if (requestId !== requestSequence.current) {
                    return;
                }


                // ====================================================
                // EXECUÇÕES RECEBIDAS
                // ====================================================
                //
                // Normalizamos a resposta uma única vez porque ela
                // também será utilizada para verificar se uma parada
                // já foi efetivamente concluída.
                // ====================================================

                const execucoesRecebidas: Execution[] =
                    response.data.executions ??
                    [];

                setExecutions(
                    execucoesRecebidas
                );


                // ====================================================
                // CONFIRMAÇÃO DA PARADA PELO POLLING
                // ====================================================
                //
                // O POST de STOP agora representa apenas:
                //
                //     "Agent aceitou a solicitação"
                //
                // e NÃO:
                //
                //     "Robot já terminou".
                //
                // Portanto mantemos a interface em "Parando..."
                // enquanto a Execution ainda aparece como running.
                //
                // Quando o callback final do Agent atualizar a
                // execução para stopped, ela deixará de aparecer na
                // coleção de execuções em andamento.
                // ====================================================

                const executionIdEmParada =
                    stoppingExecutionRef.current;

                if (executionIdEmParada !== null) {

                    const aindaEstaExecutando =
                        execucoesRecebidas.some(
                            (execution) =>
                                execution.id === executionIdEmParada
                                && execution.status === "running"
                        );

                    if (!aindaEstaExecutando) {

                        // O Control Room já não considera a execução
                        // como running. Portanto a parada foi
                        // consolidada e podemos remover o estado
                        // visual "Parando...".
                        stoppingExecutionRef.current = null;

                        setParandoExecucao(
                            null
                        );
                    }
                }

                if (
                    typeof response.data.queue_warning_seconds === "number"
                    && response.data.queue_warning_seconds >= 60
                ) {
                    setQueueWarningSeconds(response.data.queue_warning_seconds);
                }


                setError("");

            } catch (err) {

                if (signal?.aborted || requestId !== requestSequence.current) {
                    return;
                }

                console.error(
                    "Erro ao carregar execuções:",
                    err
                );


                setError(getApiErrorMessage(
                    err,
                    "Não foi possível carregar as execuções.",
                ));

            } finally {

                if (!signal?.aborted && requestId === requestSequence.current) {
                    setLoading(false);
                    setRefreshing(false);
                }
            }
        };

    const carregarExecucoes = () => carregarExecucoesComSinal();


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

    usePollingTask(
        (signal) => carregarExecucoesComSinal(signal),
        { intervalMs: 5000 },
    );


    // ========================================================
    // PARAR EXECUÇÃO
    // ========================================================

    const pararExecucao =
        async (
            executionId: number,
            agentId: string
        ) => {

            const confirmar = await confirm({
                title: `Parar execução #${executionId}?`,
                description: "O Device receberá um comando para interromper o processo em andamento.",
                detail: "A interrupção pode deixar alterações externas incompletas. Confirme somente após avaliar o impacto operacional.",
                confirmLabel: "Parar execução",
                tone: "danger",
            });


            if (!confirmar) {
                return;
            }


            try {

                // Mantém o ID da execução também na referência utilizada
                // pelo polling para acompanhar a conclusão real do STOP.
                stoppingExecutionRef.current =
                    executionId;

                // Atualiza o estado visual da interface.
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

                // O STOP não foi aceito.
                // Portanto não existe mais uma parada pendente
                // para acompanhar pelo polling.
                stoppingExecutionRef.current = null;

                setParandoExecucao(
                    null
                );

                notify({
                    tone: "danger",
                    title: "A execução não foi interrompida",
                    message:
                        data.message
                        || data.error
                        || "O Control Room recusou o comando de parada.",
                });

                return;
            }


                // Faz uma atualização imediata.
                //
                // Se o Agent já tiver terminado o Robot, essa carga
                // removerá imediatamente o estado "Parando...".
                //
                // Caso contrário, o polling automático continuará
                // acompanhando até a conclusão.
                await carregarExecucoes();

                notify({
                    tone: "success",
                    title: "Parada solicitada",
                    message:
                        `A execução #${executionId} está sendo interrompida.`,
                });

            } catch (err) {

                console.error(
                    "Erro ao enviar comando de stop:",
                    err
                );


                // ====================================================
                // FALHA ANTES DA ACEITAÇÃO DO STOP
                // ====================================================
                //
                // Se houve erro HTTP/rede, não podemos manter a tela
                // indefinidamente em "Parando...".
                // ====================================================

                stoppingExecutionRef.current = null;

                setParandoExecucao(
                    null
                );


                notify({
                    tone: "danger",
                    title: "Falha de comunicação",
                    message:
                        "Não foi possível enviar o comando de parada "
                        + "ao Control Room.",
                });
            }
        };


    // ========================================================
    // CANCELAR EXECUÇÃO DA FILA
    // ========================================================

    const cancelarExecucao =
        async (
            executionId: number
        ) => {

            const confirmar = await confirm({
                title: `Cancelar execução #${executionId}?`,
                description: "A solicitação será retirada da fila antes de iniciar em um Device.",
                confirmLabel: "Cancelar execução",
                tone: "danger",
            });


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

                    notify({
                        tone: "danger",
                        title: "A execução não foi cancelada",
                        message: data.message || data.error || "O Control Room recusou o cancelamento.",
                    });


                    return;
                }


                await carregarExecucoes();
                notify({ tone: "success", title: "Execução cancelada", message: `A execução #${executionId} foi retirada da fila.` });

            } catch (err) {

                console.error(
                    "Erro ao cancelar execução:",
                    err
                );


                notify({ tone: "danger", title: "Falha de comunicação", message: "Não foi possível cancelar a execução no Control Room." });

            } finally {

                setCancelandoExecucao(
                    null
                );
            }
        };


    const alterarPrioridade = async (
        executionId: number,
        priority: Execution["priority"],
    ) => {
        try {
            setUpdatingPriority(executionId);
            const response = await api.patch(
                `/executions/${executionId}/priority`,
                { priority },
            );

            if (response.status < 200 || response.status >= 300 || response.data.status !== "success") {
                notify({
                    tone: "danger",
                    title: "A prioridade não foi alterada",
                    message: response.data.message || "O Control Room recusou a alteração da fila.",
                });
                return;
            }

            setExecutions((current) => current.map((execution) => (
                execution.id === executionId
                    ? { ...execution, priority }
                    : execution
            )));
            await carregarExecucoes();
            notify({
                tone: "success",
                title: "Prioridade atualizada",
                message: `A execução #${executionId} foi reposicionada na fila.`,
            });
        } catch (err) {
            notify({
                tone: "danger",
                title: "Não foi possível alterar a prioridade",
                message: getApiErrorMessage(err, "Falha de comunicação com o Control Room."),
            });
        } finally {
            setUpdatingPriority(null);
        }
    };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
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
    };
}

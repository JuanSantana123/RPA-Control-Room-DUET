// ============================================================
// DUET CORE - HISTORY - DATA HOOK
// ============================================================
//
// Hook responsável pelo carregamento do histórico.
//
// Responsabilidade:
// - consultar GET /executions/history;
// - armazenar execuções finalizadas;
// - controlar loading;
// - controlar erro;
// - realizar primeira carga imediatamente;
// - atualizar o histórico a cada 5 segundos;
// - remover o intervalo ao desmontar a página.
//
// Este hook NÃO:
// - formata datas;
// - calcula duração;
// - traduz status;
// - renderiza a tabela.
//
// O polling preserva exatamente o comportamento existente
// em History.tsx.
// ============================================================

import {
    useRef,
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    HistoryExecution,
} from "../../types/history";
import { usePollingTask } from "../async/usePollingTask";
import { getApiErrorMessage } from "../../utils/apiErrors";


// ============================================================
// HOOK
// ============================================================

export function useHistoryData() {

    // ========================================================
    // EXECUÇÕES
    // ========================================================

    const [
        executions,
        setExecutions,
    ] = useState<HistoryExecution[]>(
        []
    );


    // ========================================================
    // CARREGAMENTO
    // ========================================================

    const [
        loading,
        setLoading,
    ] = useState(true);


    // ========================================================
    // ERRO
    // ========================================================

    const [
        error,
        setError,
    ] = useState("");

    const [refreshing, setRefreshing] = useState(false);

    const requestSequence = useRef(0);


    // ========================================================
    // CARREGAR HISTÓRICO
    // ========================================================

    const carregarHistorico =
            async (signal?: AbortSignal, background = false) => {

                const requestId = ++requestSequence.current;

                if (background && executions.length > 0) {
                    setRefreshing(true);
                }

                try {

                    const response =
                        await api.get(
                            "/executions/history",
                            { signal },
                        );

                    if (requestId !== requestSequence.current) {
                        return;
                    }


                    // Caso executions não exista,
                    // utiliza a mesma lista vazia atual.
                    const lista =
                        response.data.executions ||
                        [];


                    setExecutions(
                        lista
                    );


                    setError("");

                } catch (err) {

                    if (signal?.aborted || requestId !== requestSequence.current) {
                        return;
                    }

                    console.error(
                        "Erro ao carregar histórico:",
                        err
                    );


                    setError(getApiErrorMessage(
                        err,
                        "Não foi possível carregar o histórico.",
                    ));

                } finally {

                    if (!signal?.aborted && requestId === requestSequence.current) {
                        setLoading(false);
                        setRefreshing(false);
                    }
                }
            };


    // ========================================================
    // PRIMEIRA CARGA + POLLING
    // ========================================================

    usePollingTask(
        (signal) => carregarHistorico(signal, executions.length > 0),
        { intervalMs: 5000 },
    );


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        executions,
        loading,
        refreshing,
        error,
        carregarHistorico: () => carregarHistorico(undefined, true),
    };
}

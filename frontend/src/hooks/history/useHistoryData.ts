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
    useCallback,
    useEffect,
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    HistoryExecution,
} from "../../types/history";


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


    // ========================================================
    // CARREGAR HISTÓRICO
    // ========================================================

    const carregarHistorico =
        useCallback(
            async () => {

                try {

                    const response =
                        await api.get(
                            "/executions/history"
                        );


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

                    console.error(
                        "Erro ao carregar histórico:",
                        err
                    );


                    setError(
                        "Não foi possível carregar o histórico."
                    );

                } finally {

                    setLoading(
                        false
                    );
                }
            },
            []
        );


    // ========================================================
    // PRIMEIRA CARGA + POLLING
    // ========================================================

    useEffect(() => {

        // Carrega imediatamente ao abrir a página.
        carregarHistorico();


        // Mantém a atualização automática de 5 segundos.
        const intervalo =
            setInterval(
                () => {

                    carregarHistorico();

                },
                5000
            );


        // Remove o intervalo quando a página for desmontada.
        return () => {

            clearInterval(
                intervalo
            );
        };

    }, [
        carregarHistorico,
    ]);


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        executions,
        loading,
        error,
    };
}
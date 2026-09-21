// ============================================================
// DUET CORE - DASHBOARD - DATA HOOK
// ============================================================
//
// Hook responsável pelos dados operacionais do Dashboard.
//
// Responsabilidade:
// - buscar estatísticas gerais;
// - buscar execuções em andamento;
// - controlar o loading das estatísticas;
// - controlar o erro das estatísticas.
//
// Integrações:
// - GET /dashboard/stats
// - GET /executions
//
// COMPORTAMENTO PRESERVADO:
//
// O Dashboard original possui dois carregamentos independentes,
// executados uma única vez na montagem.
//
// A falha de /dashboard/stats:
// - registra erro no console;
// - define mensagem de erro;
// - encerra o loading.
//
// A falha de /executions:
// - registra somente o erro no console;
// - NÃO coloca o Dashboard inteiro em estado de erro.
//
// Não existe polling no comportamento atual.
// ============================================================

import {
    useEffect,
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    DashboardExecution,
    DashboardStats,
} from "../../types/dashboard";


// ============================================================
// HOOK
// ============================================================

export function useDashboardData() {

    // ========================================================
    // ESTATÍSTICAS
    // ========================================================

    const [
        stats,
        setStats,
    ] = useState<DashboardStats | null>(
        null
    );


    // ========================================================
    // EXECUÇÕES
    // ========================================================

    const [
        executions,
        setExecutions,
    ] = useState<DashboardExecution[]>(
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
    // CARREGAR ESTATÍSTICAS
    // ========================================================
    //
    // Mantém o primeiro useEffect existente no Dashboard.
    // ========================================================

    useEffect(() => {

        api.get(
            "/dashboard/stats"
        )
            .then((response) => {

                setStats(
                    response.data
                );

            })
            .catch((err) => {

                console.error(
                    "Erro ao buscar estatísticas do Dashboard:",
                    err
                );


                setError(
                    "Não foi possível carregar as estatísticas do Dashboard."
                );

            })
            .finally(() => {

                setLoading(false);

            });

    }, []);


    // ========================================================
    // CARREGAR EXECUÇÕES
    // ========================================================
    //
    // Mantém o segundo useEffect existente no Dashboard.
    //
    // IMPORTANTE:
    // O erro desta consulta continua somente no console,
    // exatamente como no arquivo original.
    // ========================================================

    useEffect(() => {

        api.get(
            "/executions"
        )
            .then((response) => {

                setExecutions(
                    response.data.executions
                );

            })
            .catch((err) => {

                console.error(
                    "Erro ao buscar execuções:",
                    err
                );

            });

    }, []);


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        stats,
        executions,
        loading,
        error,
    };
}
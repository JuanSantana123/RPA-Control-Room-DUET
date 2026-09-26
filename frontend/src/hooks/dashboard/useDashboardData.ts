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
    useEffectEvent,
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    DashboardExecution,
    DashboardStats,
} from "../../types/dashboard";
import { getApiErrorMessage } from "../../utils/apiErrors";


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

    const [executionsError, setExecutionsError] = useState("");
    const [refreshing, setRefreshing] = useState(false);


    const carregarDashboard = async (signal?: AbortSignal) => {
        if (stats) {
            setRefreshing(true);
        } else {
            setLoading(true);
        }

        const [statsResult, executionsResult] = await Promise.allSettled([
            api.get("/dashboard/stats", { signal }),
            api.get("/executions", { signal }),
        ]);

        if (signal?.aborted) {
            return;
        }

        if (statsResult.status === "fulfilled") {
            setStats(statsResult.value.data);
            setError("");
        } else {
            console.error("Erro ao buscar estatísticas do Dashboard:", statsResult.reason);
            setError(getApiErrorMessage(
                statsResult.reason,
                "Não foi possível carregar as estatísticas do Dashboard.",
            ));
        }

        if (executionsResult.status === "fulfilled") {
            setExecutions(executionsResult.value.data.executions ?? []);
            setExecutionsError("");
        } else {
            console.error("Erro ao buscar execuções:", executionsResult.reason);
            setExecutionsError(getApiErrorMessage(
                executionsResult.reason,
                "Não foi possível atualizar as execuções em andamento.",
            ));
        }

        setLoading(false);
        setRefreshing(false);
    };

    const carregarDashboardEvent = useEffectEvent(carregarDashboard);

    useEffect(() => {
        const controller = new AbortController();
        const initialLoad = window.setTimeout(
            () => void carregarDashboardEvent(controller.signal),
            0,
        );
        return () => {
            window.clearTimeout(initialLoad);
            controller.abort();
        };
    }, []);


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        stats,
        executions,
        loading,
        refreshing,
        error,
        executionsError,
        recarregar: () => carregarDashboard(),
    };
}

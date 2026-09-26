// ============================================================
// DUET CORE - EXECUTIONS - FILTERS HOOK
// ============================================================
//
// Responsabilidade:
// - controlar o filtro de Robot;
// - controlar o filtro de Agent;
// - gerar as opções únicas disponíveis nos filtros;
// - produzir a coleção final de execuções visíveis;
// - limpar os filtros.
//
// Origem dos dados:
// - recebe a coleção de execuções através de parâmetro.
//
// Este hook NÃO:
// - consulta API;
// - executa polling;
// - para ou cancela execuções;
// - possui responsabilidade visual.
//
// A lógica foi extraída de pages/Executions.tsx sem alteração
// das regras existentes.
// ============================================================

import {
    useMemo,
} from "react";
import { useSearchParams } from "react-router-dom";

import type {
    Execution,
} from "../../types/executions";


export function useExecutionFilters(
    executions: Execution[]
) {

    // ========================================================
    // ESTADOS DOS FILTROS
    // ========================================================

    const [searchParams, setSearchParams] = useSearchParams();
    const filtroRobo = searchParams.get("robot") ?? "";
    const filtroAgent = searchParams.get("agent") ?? "";

    const updateFilter = (key: "robot" | "agent", value: string) => {
        setSearchParams((current) => {
            const next = new URLSearchParams(current);

            if (value) {
                next.set(key, value);
            } else {
                next.delete(key);
            }

            return next;
        });
    };

    const setFiltroRobo = (value: string) => updateFilter("robot", value);
    const setFiltroAgent = (value: string) => updateFilter("agent", value);


    // ========================================================
    // ROBOTS DISPONÍVEIS
    // ========================================================
    //
    // Gera a lista única de nomes utilizada no select.
    // ========================================================

    const robos =
        useMemo(() => {

            return Array.from(
                new Set(
                    executions
                        .map(
                            (execution) =>
                                execution.robot_name
                        )
                        .filter(Boolean)
                )
            );

        }, [executions]);


    // ========================================================
    // AGENTS DISPONÍVEIS
    // ========================================================

    const agents =
        useMemo(() => {

            return Array.from(
                new Set(
                    executions
                        .map(
                            (execution) =>
                                execution.agent_name
                        )
                        .filter(Boolean)
                )
            );

        }, [executions]);


    // ========================================================
    // EXECUÇÕES VISÍVEIS
    // ========================================================

    const execucoesFiltradas =
        useMemo(() => {

            return executions.filter(
                (execution) => {

                    const correspondeRobo =
                        !filtroRobo ||
                        execution.robot_name ===
                            filtroRobo;


                    const correspondeAgent =
                        !filtroAgent ||
                        execution.agent_name ===
                            filtroAgent;


                    return (
                        correspondeRobo &&
                        correspondeAgent
                    );
                }
            );

        }, [
            executions,
            filtroRobo,
            filtroAgent,
        ]);


    // ========================================================
    // LIMPAR FILTROS
    // ========================================================

    const limparFiltros = () => {
        setSearchParams((current) => {
            const next = new URLSearchParams(current);
            next.delete("robot");
            next.delete("agent");
            return next;
        });
    };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        filtroRobo,
        setFiltroRobo,

        filtroAgent,
        setFiltroAgent,

        robos,
        agents,

        execucoesFiltradas,

        limparFiltros,
    };
}

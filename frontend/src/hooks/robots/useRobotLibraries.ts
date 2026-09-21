// ============================================================
// DUET CORE - ROBOTS - LIBRARIES HOOK
// ============================================================
//
// Responsabilidade:
// - consultar o snapshot EXATO de Libraries de um Release;
// - armazenar snapshots já carregados;
// - evitar consultas repetidas;
// - controlar expansão do painel de Libraries;
// - controlar estado de carregamento.
//
// IMPORTANTE:
// Este hook NÃO consulta simplesmente a versão atualmente
// vigente de uma Library.
//
// Ele consulta as versões imutáveis registradas no Release
// específico do Robot.
//
// Este hook NÃO:
// - altera Libraries;
// - publica Libraries;
// - gerencia o catálogo global;
// - renderiza componentes.
//
// Integração:
// GET /robots/{robot_id}/versions/{robot_version}/libraries
//
// A lógica foi extraída de Robots.tsx sem alterar o
// comportamento funcional existente.
// ============================================================

import {
    useState,
} from "react";

import api from "../../services/api";

import type {
    Robot,
    RobotLibraryDependency,
    RobotLibrariesResponse,
} from "../../types/robots";


interface UseRobotLibrariesParams {

    // Mensagens continuam sendo apresentadas pela página.
    setError: React.Dispatch<
        React.SetStateAction<string>
    >;
}


export function useRobotLibraries({
    setError,
}: UseRobotLibrariesParams) {

    // ========================================================
    // SNAPSHOTS CARREGADOS
    // ========================================================
    //
    // Chave:
    // robot.id
    //
    // Valor:
    // versões exatas das Libraries utilizadas pelo Release.
    // ========================================================

    const [
        robotLibraries,
        setRobotLibraries,
    ] = useState<
        Record<
            number,
            RobotLibraryDependency[]
        >
    >({});


    // ========================================================
    // ROBOTS JÁ CONSULTADOS
    // ========================================================
    //
    // Permite diferenciar:
    //
    // - ainda não consultado;
    // - consultado e possui zero Libraries.
    // ========================================================

    const [
        loadedRobotLibraries,
        setLoadedRobotLibraries,
    ] = useState<Set<number>>(
        new Set()
    );


    // ========================================================
    // PAINEL EXPANDIDO
    // ========================================================

    const [
        expandedRobotLibraries,
        setExpandedRobotLibraries,
    ] = useState<number | null>(
        null
    );


    // ========================================================
    // CONSULTA EM ANDAMENTO
    // ========================================================

    const [
        loadingRobotLibraries,
        setLoadingRobotLibraries,
    ] = useState<number | null>(
        null
    );


    // ========================================================
    // CARREGAR LIBRARIES DO RELEASE
    // ========================================================

    const carregarBibliotecasDoRobo =
        async (
            robot: Robot
        ): Promise<
            RobotLibraryDependency[]
        > => {

            // Reutiliza o snapshot se já foi consultado
            // durante esta sessão da página.
            if (
                loadedRobotLibraries.has(
                    robot.id
                )
            ) {

                return (
                    robotLibraries[
                        robot.id
                    ] || []
                );
            }


            setLoadingRobotLibraries(
                robot.id
            );


            try {

                const response =
                    await api.get<
                        RobotLibrariesResponse
                    >(
                        `/robots/${robot.id}/versions/${robot.version}/libraries`
                    );


                const libraries =
                    response.data.libraries ||
                    [];


                // Armazena o snapshot pelo ID do Robot.
                setRobotLibraries(
                    (current) => ({
                        ...current,

                        [robot.id]:
                            libraries,
                    })
                );


                // Marca o Robot como consultado.
                setLoadedRobotLibraries(
                    (current) => {

                        const next =
                            new Set(current);


                        next.add(
                            robot.id
                        );


                        return next;
                    }
                );


                return libraries;

            } catch (err) {

                console.error(
                    "Erro ao carregar bibliotecas do Robot:",
                    err
                );


                setError(
                    `Não foi possível carregar as bibliotecas de "${robot.name}".`
                );


                return [];

            } finally {

                setLoadingRobotLibraries(
                    null
                );
            }
        };


    // ========================================================
    // ABRIR / FECHAR SNAPSHOT
    // ========================================================

    const alternarBibliotecasDoRobo =
        async (
            robot: Robot
        ) => {

            // Se já estiver aberto, fecha.
            if (
                expandedRobotLibraries ===
                robot.id
            ) {

                setExpandedRobotLibraries(
                    null
                );

                return;
            }


            // Abre o painel do Robot escolhido.
            setExpandedRobotLibraries(
                robot.id
            );


            // Consulta somente se ainda não estiver em cache.
            if (
                !loadedRobotLibraries.has(
                    robot.id
                )
            ) {

                await carregarBibliotecasDoRobo(
                    robot
                );
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        robotLibraries,
        loadedRobotLibraries,

        expandedRobotLibraries,
        loadingRobotLibraries,

        carregarBibliotecasDoRobo,
        alternarBibliotecasDoRobo,
    };
}
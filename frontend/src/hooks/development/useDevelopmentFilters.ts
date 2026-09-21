// ============================================================
// USE DEVELOPMENT FILTERS
// ============================================================
//
// Responsabilidade:
//     Centraliza a lógica de filtragem utilizada pela página
//     Development do DUET CORE.
//
// O hook calcula:
//     - projetos ativos filtrados;
//     - etapas do Kanban com cards filtrados;
//     - quantidade de projetos visíveis no Kanban;
//     - projetos da Lixeira filtrados.
//
// Arquitetura:
//     Este hook contém somente lógica derivada de estado.
//
// Este arquivo NÃO deve:
//     - realizar chamadas HTTP;
//     - alterar projetos;
//     - alterar etapas do Workflow;
//     - controlar permissões;
//     - possuir efeitos colaterais;
//     - persistir qualquer informação.
//
// Os arrays originais continuam pertencendo ao
// Development.tsx.
//
// O hook recebe os dados atuais e devolve somente
// representações derivadas através de useMemo.
// ============================================================

import {
    useMemo,
} from "react";


import type {
    DevelopmentProject,
    DevelopmentStage,
} from "../../types/development";


// ============================================================
// PARÂMETROS
// ============================================================

interface UseDevelopmentFiltersParams {

    // Texto atual da pesquisa compartilhada pela página.
    search:
        string;


    // Projetos ativos de Desenvolvimento.
    projects:
        DevelopmentProject[];


    // Etapas completas retornadas pelo Workflow.
    kanbanStages:
        DevelopmentStage[];


    // Projetos atualmente presentes na Lixeira.
    trashProjects:
        DevelopmentProject[];
}


// ============================================================
// RETORNO
// ============================================================

interface UseDevelopmentFiltersResult {

    // Projetos ativos depois da pesquisa.
    filteredProjects:
        DevelopmentProject[];


    // Mesmas etapas do Workflow, porém com os projetos
    // de cada coluna filtrados pela pesquisa.
    filteredKanbanStages:
        DevelopmentStage[];


    // Quantidade total de cards atualmente visíveis
    // depois da pesquisa aplicada ao Kanban.
    filteredKanbanProjectCount:
        number;


    // Projetos da Lixeira depois da pesquisa.
    filteredTrashProjects:
        DevelopmentProject[];
}


// ============================================================
// HOOK
// ============================================================

function useDevelopmentFilters({
    search,
    projects,
    kanbanStages,
    trashProjects,
}: UseDevelopmentFiltersParams): UseDevelopmentFiltersResult {

    // ========================================================
    // PROJETOS ATIVOS
    // ========================================================

    const filteredProjects =
        useMemo(
            () => {

                const term =
                    search
                        .trim()
                        .toLowerCase();


                // Sem pesquisa, mantém exatamente o array
                // atualmente carregado pela página.
                if (!term) {
                    return projects;
                }


                return projects.filter(
                    (project) =>
                        project.name
                            .toLowerCase()
                            .includes(term) ||
                        (
                            project.description
                                ?.toLowerCase()
                                .includes(term)
                            ?? false
                        )
                );
            },
            [
                projects,
                search,
            ]
        );


    // ========================================================
    // KANBAN
    // ========================================================
    //
    // As etapas permanecem intactas.
    //
    // Somente o array "projects" de cada etapa é filtrado.
    // ========================================================

    const filteredKanbanStages =
        useMemo(
            () => {

                const term =
                    search
                        .trim()
                        .toLowerCase();


                if (!term) {
                    return kanbanStages;
                }


                return kanbanStages.map(
                    (stage) => ({
                        ...stage,

                        projects:
                            stage.projects.filter(
                                (project) =>
                                    project.name
                                        .toLowerCase()
                                        .includes(term) ||
                                    (
                                        project.description
                                            ?.toLowerCase()
                                            .includes(term)
                                        ?? false
                                    )
                            ),
                    })
                );
            },
            [
                kanbanStages,
                search,
            ]
        );


    // ========================================================
    // CONTAGEM VISÍVEL DO KANBAN
    // ========================================================

    const filteredKanbanProjectCount =
        useMemo(
            () =>
                filteredKanbanStages.reduce(
                    (total, stage) =>
                        total +
                        stage.projects.length,

                    0
                ),
            [
                filteredKanbanStages,
            ]
        );


    // ========================================================
    // LIXEIRA
    // ========================================================

    const filteredTrashProjects =
        useMemo(
            () => {

                const term =
                    search
                        .trim()
                        .toLowerCase();


                if (!term) {
                    return trashProjects;
                }


                return trashProjects.filter(
                    (project) =>
                        project.name
                            .toLowerCase()
                            .includes(term) ||
                        (
                            project.description
                                ?.toLowerCase()
                                .includes(term)
                            ?? false
                        )
                );
            },
            [
                trashProjects,
                search,
            ]
        );


    // ========================================================
    // RESULTADO
    // ========================================================

    return {
        filteredProjects,
        filteredKanbanStages,
        filteredKanbanProjectCount,
        filteredTrashProjects,
    };
}


export default useDevelopmentFilters;
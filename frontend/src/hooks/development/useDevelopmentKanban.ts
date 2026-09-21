// ============================================================
// USE DEVELOPMENT KANBAN
// ============================================================
//
// Responsabilidade:
//     Centraliza o estado operacional e as ações do Workflow /
//     Kanban da área de Desenvolvimento.
//
// O hook controla:
//     - carregamento do board;
//     - stages oficiais retornados pelo backend;
//     - movimentação de AutomationProjects entre stages;
//     - estados de drag-and-drop;
//     - localização de projetos dentro do board;
//     - proteção contra movimentações simultâneas;
//     - limpeza do drag após movimentação;
//     - feedback de erro das operações do Workflow.
//
// Integrações:
//     GET   /development/workflow/board
//     PATCH /development/projects/{id}/stage
//
// A página fornece:
//     - permissão de visualização;
//     - permissão de movimentação;
//     - callback para atualizar a lista oficial de projetos;
//     - callback para feedback global de erro.
//
// Este arquivo NÃO deve:
//     - renderizar KanbanBoard;
//     - controlar pesquisa;
//     - controlar viewMode;
//     - controlar Release;
//     - controlar Card Details;
//     - controlar Studio;
//     - decidir quando a página entra ou sai da visualização Kanban.
//
// Development.tsx continua responsável pela navegação entre
// Projetos / Kanban / Lixeira.
//
// KanbanBoard continua exclusivamente visual.
// ============================================================

import {
    useState,

    type DragEvent,
} from "react";


import api
    from "../../services/api";


import {
    getApiErrorMessage,
} from "../../utils/apiErrors";


import type {
    DevelopmentProject,
    DevelopmentStage,
} from "../../types/development";


// ============================================================
// PARÂMETROS
// ============================================================

interface UseDevelopmentKanbanParams {

    // Permissão efetiva Development:view.
    canViewDevelopment:
        boolean;


    // Permissão efetiva Development:move_stage.
    canMoveDevelopmentStage:
        boolean;


    // Development.tsx continua sendo dono da lista oficial
    // utilizada na visualização de Projetos.
    //
    // Quando o backend devolver o projeto movimentado,
    // o hook entrega esse objeto para a página.
    onProjectMoved:
        (
            project: DevelopmentProject
        ) => void;


    // Erros continuam aparecendo no feedback global
    // já existente no Development.tsx.
    onError:
        (
            message: string
        ) => void;
}


// ============================================================
// RETORNO
// ============================================================

interface UseDevelopmentKanbanResult {

    // Board oficial.
    kanbanStages:
        DevelopmentStage[];


    // Estados operacionais.
    loadingKanban:
        boolean;

    movingProjectId:
        number | null;


    // Estados de drag-and-drop.
    draggedProjectId:
        number | null;

    draggedSourceStageCode:
        string | null;

    dragOverStageId:
        number | null;


    // Utilizado pelo KanbanBoard durante drag-over.
    setDragOverStageId:
        (
            value: number | null
        ) => void;


    // Ações públicas.
    loadKanban:
        () => Promise<void>;

    moveProjectToStage:
        (
            project: DevelopmentProject,
            targetStage: DevelopmentStage
        ) => Promise<void>;

    handleKanbanDragStart:
        (
            event: DragEvent<HTMLElement>,
            project: DevelopmentProject,
            stage: DevelopmentStage
        ) => void;

    handleKanbanDragEnd:
        () => void;

    handleKanbanDrop:
        (
            event: DragEvent<HTMLElement>,
            targetStage: DevelopmentStage
        ) => Promise<void>;
}


// ============================================================
// HOOK
// ============================================================

function useDevelopmentKanban({
    canViewDevelopment,
    canMoveDevelopmentStage,
    onProjectMoved,
    onError,
}: UseDevelopmentKanbanParams): UseDevelopmentKanbanResult {

    // ========================================================
    // ESTADOS - BOARD
    // ========================================================

    const [
        kanbanStages,
        setKanbanStages,
    ] =
        useState<DevelopmentStage[]>([]);


    const [
        loadingKanban,
        setLoadingKanban,
    ] =
        useState(false);


    const [
        movingProjectId,
        setMovingProjectId,
    ] =
        useState<number | null>(
            null
        );


    // ========================================================
    // ESTADOS - DRAG AND DROP
    // ========================================================

    const [
        draggedProjectId,
        setDraggedProjectId,
    ] =
        useState<number | null>(
            null
        );


    const [
        draggedSourceStageCode,
        setDraggedSourceStageCode,
    ] =
        useState<string | null>(
            null
        );


    const [
        dragOverStageId,
        setDragOverStageId,
    ] =
        useState<number | null>(
            null
        );


    // ========================================================
    // LIMPAR DRAG
    // ========================================================
    //
    // Mantém em um único lugar a limpeza dos três estados
    // temporários utilizados durante drag-and-drop.
    // ========================================================

    const clearDragState = () => {

        setDraggedProjectId(
            null
        );


        setDraggedSourceStageCode(
            null
        );


        setDragOverStageId(
            null
        );
    };


    // ========================================================
    // CARREGAR WORKFLOW / KANBAN
    // ========================================================

    const loadKanban = async () => {

        if (!canViewDevelopment) {

            setKanbanStages(
                []
            );


            setLoadingKanban(
                false
            );


            return;
        }


        try {

            setLoadingKanban(
                true
            );


            onError(
                ""
            );


            const response =
                await api.get(
                    "/development/workflow/board"
                );


            setKanbanStages(
                response.data?.stages || []
            );

        } catch (err: any) {

            console.error(
                "Erro ao carregar o Kanban de Desenvolvimento:",
                err
            );


            onError(
                getApiErrorMessage(
                    err,
                    "Não foi possível carregar o Kanban."
                )
            );

        } finally {

            setLoadingKanban(
                false
            );
        }
    };


    // ========================================================
    // LOCALIZAR PROJETO NO BOARD
    // ========================================================
    //
    // Função interna.
    //
    // O restante da aplicação não precisa conhecer a forma
    // como um projeto é localizado dentro dos stages.
    // ========================================================

    const findKanbanProject = (
        projectId: number
    ): DevelopmentProject | null => {

        for (
            const stage
            of kanbanStages
        ) {

            const project =
                stage.projects.find(
                    (item) =>
                        item.id ===
                        projectId
                );


            if (project) {
                return project;
            }
        }


        return null;
    };


    // ========================================================
    // MOVIMENTAR PROJETO NO WORKFLOW
    // ========================================================

    const moveProjectToStage = async (
        project: DevelopmentProject,
        targetStage: DevelopmentStage
    ) => {

        // Mantém exatamente as proteções atuais.
        if (
            !canMoveDevelopmentStage ||
            movingProjectId !== null
        ) {
            return;
        }


        // PUBLISHED não aceita movimentação manual.
        if (
            targetStage.code === "PUBLISHED"
        ) {
            return;
        }


        // Não executa PATCH quando o projeto já está
        // no stage solicitado.
        if (
            project.current_stage_id ===
            targetStage.id
        ) {
            return;
        }


        try {

            setMovingProjectId(
                project.id
            );


            onError(
                ""
            );


            const response =
                await api.patch(
                    `/development/projects/${project.id}/stage`,
                    {
                        target_stage_id:
                            targetStage.id,
                    }
                );


            const movedProject:
                DevelopmentProject | undefined =
                    response.data?.project;


            if (movedProject) {

                // A página continua dona da lista oficial
                // de AutomationProjects.
                onProjectMoved(
                    movedProject
                );
            }


            // O board é recarregado somente depois da
            // confirmação do PATCH.
            await loadKanban();

        } catch (err: any) {

            console.error(
                "Erro ao movimentar projeto no Workflow:",
                err
            );


            onError(
                getApiErrorMessage(
                    err,
                    "Não foi possível movimentar o projeto."
                )
            );

        } finally {

            setMovingProjectId(
                null
            );


            clearDragState();
        }
    };


    // ========================================================
    // DRAG START
    // ========================================================

    const handleKanbanDragStart = (
        event: DragEvent<HTMLElement>,
        project: DevelopmentProject,
        stage: DevelopmentStage
    ) => {

        // Mantém as mesmas regras atuais:
        //
        // - precisa da permissão move_stage;
        // - cards publicados não podem ser arrastados;
        // - não inicia novo drag durante movimentação.
        if (
            !canMoveDevelopmentStage ||
            stage.code === "PUBLISHED" ||
            movingProjectId !== null
        ) {

            event.preventDefault();

            return;
        }


        event.dataTransfer.effectAllowed =
            "move";


        // Mantemos o ID também no DataTransfer para preservar
        // compatibilidade com o comportamento atual.
        event.dataTransfer.setData(
            "text/plain",
            String(
                project.id
            )
        );


        setDraggedProjectId(
            project.id
        );


        setDraggedSourceStageCode(
            stage.code
        );
    };


    // ========================================================
    // DRAG END
    // ========================================================

    const handleKanbanDragEnd = () => {

        clearDragState();
    };


    // ========================================================
    // DROP
    // ========================================================

    const handleKanbanDrop = async (
        event: DragEvent<HTMLElement>,
        targetStage: DevelopmentStage
    ) => {

        event.preventDefault();


        setDragOverStageId(
            null
        );


        // PUBLISHED continua protegido tanto como destino
        // quanto como origem.
        if (
            !canMoveDevelopmentStage ||
            targetStage.code === "PUBLISHED" ||
            draggedSourceStageCode === "PUBLISHED"
        ) {
            return;
        }


        const transferredId =
            Number(
                event.dataTransfer.getData(
                    "text/plain"
                )
            );


        // Primeiro utiliza o ID controlado pelo React.
        //
        // Como fallback, preserva o ID armazenado no
        // DataTransfer do navegador.
        const projectId =
            draggedProjectId ??
            (
                Number.isFinite(
                    transferredId
                )
                    ? transferredId
                    : null
            );


        if (
            projectId === null
        ) {
            return;
        }


        const project =
            findKanbanProject(
                projectId
            );


        if (!project) {

            onError(
                "Não foi possível localizar o projeto no quadro."
            );


            return;
        }


        await moveProjectToStage(
            project,
            targetStage
        );
    };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        kanbanStages,
        loadingKanban,
        movingProjectId,

        draggedProjectId,
        draggedSourceStageCode,
        dragOverStageId,

        setDragOverStageId,

        loadKanban,
        moveProjectToStage,

        handleKanbanDragStart,
        handleKanbanDragEnd,
        handleKanbanDrop,
    };
}


export default useDevelopmentKanban;
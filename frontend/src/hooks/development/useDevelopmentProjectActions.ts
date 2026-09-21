// ============================================================
// USE DEVELOPMENT PROJECT ACTIONS
// ============================================================
//
// Responsabilidade:
//     Centraliza as operações executadas sobre AutomationProjects
//     ativos na área de Desenvolvimento.
//
// Nesta versão, o hook controla:
//     - soft delete de um AutomationProject;
//     - confirmação da exclusão;
//     - proteção contra requisições duplicadas;
//     - estado do projeto atualmente sendo excluído;
//     - tratamento de erro da operação.
//
// Integração:
//     DELETE /development/projects/{project_id}
//
// O backend continua responsável pela regra real de exclusão:
//
//     - o projeto deixa a área ativa de Desenvolvimento;
//     - o registro permanece preservado no banco;
//     - o workspace físico permanece preservado;
//     - o projeto passa a poder ser tratado pela Lixeira.
//
// Development.tsx continua responsável por:
//     - lista oficial de projetos ativos;
//     - menu visual de três pontos;
//     - posição do menu;
//     - navegação para o Studio;
//     - execução;
//     - Workflow;
//     - Lixeira.
//
// Este hook NÃO deve:
//     - renderizar componentes;
//     - conhecer ProjectOptionsMenu;
//     - calcular posição de menus;
//     - manipular viewMode;
//     - manipular Kanban;
//     - excluir permanentemente projetos.
//
// A exclusão permanente pertence ao domínio da Lixeira,
// atualmente isolado em useDevelopmentTrash.
// ============================================================

import {
    useState,
} from "react";


import api
    from "../../services/api";


import {
    getApiErrorMessage,
} from "../../utils/apiErrors";


import type {
    DevelopmentProject,
} from "../../types/development";


// ============================================================
// PARÂMETROS
// ============================================================

interface UseDevelopmentProjectActionsParams {

    // Permissão efetiva:
    //
    // Development:delete
    canDeleteDevelopment:
        boolean;


    // Development.tsx continua dono da coleção oficial.
    //
    // Depois que o backend confirmar o soft delete,
    // o hook devolve o projeto removido para a página.
    onProjectDeleted:
        (
            project: DevelopmentProject
        ) => void;


    // Permite que a página feche elementos visuais associados
    // ao projeto antes de iniciar efetivamente a exclusão.
    //
    // Atualmente será utilizado para fechar o menu de opções.
    onBeforeDelete?:
        (
            project: DevelopmentProject
        ) => void;


    // Feedback global continua pertencendo ao container
    // Development.tsx.
    onError:
        (
            message: string
        ) => void;
}


// ============================================================
// RETORNO
// ============================================================

interface UseDevelopmentProjectActionsResult {

    // ID do projeto que possui uma requisição DELETE
    // atualmente em andamento.
    deletingProjectId:
        number | null;


    // Executa o fluxo completo de soft delete.
    deleteProject:
        (
            project: DevelopmentProject
        ) => Promise<void>;
}


// ============================================================
// HOOK
// ============================================================

function useDevelopmentProjectActions({
    canDeleteDevelopment,
    onProjectDeleted,
    onBeforeDelete,
    onError,
}: UseDevelopmentProjectActionsParams): UseDevelopmentProjectActionsResult {

    // ========================================================
    // ESTADO OPERACIONAL
    // ========================================================
    //
    // null:
    //     nenhuma exclusão em andamento.
    //
    // number:
    //     ID do AutomationProject cujo DELETE está sendo
    //     processado pelo backend.
    // ========================================================

    const [
        deletingProjectId,
        setDeletingProjectId,
    ] =
        useState<number | null>(
            null
        );


    // ========================================================
    // SOFT DELETE
    // ========================================================

    const deleteProject = async (
        project: DevelopmentProject
    ) => {

        // ----------------------------------------------------
        // PERMISSÃO
        // ----------------------------------------------------

        if (!canDeleteDevelopment) {
            return;
        }


        // ----------------------------------------------------
        // PROTEÇÃO CONTRA DUPLICIDADE
        // ----------------------------------------------------
        //
        // Enquanto uma exclusão estiver em andamento,
        // nenhuma segunda exclusão é iniciada.
        // ----------------------------------------------------

        if (
            deletingProjectId !== null
        ) {
            return;
        }


        // ----------------------------------------------------
        // CONFIRMAÇÃO
        // ----------------------------------------------------
        //
        // Mantém exatamente a confirmação utilizada
        // atualmente pelo Development.tsx.
        // ----------------------------------------------------

        const confirmed =
            window.confirm(
                `Excluir o projeto "${project.name}"?\n\n` +
                "O projeto será removido da área de Desenvolvimento."
            );


        if (!confirmed) {
            return;
        }


        // ----------------------------------------------------
        // PREPARAÇÃO VISUAL
        // ----------------------------------------------------
        //
        // O hook informa à página que a exclusão foi
        // confirmada.
        //
        // Development.tsx decide o que precisa fechar
        // visualmente. Hoje: ProjectOptionsMenu.
        // ----------------------------------------------------

        onBeforeDelete?.(
            project
        );


        try {

            setDeletingProjectId(
                project.id
            );


            // Limpa feedback anterior antes da operação.
            onError(
                ""
            );


            // ------------------------------------------------
            // SOFT DELETE
            // ------------------------------------------------
            //
            // O backend altera o estado lógico do projeto.
            //
            // O workspace físico NÃO deve ser removido por
            // esta operação.
            // ------------------------------------------------

            await api.delete(
                `/development/projects/${project.id}`
            );


            // ------------------------------------------------
            // CONFIRMAÇÃO PARA O CONTAINER
            // ------------------------------------------------
            //
            // O hook não altera diretamente a coleção global.
            //
            // Development.tsx continua sendo dono de projects
            // e decide como remover o item da interface.
            // ------------------------------------------------

            onProjectDeleted(
                project
            );

        } catch (err: any) {

            console.error(
                "Erro ao excluir projeto de Desenvolvimento:",
                err
            );


            onError(
                getApiErrorMessage(
                    err,
                    "Não foi possível excluir o projeto."
                )
            );

        } finally {

            setDeletingProjectId(
                null
            );
        }
    };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        deletingProjectId,
        deleteProject,
    };
}


export default useDevelopmentProjectActions;
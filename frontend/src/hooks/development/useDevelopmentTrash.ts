// ============================================================
// USE DEVELOPMENT TRASH
// ============================================================
//
// Responsabilidade:
//     Centraliza o estado e as operações de persistência da
//     Lixeira de AutomationProjects da área Development.
//
// O hook controla:
//     - projetos presentes na Lixeira;
//     - carregamento da Lixeira;
//     - projeto atualmente sendo restaurado;
//     - projeto atualmente sendo excluído permanentemente;
//     - consulta dos projetos removidos;
//     - restauração de um projeto;
//     - exclusão permanente de um projeto.
//
// Integração:
//     - utiliza o client HTTP padrão do DUET CORE;
//     - recebe as permissões já calculadas pela página;
//     - comunica alterações na lista de projetos ativos através
//       de callbacks fornecidos pelo Development.tsx.
//
// Arquitetura:
//     Development.tsx continua responsável pela navegação visual
//     entre Projetos, Kanban e Lixeira.
//
//     Este hook é responsável somente pelo domínio operacional
//     da Lixeira.
//
// Este arquivo NÃO deve:
//     - renderizar componentes;
//     - controlar search;
//     - controlar viewMode;
//     - controlar showTrash;
//     - abrir ou fechar menus;
//     - executar automações;
//     - publicar Releases;
//     - alterar o Kanban.
//
// Dessa forma, navegação de página e persistência da Lixeira
// permanecem responsabilidades separadas.
// ============================================================

import {
    useState,
} from "react";


import api
    from "../../services/api";


import type {
    DevelopmentProject,
} from "../../types/development";


// ============================================================
// PARÂMETROS
// ============================================================

interface UseDevelopmentTrashParams {

    // Permissão para visualizar a Lixeira.
    canViewTrash:
        boolean;


    // Permissão para restaurar projetos.
    canRestoreDevelopment:
        boolean;


    // Permissão para exclusão definitiva.
    canPermanentDeleteDevelopment:
        boolean;


    // Permite que o hook devolva um projeto restaurado
    // para a lista oficial de projetos ativos da página.
    onProjectRestored:
        (
            project: DevelopmentProject
        ) => void;


    // Permite que erros operacionais da Lixeira continuem
    // aparecendo na área global de feedback da página.
    onError:
        (
            message: string
        ) => void;
}


// ============================================================
// RETORNO
// ============================================================

interface UseDevelopmentTrashResult {

    // Projetos atualmente presentes na Lixeira.
    trashProjects:
        DevelopmentProject[];


    // GET da Lixeira em andamento.
    loadingTrash:
        boolean;


    // ID do projeto atualmente sendo restaurado.
    restoringProjectId:
        number | null;


    // ID do projeto atualmente sendo excluído definitivamente.
    permanentlyDeletingProjectId:
        number | null;


    // Consulta novamente a Lixeira no backend.
    loadTrash:
        () => Promise<void>;


    // Restaura um AutomationProject.
    restoreProject:
        (
            project: DevelopmentProject
        ) => Promise<void>;


    // Exclui definitivamente um AutomationProject.
    permanentlyDeleteProject:
        (
            project: DevelopmentProject
        ) => Promise<void>;
}


// ============================================================
// HOOK
// ============================================================

function useDevelopmentTrash({
    canViewTrash,
    canRestoreDevelopment,
    canPermanentDeleteDevelopment,
    onProjectRestored,
    onError,
}: UseDevelopmentTrashParams): UseDevelopmentTrashResult {

    // ========================================================
    // ESTADOS
    // ========================================================

    // Projetos retornados por:
    //
    // GET /development/projects/trash
    const [
        trashProjects,
        setTrashProjects,
    ] =
        useState<DevelopmentProject[]>([]);


    // Loading independente da lista principal de projetos.
    const [
        loadingTrash,
        setLoadingTrash,
    ] =
        useState(false);


    // Projeto atualmente sendo restaurado.
    const [
        restoringProjectId,
        setRestoringProjectId,
    ] =
        useState<number | null>(
            null
        );


    // Projeto atualmente sendo apagado definitivamente.
    const [
        permanentlyDeletingProjectId,
        setPermanentlyDeletingProjectId,
    ] =
        useState<number | null>(
            null
        );


    // ========================================================
    // CARREGAR LIXEIRA
    // ========================================================

    const loadTrash = async () => {

        if (!canViewTrash) {

            setLoadingTrash(
                false
            );

            return;
        }


        try {

            setLoadingTrash(
                true
            );


            onError(
                ""
            );


            const response =
                await api.get(
                    "/development/projects/trash"
                );


            setTrashProjects(
                response.data?.projects || []
            );

        } catch (err: any) {

            console.error(
                "Erro ao carregar Lixeira de Desenvolvimento:",
                err
            );


            const message =
                err.response?.data?.detail ||
                err.response?.data?.message ||
                "Não foi possível carregar a Lixeira.";


            onError(
                message
            );

        } finally {

            setLoadingTrash(
                false
            );
        }
    };


    // ========================================================
    // RESTAURAR PROJETO
    // ========================================================

    const restoreProject = async (
        project: DevelopmentProject
    ) => {

        if (!canRestoreDevelopment) {
            return;
        }


        // Mantém a trava atual:
        // restauração e exclusão permanente não podem ocorrer
        // simultaneamente.
        if (
            restoringProjectId !== null ||
            permanentlyDeletingProjectId !== null
        ) {
            return;
        }


        try {

            setRestoringProjectId(
                project.id
            );


            onError(
                ""
            );


            const response =
                await api.post(
                    `/development/projects/${project.id}/restore`
                );


            const restoredProject:
                DevelopmentProject | undefined =
                    response.data?.project;


            if (!restoredProject) {

                throw new Error(
                    "O backend não retornou o projeto restaurado."
                );
            }


            // Remove imediatamente o projeto da Lixeira.
            setTrashProjects(
                (current) =>
                    current.filter(
                        (item) =>
                            item.id !== project.id
                    )
            );


            // Development.tsx continua sendo dono da lista
            // oficial de projetos ativos.
            onProjectRestored(
                restoredProject
            );

        } catch (err: any) {

            console.error(
                "Erro ao restaurar projeto:",
                err
            );


            const message =
                err.response?.data?.detail ||
                err.response?.data?.message ||
                err.message ||
                "Não foi possível restaurar o projeto.";


            onError(
                message
            );

        } finally {

            setRestoringProjectId(
                null
            );
        }
    };


    // ========================================================
    // EXCLUIR PROJETO PERMANENTEMENTE
    // ========================================================

    const permanentlyDeleteProject = async (
        project: DevelopmentProject
    ) => {

        if (
            !canPermanentDeleteDevelopment
        ) {
            return;
        }


        if (
            permanentlyDeletingProjectId !== null ||
            restoringProjectId !== null
        ) {
            return;
        }


        // ====================================================
        // CONFIRMAÇÃO FORTE
        // ====================================================
        //
        // Mantém exatamente a proteção atual:
        // o usuário precisa digitar o nome completo do projeto
        // antes da exclusão irreversível.
        // ====================================================

        const confirmation =
            window.prompt(
                `Esta ação é irreversível.\n\n` +
                `Para excluir permanentemente "${project.name}", ` +
                "digite exatamente o nome do projeto:"
            );


        if (
            confirmation !== project.name
        ) {
            return;
        }


        try {

            setPermanentlyDeletingProjectId(
                project.id
            );


            onError(
                ""
            );


            await api.delete(
                `/development/projects/${project.id}/permanent`
            );


            // O backend confirmou a exclusão definitiva.
            // Portanto removemos o projeto da cópia local.
            setTrashProjects(
                (current) =>
                    current.filter(
                        (item) =>
                            item.id !== project.id
                    )
            );

        } catch (err: any) {

            console.error(
                "Erro ao excluir projeto permanentemente:",
                err
            );


            const message =
                err.response?.data?.detail ||
                err.response?.data?.message ||
                "Não foi possível excluir o projeto permanentemente.";


            onError(
                message
            );

        } finally {

            setPermanentlyDeletingProjectId(
                null
            );
        }
    };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        trashProjects,
        loadingTrash,
        restoringProjectId,
        permanentlyDeletingProjectId,

        loadTrash,
        restoreProject,
        permanentlyDeleteProject,
    };
}


export default useDevelopmentTrash;
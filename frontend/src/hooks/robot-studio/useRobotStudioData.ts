// ============================================================
// DUET CORE - ROBOT STUDIO - DATA
// ============================================================
//
// Responsabilidade:
// - carregar permissões do usuário autenticado;
// - carregar os metadados do AutomationProject;
// - disponibilizar as permissões derivadas usadas pelo Studio.
//
// NÃO controla:
// - Checkout;
// - workspace;
// - editor;
// - Libraries.
//
// A segurança definitiva continua sendo responsabilidade
// do backend. Este hook apenas reproduz o controle visual
// existente no RobotStudio.
// ============================================================

import {
    useEffect,
    useState,
} from "react";

import api from "../../services/api";

import type {
    AutomationProject,
} from "../../types/robotStudio";


interface UseRobotStudioDataParams {
    projectId?: string;
}


export function useRobotStudioData({
    projectId,
}: UseRobotStudioDataParams) {

    // ========================================================
    // METADADOS DO PROJETO
    // ========================================================

    const [project, setProject] =
        useState<AutomationProject | null>(
            null
        );

    // Mantido exatamente como responsabilidade interna.
    // Atualmente o RobotStudio não apresenta este erro
    // diretamente na interface.
    const [, setProjectError] =
        useState("");


    // ========================================================
    // PERMISSÕES
    // ========================================================

    const [permissions, setPermissions] =
        useState<string[]>([]);

    const [
        permissionsLoaded,
        setPermissionsLoaded,
    ] = useState(false);


    const canViewDevelopment =
        permissions.includes(
            "Development:view"
        );

    const canEditWorkspace =
        permissions.includes(
            "Development:edit"
        );

    const canCheckout =
        permissions.includes(
            "Development:checkout"
        );

    const canForceCheckoutRelease =
        permissions.includes(
            "Development:force_checkout_release"
        );

    const canViewLibraries =
        permissions.includes(
            "Libraries:view"
        );

    const canUseLibrary =
        permissions.includes(
            "Libraries:use"
        );

    const canCreateLibrary =
        permissions.includes(
            "Libraries:create"
        );


    // ========================================================
    // CARREGAR PERMISSÕES DO USUÁRIO
    // ========================================================

    useEffect(() => {

        const carregarPermissoes =
            async () => {

                try {

                    const response =
                        await api.get(
                            "/auth/me"
                        );

                    const permissoes =
                        response.data?.user
                            ?.permissions || [];

                    setPermissions(
                        Array.isArray(
                            permissoes
                        )
                            ? permissoes
                            : []
                    );

                } catch (err) {

                    console.error(
                        "Erro ao carregar permissões do usuário no DUET Studio:",
                        err
                    );

                    // Em caso de falha, nenhuma funcionalidade
                    // protegida é liberada pela interface.
                    setPermissions([]);

                } finally {

                    setPermissionsLoaded(
                        true
                    );
                }
            };


        carregarPermissoes();

    }, []);


    // ========================================================
    // CARREGAR METADADOS DO PROJETO
    // ========================================================

    useEffect(() => {

        const carregarProjeto =
            async () => {

                if (
                    !permissionsLoaded ||
                    !canViewDevelopment
                ) {
                    return;
                }


                if (!projectId) {

                    setProjectError(
                        "ID do projeto não informado."
                    );

                    return;
                }


                try {

                    setProjectError("");

                    const response =
                        await api.get(
                            `/development/projects/${projectId}`
                        );

                    const projeto:
                        AutomationProject | undefined =
                            response.data?.project;


                    if (!projeto) {

                        throw new Error(
                            "O backend não retornou os dados do projeto."
                        );
                    }


                    setProject(
                        projeto
                    );

                } catch (err: any) {

                    console.error(
                        "Erro ao carregar projeto no DUET Studio:",
                        err
                    );

                    const mensagem =
                        err.response?.data?.detail ||
                        err.response?.data?.message ||
                        "Não foi possível carregar o projeto.";

                    setProjectError(
                        mensagem
                    );
                }
            };


        carregarProjeto();

    }, [
        projectId,
        permissionsLoaded,
        canViewDevelopment,
    ]);


    return {
        project,

        permissionsLoaded,

        canViewDevelopment,
        canEditWorkspace,
        canCheckout,
        canForceCheckoutRelease,

        canViewLibraries,
        canUseLibrary,
        canCreateLibrary,
    };
}
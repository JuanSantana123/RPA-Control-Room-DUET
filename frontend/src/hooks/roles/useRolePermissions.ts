// ============================================================
// DUET CORE - ROLES - PERMISSIONS HOOK
// ============================================================
//
// Hook responsável pela configuração de permissões das Roles.
//
// Responsabilidade:
// - carregar o catálogo de permissões;
// - controlar a Role selecionada;
// - buscar permissões já associadas;
// - marcar/desmarcar permissões localmente;
// - salvar o estado completo das permissões;
// - limpar seleção quando uma Role selecionada for excluída.
//
// Integrações:
// - GET /roles/permissions
// - GET /roles/{role_id}/permissions
// - PUT /roles/{role_id}/permissions
//
// Este hook NÃO:
// - cria Roles;
// - exclui Roles;
// - renderiza checkboxes;
// - agrupa permissões visualmente.
//
// O agrupamento visual permanece em um utilitário puro.
// ============================================================

import {
    useCallback,
    useEffect,
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    Permission,
    Role,
} from "../../types/roles";


// ============================================================
// PROPS
// ============================================================

interface UseRolePermissionsProps {
    setError:
        (message: string) => void;

    setSuccess:
        (message: string) => void;
}


// ============================================================
// HOOK
// ============================================================

export function useRolePermissions({
    setError,
    setSuccess,
}: UseRolePermissionsProps) {

    // ========================================================
    // ROLE SELECIONADA
    // ========================================================

    const [
        selectedRole,
        setSelectedRole,
    ] = useState<Role | null>(
        null
    );


    // ========================================================
    // CATÁLOGO
    // ========================================================

    const [
        permissions,
        setPermissions,
    ] = useState<Permission[]>([]);


    const [
        selectedPermissions,
        setSelectedPermissions,
    ] = useState<number[]>([]);


    // ========================================================
    // CARREGAMENTO
    // ========================================================

    const [
        loadingPermissions,
        setLoadingPermissions,
    ] = useState(false);


    // O estado original possui somente o valor false.
    // Não adicionamos nova regra de saving durante
    // esta modularização.
    const [
        savingPermissions,
    ] = useState(false);


    // ========================================================
    // CARREGAR CATÁLOGO DE PERMISSÕES
    // ========================================================

    const carregarPermissoes =
        useCallback(
            async () => {

                try {

                    setLoadingPermissions(
                        true
                    );

                    setError("");


                    const response =
                        await api.get(
                            "/roles/permissions"
                        );


                    setPermissions(
                        response.data
                    );

                } catch (err) {

                    console.error(
                        "Erro ao buscar permissões:",
                        err
                    );


                    setError(
                        "Não foi possível carregar as permissões."
                    );

                } finally {

                    setLoadingPermissions(
                        false
                    );
                }
            },
            [
                setError,
            ]
        );


    // ========================================================
    // CARREGAMENTO INICIAL
    // ========================================================

    useEffect(() => {

        carregarPermissoes();

    }, [
        carregarPermissoes,
    ]);


    // ========================================================
    // SELECIONAR ROLE
    // ========================================================

    const selecionarRole =
        async (
            role: Role
        ) => {

            setSelectedRole(
                role
            );


            setSelectedPermissions(
                []
            );


            try {

                const response =
                    await api.get(
                        `/roles/${role.id}/permissions`
                    );


                const permissoesExistentes =
                    response.data.map(
                        (
                            permissao:
                                Permission
                        ) =>
                            permissao.id
                    );


                setSelectedPermissions(
                    permissoesExistentes
                );

            } catch (err) {

                console.error(
                    "Erro ao carregar permissões da Role:",
                    err
                );


                setError(
                    "Não foi possível carregar as permissões da Role."
                );
            }
        };


    // ========================================================
    // ALTERAR PERMISSÃO LOCAL
    // ========================================================

    const alternarPermissao =
        (
            permissionId: number
        ) => {

            setSelectedPermissions(
                (permissoesAtuais) => {

                    if (
                        permissoesAtuais.includes(
                            permissionId
                        )
                    ) {

                        return permissoesAtuais.filter(
                            (id) =>
                                id !==
                                permissionId
                        );
                    }


                    return [
                        ...permissoesAtuais,
                        permissionId,
                    ];
                }
            );
        };


    // ========================================================
    // SALVAR PERMISSÕES
    // ========================================================

    const salvarPermissoes =
        async () => {

            if (!selectedRole) {

                setError(
                    "Selecione uma Role."
                );

                return;
            }


            try {

                setError("");
                setSuccess("");


                // Envia o estado completo da seleção.
                const response =
                    await api.put(
                        `/roles/${selectedRole.id}/permissions`,
                        {
                            permission_ids:
                                selectedPermissions,
                        }
                    );


                if (
                    response.data?.status ===
                    "success"
                ) {

                    setSuccess(
                        "Permissões salvas com sucesso."
                    );


                    // Recarrega o estado persistido para que
                    // a interface reflita exatamente o backend.
                    const permissoesAtualizadas =
                        await api.get(
                            `/roles/${selectedRole.id}/permissions`
                        );


                    const idsAtualizados =
                        permissoesAtualizadas.data.map(
                            (
                                permissao:
                                    Permission
                            ) =>
                                permissao.id
                        );


                    setSelectedPermissions(
                        idsAtualizados
                    );

                } else {

                    setError(
                        response.data?.message ||
                        "Não foi possível salvar as permissões."
                    );
                }

            } catch (err: any) {

                console.error(
                    "Erro ao salvar permissões:",
                    err
                );


                setError(
                    err.response?.data?.detail ||
                    "Não foi possível salvar as permissões."
                );
            }
        };


    // ========================================================
    // ROLE EXCLUÍDA
    // ========================================================
    //
    // Mantém o comportamento anterior:
    // se a Role excluída estiver selecionada, limpa o painel.
    // ========================================================

    const handleRoleDeleted =
        (
            roleId: number
        ) => {

            if (
                selectedRole?.id ===
                roleId
            ) {

                setSelectedRole(
                    null
                );

                setSelectedPermissions(
                    []
                );
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        selectedRole,

        permissions,
        selectedPermissions,

        loadingPermissions,
        savingPermissions,

        selecionarRole,
        alternarPermissao,
        salvarPermissoes,

        handleRoleDeleted,
    };
}
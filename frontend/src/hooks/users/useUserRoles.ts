// ============================================================
// DUET CORE - USERS - ROLE EDITING HOOK
// ============================================================
//
// Hook responsável exclusivamente pela edição das Roles
// associadas a um usuário.
//
// Responsabilidade:
// - iniciar edição;
// - armazenar Roles selecionadas;
// - marcar/desmarcar Roles;
// - cancelar edição;
// - persistir a nova coleção de Roles.
//
// Integração:
// - PUT /auth/users/{user_id}/roles
//
// Este hook NÃO:
// - cria usuários;
// - exclui usuários;
// - altera senha;
// - carrega permissões do usuário logado;
// - renderiza interface.
// ============================================================

import {
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    User,
} from "../../types/users";


// ============================================================
// PROPS
// ============================================================

interface UseUserRolesProps {
    setError:
        (message: string) => void;

    setSuccess:
        (message: string) => void;

    reloadUsers:
        () => Promise<void>;
}


// ============================================================
// HOOK
// ============================================================

export function useUserRoles({
    setError,
    setSuccess,
    reloadUsers,
}: UseUserRolesProps) {

    const [
        editingUserId,
        setEditingUserId,
    ] = useState<number | null>(
        null
    );


    const [
        editingRoleIds,
        setEditingRoleIds,
    ] = useState<number[]>([]);


    // ========================================================
    // INICIAR EDIÇÃO
    // ========================================================

    const iniciarEdicaoRoles =
        (
            user: User
        ) => {

            setEditingUserId(
                user.id
            );


            setEditingRoleIds(
                user.roles.map(
                    (role) =>
                        role.id
                )
            );


            setError("");
            setSuccess("");
        };


    // ========================================================
    // ALTERNAR ROLE
    // ========================================================

    const alternarRole =
        (
            roleId: number
        ) => {

            if (
                editingRoleIds.includes(
                    roleId
                )
            ) {

                setEditingRoleIds(
                    editingRoleIds.filter(
                        (id) =>
                            id !== roleId
                    )
                );

                return;
            }


            setEditingRoleIds([
                ...editingRoleIds,
                roleId,
            ]);
        };


    // ========================================================
    // CANCELAR EDIÇÃO
    // ========================================================

    const cancelarEdicaoRoles =
        () => {

            setEditingUserId(
                null
            );

            setEditingRoleIds(
                []
            );
        };


    // ========================================================
    // SALVAR ROLES
    // ========================================================

    const salvarRolesUsuario =
        async () => {

            if (
                editingUserId === null
            ) {
                return;
            }


            setError("");
            setSuccess("");


            try {

                await api.put(
                    `/auth/users/${editingUserId}/roles`,
                    {
                        role_ids:
                            editingRoleIds,
                    }
                );


                setSuccess(
                    "Roles do usuário atualizadas com sucesso."
                );


                setEditingUserId(
                    null
                );

                setEditingRoleIds(
                    []
                );


                await reloadUsers();

            } catch (err: any) {

                console.error(
                    "Erro ao atualizar Roles do usuário:",
                    err
                );


                setError(
                    err.response?.data?.detail ||
                    err.response?.data?.message ||
                    "Não foi possível atualizar as Roles do usuário."
                );
            }
        };


    // ========================================================
    // USUÁRIO EXCLUÍDO
    // ========================================================

    const handleUserDeleted =
        (
            userId: number
        ) => {

            if (
                editingUserId ===
                userId
            ) {

                setEditingUserId(
                    null
                );

                setEditingRoleIds(
                    []
                );
            }
        };


    return {
        editingUserId,
        editingRoleIds,

        iniciarEdicaoRoles,
        alternarRole,
        cancelarEdicaoRoles,
        salvarRolesUsuario,

        handleUserDeleted,
    };
}
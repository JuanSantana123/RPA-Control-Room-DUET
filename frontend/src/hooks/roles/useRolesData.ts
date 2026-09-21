// ============================================================
// DUET CORE - ROLES - DATA HOOK
// ============================================================
//
// Hook responsável pela gestão da coleção de Roles.
//
// Responsabilidade:
// - carregar Roles;
// - controlar loading da listagem;
// - controlar formulário de criação;
// - criar uma Role;
// - excluir uma Role;
// - controlar mensagens de erro e sucesso.
//
// Integrações:
// - GET    /roles
// - POST   /roles
// - DELETE /roles/{role_id}
//
// Este hook NÃO:
// - gerencia permissões;
// - seleciona permissões;
// - renderiza interface;
// - agrupa catálogo de permissões.
//
// A lógica foi extraída de pages/Roles.tsx sem alterar
// os contratos atualmente utilizados.
// ============================================================

import {
    useCallback,
    useEffect,
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    Role,
} from "../../types/roles";


// ============================================================
// HOOK
// ============================================================

export function useRolesData() {

    // ========================================================
    // ROLES
    // ========================================================

    const [
        roles,
        setRoles,
    ] = useState<Role[]>([]);


    const [
        loadingRoles,
        setLoadingRoles,
    ] = useState(true);


    // ========================================================
    // CRIAÇÃO
    // ========================================================

    const [
        showCreateForm,
        setShowCreateForm,
    ] = useState(false);


    const [
        roleName,
        setRoleName,
    ] = useState("");


    const [
        roleDescription,
        setRoleDescription,
    ] = useState("");


    const [
        creatingRole,
        setCreatingRole,
    ] = useState(false);


    // ========================================================
    // MENSAGENS
    // ========================================================

    const [
        error,
        setError,
    ] = useState("");


    const [
        success,
        setSuccess,
    ] = useState("");


    // ========================================================
    // BUSCAR ROLES
    // ========================================================

    const carregarRoles =
        useCallback(
            async () => {

                try {

                    setLoadingRoles(
                        true
                    );

                    setError("");


                    const response =
                        await api.get(
                            "/roles"
                        );


                    setRoles(
                        response.data
                    );

                } catch (err) {

                    console.error(
                        "Erro ao buscar Roles:",
                        err
                    );


                    setError(
                        "Não foi possível carregar as Roles."
                    );

                } finally {

                    setLoadingRoles(
                        false
                    );
                }
            },
            []
        );


    // ========================================================
    // CARREGAMENTO INICIAL DAS ROLES
    // ========================================================

    useEffect(() => {

        carregarRoles();

    }, [
        carregarRoles,
    ]);


    // ========================================================
    // ABRIR FORMULÁRIO
    // ========================================================

    const abrirFormulario = () => {

        setRoleName("");
        setRoleDescription("");

        setError("");
        setSuccess("");

        setShowCreateForm(
            true
        );
    };


    // ========================================================
    // CANCELAR CRIAÇÃO
    // ========================================================

    const cancelarCriacao = () => {

        setShowCreateForm(
            false
        );

        setRoleName("");
        setRoleDescription("");

        setError("");
    };


    // ========================================================
    // CRIAR ROLE
    // ========================================================

    const criarRole =
        async () => {

            if (
                !roleName.trim()
            ) {

                setError(
                    "Informe o nome da Role."
                );

                return;
            }


            try {

                setCreatingRole(
                    true
                );

                setError("");
                setSuccess("");


                const response =
                    await api.post(
                        "/roles",
                        {
                            name:
                                roleName.trim(),

                            description:
                                roleDescription.trim() ||
                                null,
                        }
                    );


                if (
                    response.data?.status ===
                    "success"
                ) {

                    if (
                        response.data.role
                    ) {

                        setRoles(
                            (rolesAtuais) => [
                                ...rolesAtuais,
                                response.data.role,
                            ]
                        );

                    } else {

                        await carregarRoles();
                    }


                    setShowCreateForm(
                        false
                    );

                    setRoleName("");
                    setRoleDescription("");


                    setSuccess(
                        "Role criada com sucesso."
                    );

                } else {

                    setError(
                        response.data?.message ||
                        "Não foi possível criar a Role."
                    );
                }

            } catch (err: any) {

                console.error(
                    "Erro ao criar Role:",
                    err
                );


                console.error(
                    "Resposta da API:",
                    err.response?.data
                );


                setError(
                    err.response?.data?.detail ||
                    err.response?.data?.message ||
                    "Não foi possível criar a Role."
                );

            } finally {

                setCreatingRole(
                    false
                );
            }
        };


    // ========================================================
    // EXCLUIR ROLE
    // ========================================================
    //
    // Recebe callback opcional para permitir que a camada
    // responsável pelas permissões limpe a Role selecionada
    // caso justamente ela seja excluída.
    // ========================================================

    const excluirRole =
        async (
            roleId: number,
            onDeleted?: (
                roleId: number
            ) => void
        ) => {

            const confirmar =
                window.confirm(
                    "Tem certeza que deseja excluir esta Role?"
                );


            if (!confirmar) {
                return;
            }


            try {

                setError("");
                setSuccess("");


                await api.delete(
                    `/roles/${roleId}`
                );


                if (onDeleted) {

                    onDeleted(
                        roleId
                    );
                }


                await carregarRoles();


                setSuccess(
                    "Role excluída com sucesso."
                );

            } catch (err: any) {

                console.error(
                    "Erro ao excluir Role:",
                    err
                );


                setError(
                    err.response?.data?.detail ||
                    err.response?.data?.message ||
                    "Não foi possível excluir a Role."
                );
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        roles,
        loadingRoles,

        showCreateForm,

        roleName,
        setRoleName,

        roleDescription,
        setRoleDescription,

        creatingRole,

        error,
        success,

        setError,
        setSuccess,

        abrirFormulario,
        cancelarCriacao,
        criarRole,
        excluirRole,
    };
}
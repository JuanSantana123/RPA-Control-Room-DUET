// ============================================================
// DUET CORE - USERS - DATA HOOK
// ============================================================
//
// Hook principal de dados da gestão de usuários.
//
// Responsabilidade:
// - carregar permissões do usuário logado;
// - carregar usuários quando houver Users:view;
// - carregar Roles quando houver Roles:view;
// - criar usuários;
// - excluir usuários;
// - ativar/desativar usuários;
// - controlar mensagens globais.
//
// Integrações:
// - GET    /auth/me
// - GET    /auth/users
// - GET    /roles
// - POST   /auth/users
// - DELETE /auth/users/{user_id}
// - PATCH  /auth/users/{user_id}/status
//
// Este hook NÃO:
// - edita Roles de um usuário;
// - altera senha;
// - renderiza componentes.
//
// Essas responsabilidades ficam em hooks específicos.
// ============================================================

import {
    useCallback,
    useEffect,
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    User,
    UserAvailableRole,
} from "../../types/users";


// ============================================================
// HOOK
// ============================================================

export function useUsersData() {

    // ========================================================
    // USUÁRIOS / PERMISSÕES
    // ========================================================

    const [
        users,
        setUsers,
    ] = useState<User[]>([]);


    const [
        permissions,
        setPermissions,
    ] = useState<string[]>([]);


    const [
        permissionsLoaded,
        setPermissionsLoaded,
    ] = useState(false);


    const [
        loading,
        setLoading,
    ] = useState(true);


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
    // NOVO USUÁRIO
    // ========================================================

    const [
        username,
        setUsername,
    ] = useState("");


    const [
        name,
        setName,
    ] = useState("");


    const [
        password,
        setPassword,
    ] = useState("");


    // ========================================================
    // ROLES DISPONÍVEIS
    // ========================================================

    const [
        roles,
        setRoles,
    ] = useState<UserAvailableRole[]>([]);


    const [
        selectedRoleId,
        setSelectedRoleId,
    ] = useState<number | "">("");


    // ========================================================
    // BUSCAR USUÁRIOS
    // ========================================================

    const carregarUsuarios =
        useCallback(
            async () => {

                try {

                    setLoading(true);
                    setError("");


                    const response =
                        await api.get(
                            "/auth/users"
                        );


                    setUsers(
                        response.data
                    );

                } catch (err) {

                    console.error(
                        "Erro ao carregar usuários:",
                        err
                    );


                    setError(
                        "Não foi possível carregar os usuários."
                    );

                } finally {

                    setLoading(false);
                }
            },
            []
        );


    // ========================================================
    // CARREGAR ROLES
    // ========================================================

    const carregarRoles =
        useCallback(
            async () => {

                try {

                    const response =
                        await api.get(
                            "/roles"
                        );


                    setRoles(
                        response.data
                    );

                } catch (err) {

                    console.error(
                        "Erro ao carregar Roles:",
                        err
                    );


                    setError(
                        "Não foi possível carregar as Roles."
                    );
                }
            },
            []
        );


    // ========================================================
    // CARREGAMENTO INICIAL
    // ========================================================
    //
    // Preserva a ordem original:
    //
    // 1. GET /auth/me
    // 2. Users:view -> carregar usuários
    // 3. Roles:view -> carregar Roles
    // 4. permissionsLoaded = true
    // ========================================================

    useEffect(() => {

        const carregarDados =
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
                        permissoes
                    );


                    if (
                        permissoes.includes(
                            "Users:view"
                        )
                    ) {

                        await carregarUsuarios();

                    } else {

                        setLoading(false);
                    }


                    if (
                        permissoes.includes(
                            "Roles:view"
                        )
                    ) {

                        await carregarRoles();
                    }

                } catch (err) {

                    console.error(
                        "Erro ao carregar permissões do usuário:",
                        err
                    );


                    setPermissions([]);

                    setLoading(false);

                } finally {

                    setPermissionsLoaded(
                        true
                    );
                }
            };


        carregarDados();

    }, [
        carregarRoles,
        carregarUsuarios,
    ]);


    // ========================================================
    // CRIAR USUÁRIO
    // ========================================================

    const criarUsuario =
        async () => {

            setError("");
            setSuccess("");


            if (!username.trim()) {

                setError(
                    "Informe o username."
                );

                return;
            }


            if (!name.trim()) {

                setError(
                    "Informe o nome."
                );

                return;
            }


            if (!password) {

                setError(
                    "Informe a senha."
                );

                return;
            }


            try {

                const response =
                    await api.post(
                        "/auth/users",
                        {
                            username:
                                username.trim(),

                            password,

                            name:
                                name.trim(),

                            role_id:
                                selectedRoleId === ""
                                    ? null
                                    : Number(
                                        selectedRoleId
                                    ),
                        }
                    );


                if (
                    response.data?.status ===
                    "success"
                ) {

                    setSuccess(
                        "Usuário criado com sucesso."
                    );


                    setUsername("");
                    setName("");
                    setPassword("");


                    await carregarUsuarios();

                } else {

                    setError(
                        response.data?.message ||
                        "Não foi possível criar o usuário."
                    );
                }

            } catch (err: any) {

                console.error(
                    "Erro ao criar usuário:",
                    err
                );


                setError(
                    err.response?.data?.detail ||
                    "Não foi possível criar o usuário."
                );
            }
        };


    // ========================================================
    // EXCLUIR USUÁRIO
    // ========================================================

    const excluirUsuario =
        async (
            userId: number,
            onDeleted?: (
                userId: number
            ) => void
        ) => {

            const confirmar =
                window.confirm(
                    "Tem certeza que deseja excluir este usuário?"
                );


            if (!confirmar) {
                return;
            }


            setError("");
            setSuccess("");


            try {

                await api.delete(
                    `/auth/users/${userId}`
                );


                setSuccess(
                    "Usuário excluído com sucesso."
                );


                // Permite que os hooks especializados limpem
                // seus estados caso necessário.
                if (onDeleted) {

                    onDeleted(
                        userId
                    );
                }


                await carregarUsuarios();

            } catch (err: any) {

                console.error(
                    "Erro ao excluir usuário:",
                    err
                );


                setError(
                    err.response?.data?.detail ||
                    err.response?.data?.message ||
                    "Não foi possível excluir o usuário."
                );
            }
        };


    // ========================================================
    // ATIVAR / DESATIVAR USUÁRIO
    // ========================================================

    const alterarStatusUsuario =
        async (
            user: User
        ) => {

            const novoStatus =
                user.is_active !== 1;


            const acao =
                novoStatus
                    ? "ativar"
                    : "desativar";


            const confirmar =
                window.confirm(
                    `Tem certeza que deseja ${acao} o usuário "${user.name}"?`
                );


            if (!confirmar) {
                return;
            }


            setError("");
            setSuccess("");


            try {

                await api.patch(
                    `/auth/users/${user.id}/status`,
                    {
                        is_active:
                            novoStatus,
                    }
                );


                setSuccess(
                    novoStatus
                        ? "Usuário ativado com sucesso."
                        : "Usuário desativado com sucesso."
                );


                await carregarUsuarios();

            } catch (err: any) {

                console.error(
                    "Erro ao alterar status do usuário:",
                    err
                );


                setError(
                    err.response?.data?.detail ||
                    err.response?.data?.message ||
                    "Não foi possível alterar o status do usuário."
                );
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        users,
        permissions,
        permissionsLoaded,
        loading,

        error,
        success,
        setError,
        setSuccess,

        username,
        setUsername,

        name,
        setName,

        password,
        setPassword,

        roles,

        selectedRoleId,
        setSelectedRoleId,

        carregarUsuarios,
        criarUsuario,
        excluirUsuario,
        alterarStatusUsuario,
    };
}
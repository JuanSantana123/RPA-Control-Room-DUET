// ============================================================
// DUET CORE - USERS PAGE
// ============================================================
//
// Página principal da gestão de usuários do Control Room.
//
// Responsabilidade:
// - compor a interface de usuários;
// - conectar os hooks especializados aos componentes visuais;
// - respeitar as permissões efetivas do usuário logado;
// - coordenar criação, edição de Roles, alteração de senha,
//   exclusão e ativação/desativação.
//
// Arquitetura:
//
// Users
//   │
//   ├── useUsersData
//   │     ├── permissões do usuário logado
//   │     ├── listagem
//   │     ├── criação
//   │     ├── exclusão
//   │     └── ativação/desativação
//   │
//   ├── useUserRoles
//   │     └── edição das Roles do usuário
//   │
//   ├── useUserPassword
//   │     └── alteração de senha
//   │
//   ├── UsersHeader
//   ├── UserCreatePanel
//   ├── UserRolesEditPanel
//   ├── UserPasswordPanel
//   └── UsersTable
//         └── UserRow
//
// Esta página NÃO:
// - executa chamadas HTTP diretamente;
// - implementa regras de CRUD;
// - manipula diretamente os checkboxes de Roles;
// - valida ou altera senhas;
// - renderiza individualmente as linhas da tabela.
//
// A página funciona como camada de composição.
// ============================================================

import UsersHeader
    from "../components/users/UsersHeader";

import UserCreatePanel
    from "../components/users/UserCreatePanel";

import UserRolesEditPanel
    from "../components/users/UserRolesEditPanel";

import UserPasswordPanel
    from "../components/users/UserPasswordPanel";

import UsersTable
    from "../components/users/UsersTable";

import {
    useUsersData,
} from "../hooks/users/useUsersData";

import {
    useUserRoles,
} from "../hooks/users/useUserRoles";

import {
    useUserPassword,
} from "../hooks/users/useUserPassword";


// ============================================================
// PÁGINA DE USUÁRIOS
// ============================================================

function Users() {

    // ========================================================
    // DADOS PRINCIPAIS
    // ========================================================
    //
    // Responsável por:
    // - usuários;
    // - permissões;
    // - Roles disponíveis;
    // - criação;
    // - exclusão;
    // - ativação/desativação;
    // - mensagens globais.
    // ========================================================

    const {
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
    } = useUsersData();


    // ========================================================
    // EDIÇÃO DE ROLES
    // ========================================================

    const {
        editingUserId,
        editingRoleIds,

        iniciarEdicaoRoles,
        alternarRole,
        cancelarEdicaoRoles,
        salvarRolesUsuario,

        handleUserDeleted,
    } = useUserRoles({
        setError,
        setSuccess,
        reloadUsers:
            carregarUsuarios,
    });


    // ========================================================
    // ALTERAÇÃO DE SENHA
    // ========================================================

    const {
        changingPasswordUserId,

        newPassword,
        setNewPassword,

        confirmNewPassword,
        setConfirmNewPassword,

        iniciarAlteracaoSenha,
        cancelarAlteracaoSenha,
        salvarNovaSenha,
    } = useUserPassword({
        setError,
        setSuccess,
    });


    // ========================================================
    // EXCLUSÃO
    // ========================================================
    //
    // A exclusão pertence a useUsersData.
    //
    // Após a exclusão, notificamos useUserRoles para preservar
    // o comportamento anterior: se o usuário removido estiver
    // com suas Roles em edição, o modo de edição é encerrado.
    // ========================================================

    const handleDeleteUser =
        async (
            userId: number
        ) => {

            await excluirUsuario(
                userId,
                handleUserDeleted
            );
        };


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="users-page">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <UsersHeader />


            {/* ==================================================
                MENSAGENS GLOBAIS
                ================================================== */}

            {error && (

                <div className="users-alert users-alert-error">

                    <span>
                        ⚠
                    </span>

                    <span>
                        {error}
                    </span>

                </div>

            )}


            {success && (

                <div className="users-alert users-alert-success">

                    <span>
                        ✓
                    </span>

                    <span>
                        {success}
                    </span>

                </div>

            )}


            {/* ==================================================
                CRIAÇÃO DE USUÁRIO
                ==================================================
                
                Preserva a regra atual:
                
                - permissões precisam estar carregadas;
                - usuário precisa possuir Users:create.
                ================================================== */}

            {permissionsLoaded &&
                permissions.includes(
                    "Users:create"
                ) && (

                    <UserCreatePanel
                        username={
                            username
                        }
                        setUsername={
                            setUsername
                        }
                        name={
                            name
                        }
                        setName={
                            setName
                        }
                        password={
                            password
                        }
                        setPassword={
                            setPassword
                        }
                        roles={
                            roles
                        }
                        selectedRoleId={
                            selectedRoleId
                        }
                        setSelectedRoleId={
                            setSelectedRoleId
                        }
                        onCreate={
                            criarUsuario
                        }
                    />

                )}


            {/* ==================================================
                EDIÇÃO DE ROLES
                ================================================== */}

            {editingUserId !== null && (

                <UserRolesEditPanel
                    roles={
                        roles
                    }
                    editingRoleIds={
                        editingRoleIds
                    }
                    onToggleRole={
                        alternarRole
                    }
                    onCancel={
                        cancelarEdicaoRoles
                    }
                    onSave={
                        salvarRolesUsuario
                    }
                />

            )}


            {/* ==================================================
                ALTERAÇÃO DE SENHA
                ================================================== */}

            {changingPasswordUserId !== null && (

                <UserPasswordPanel
                    newPassword={
                        newPassword
                    }
                    setNewPassword={
                        setNewPassword
                    }
                    confirmNewPassword={
                        confirmNewPassword
                    }
                    setConfirmNewPassword={
                        setConfirmNewPassword
                    }
                    onCancel={
                        cancelarAlteracaoSenha
                    }
                    onSave={
                        salvarNovaSenha
                    }
                />

            )}


            {/* ==================================================
                LISTA DE USUÁRIOS
                ==================================================
                
                Preserva a regra atual:
                
                - permissões precisam estar carregadas;
                - usuário precisa possuir Users:view.
                ================================================== */}

            {permissionsLoaded &&
                permissions.includes(
                    "Users:view"
                ) && (

                    <UsersTable
                        users={
                            users
                        }
                        permissions={
                            permissions
                        }
                        loading={
                            loading
                        }
                        onEditRoles={
                            iniciarEdicaoRoles
                        }
                        onChangePassword={
                            iniciarAlteracaoSenha
                        }
                        onDelete={
                            handleDeleteUser
                        }
                        onChangeStatus={
                            alterarStatusUsuario
                        }
                    />

                )}

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default Users;
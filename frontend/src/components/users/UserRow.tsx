// ============================================================
// DUET CORE - USERS - USER ROW
// ============================================================
//
// Representação visual de um usuário na tabela.
//
// Responsabilidade:
// - apresentar identidade;
// - apresentar ID;
// - apresentar Roles;
// - apresentar status;
// - disponibilizar ações permitidas.
//
// As ações são condicionadas pelas permissões efetivas
// recebidas da página.
//
// Este componente NÃO:
// - modifica usuários;
// - executa chamadas HTTP;
// - decide permissões do usuário logado;
// - controla formulários de edição.
// ============================================================

import type {
    User,
} from "../../types/users";


// ============================================================
// PROPS
// ============================================================

interface UserRowProps {
    user:
        User;

    permissions:
        string[];

    onEditRoles:
        (user: User) => void;

    onChangePassword:
        (user: User) => void;

    onDelete:
        (userId: number) => void | Promise<void>;

    onChangeStatus:
        (user: User) => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function UserRow({
    user,
    permissions,
    onEditRoles,
    onChangePassword,
    onDelete,
    onChangeStatus,
}: UserRowProps) {

    return (
        <tr>

            {/* ==================================================
                IDENTIDADE
                ================================================== */}

            <td>

                <div className="users-identity">

                    <div className="users-avatar">

                        {user.name
                            ? user.name
                                .substring(
                                    0,
                                    2
                                )
                                .toUpperCase()
                            : "US"
                        }

                    </div>


                    <div className="users-identity-info">

                        <p className="users-identity-name">
                            {user.name}
                        </p>

                        <span className="users-identity-username">
                            @{user.username}
                        </span>

                    </div>

                </div>

            </td>


            {/* ==================================================
                ID
                ================================================== */}

            <td>
                #{user.id}
            </td>


            {/* ==================================================
                ROLES
                ================================================== */}

            <td>

                {user.roles &&
                user.roles.length > 0 ? (

                    <div className="users-role-badges">

                        {user.roles.map(
                            (role) => (

                                <span
                                    key={role.id}
                                    className="users-role-badge"
                                >
                                    {role.name}
                                </span>

                            )
                        )}

                    </div>

                ) : (

                    <span className="users-no-role">
                        Nenhuma Role
                    </span>

                )}

            </td>


            {/* ==================================================
                STATUS
                ================================================== */}

            <td>

                <span
                    className={`users-status ${
                        user.is_active === 1
                            ? "users-status-active"
                            : "users-status-inactive"
                    }`}
                >
                    {user.is_active === 1
                        ? "Ativo"
                        : "Inativo"
                    }
                </span>

            </td>


            {/* ==================================================
                AÇÕES
                ================================================== */}

            <td>

                <div className="users-actions">

                    {permissions.includes(
                        "Users:edit"
                    ) && (

                        <button
                            className="users-action-button"
                            onClick={() =>
                                onEditRoles(
                                    user
                                )
                            }
                        >
                            Editar Roles
                        </button>

                    )}


                    {permissions.includes(
                        "Users:edit"
                    ) && (

                        <button
                            className="users-action-button"
                            onClick={() =>
                                onChangePassword(
                                    user
                                )
                            }
                        >
                            Alterar senha
                        </button>

                    )}


                    {permissions.includes(
                        "Users:delete"
                    ) && (

                        <button
                            className="users-action-button users-action-danger"
                            onClick={() =>
                                onDelete(
                                    user.id
                                )
                            }
                        >
                            Excluir
                        </button>

                    )}


                    {permissions.includes(
                        "Users:edit"
                    ) && (

                        <button
                            className={
                                user.is_active === 1
                                    ? "users-action-button users-action-warning"
                                    : "users-action-button users-action-success"
                            }
                            onClick={() =>
                                onChangeStatus(
                                    user
                                )
                            }
                        >
                            {user.is_active === 1
                                ? "Desativar"
                                : "Ativar"
                            }
                        </button>

                    )}

                </div>

            </td>

        </tr>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default UserRow;
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
import { Button } from "../ui/Button";


// ============================================================
// PROPS
// ============================================================

interface UserRowProps {
    canEdit: boolean;

    canDelete: boolean;

    user:
        User;

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
    canEdit,
    canDelete,
    user,
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
                        Nenhum perfil
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

                    {canEdit && (

                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() =>
                                onEditRoles(
                                    user
                                )
                            }
                        >
                            Editar perfis
                        </Button>

                    )}


                    {canEdit && (

                        <Button
                            variant="secondary"
                            size="sm"
                            onClick={() =>
                                onChangePassword(
                                    user
                                )
                            }
                        >
                            Alterar senha
                        </Button>

                    )}


                    {canDelete && (

                        <Button
                            variant="danger"
                            size="sm"
                            onClick={() =>
                                onDelete(
                                    user.id
                                )
                            }
                        >
                            Excluir
                        </Button>

                    )}


                    {canEdit && (

                        <Button
                            variant={user.is_active === 1 ? "secondary" : "primary"}
                            size="sm"
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
                        </Button>

                    )}

                    {!canEdit && !canDelete && (
                        <span className="users-actions-readonly">Consulta</span>
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

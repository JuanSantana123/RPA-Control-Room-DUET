// ============================================================
// DUET CORE - USERS - TABLE
// ============================================================
//
// Painel principal da lista de usuários.
//
// Responsabilidade:
// - apresentar quantidade de usuários;
// - apresentar loading;
// - apresentar estado vazio;
// - renderizar UserRow;
// - encaminhar ações da tabela.
//
// Este componente NÃO:
// - carrega usuários;
// - executa chamadas HTTP;
// - altera Roles;
// - altera senha;
// - altera status diretamente.
// ============================================================

import UserRow
    from "./UserRow";

import { TableSkeleton }
    from "../ui/Skeletons";

import type {
    User,
} from "../../types/users";
import { UsersRound } from "lucide-react";
import EmptyState from "../ui/EmptyState";
import AccessModeBadge from "../ui/AccessModeBadge";


// ============================================================
// PROPS
// ============================================================

interface UsersTableProps {
    canEdit: boolean;

    canDelete: boolean;

    users:
        User[];

    loading:
        boolean;

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

function UsersTable({
    canEdit,
    canDelete,
    users,
    loading,
    onEditRoles,
    onChangePassword,
    onDelete,
    onChangeStatus,
}: UsersTableProps) {

    return (
        <section className="users-panel users-list-panel">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="users-panel-header">

                <div className="users-panel-heading">

                    <div className="users-panel-icon">
                        <UsersRound size={18} strokeWidth={1.8} aria-hidden="true" />
                    </div>

                    <div>

                        <h2>
                            Usuários cadastrados
                        </h2>

                        <p>
                            Usuários disponíveis no Control Room
                        </p>

                    </div>

                </div>


                <div className="users-panel-meta">
                    {!canEdit && !canDelete && <AccessModeBadge />}
                    <span className="users-panel-count">
                        {users.length}
                    </span>
                </div>

            </div>


            {/* ==================================================
                CONTEÚDO
                ================================================== */}

            {loading ? (
                <TableSkeleton rows={4} columns={5} />

            ) : users.length === 0 ? (

                <EmptyState
                    icon={<UsersRound />}
                    title="Nenhum usuário cadastrado"
                    description="As contas autorizadas a acessar o Control Room aparecerão aqui."
                />

            ) : (

                <div className="users-table-wrapper">

                    <table className="users-table">

                        <thead>

                            <tr>

                                <th>
                                    Usuário
                                </th>

                                <th>
                                    ID
                                </th>

                                <th>
                                    Perfis
                                </th>

                                <th>
                                    Situação
                                </th>

                                <th>
                                    Ações
                                </th>

                            </tr>

                        </thead>


                        <tbody>

                            {users.map(
                                (user) => (

                                    <UserRow
                                        canEdit={canEdit}
                                        canDelete={canDelete}
                                        key={user.id}
                                        user={user}
                                        onEditRoles={
                                            onEditRoles
                                        }
                                        onChangePassword={
                                            onChangePassword
                                        }
                                        onDelete={
                                            onDelete
                                        }
                                        onChangeStatus={
                                            onChangeStatus
                                        }
                                    />

                                )
                            )}

                        </tbody>

                    </table>

                </div>

            )}

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default UsersTable;

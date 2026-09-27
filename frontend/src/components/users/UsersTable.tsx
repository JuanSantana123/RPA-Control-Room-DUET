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
import { useMemo, useState } from "react";
import SearchField from "../ui/SearchField";
import PremiumSelect from "../ui/PremiumSelect";
import { Button } from "../ui/Button";
import PanelHeader from "../ui/PanelHeader";


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

    const [search, setSearch] = useState("");
    const [status, setStatus] = useState<"all" | "active" | "inactive">("all");
    const filteredUsers = useMemo(() => {
        const term = search.trim().toLocaleLowerCase("pt-BR");

        return users.filter((user) => {
            const matchesStatus = status === "all"
                || (status === "active" ? user.is_active === 1 : user.is_active !== 1);
            const matchesSearch = !term || [
                user.name,
                user.username,
                String(user.id),
                ...user.roles.map((role) => role.name),
            ].some((value) => value.toLocaleLowerCase("pt-BR").includes(term));

            return matchesStatus && matchesSearch;
        });
    }, [search, status, users]);
    const hasFilters = Boolean(search.trim()) || status !== "all";
    const clearFilters = () => {
        setSearch("");
        setStatus("all");
    };

    return (
        <section className="users-panel users-list-panel">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <PanelHeader
                icon={<UsersRound />}
                title="Usuários cadastrados"
                description="Usuários disponíveis no Control Room"
                actions={(
                    <div className="users-panel-meta">
                        {!canEdit && !canDelete && <AccessModeBadge />}
                        <span className="users-panel-count">
                            {hasFilters ? `${filteredUsers.length}/${users.length}` : users.length}
                        </span>
                    </div>
                )}
            />

            {users.length > 0 && (
                <div className="users-list-toolbar" aria-label="Filtros de usuários">
                    <SearchField
                        label="Pesquisar usuários"
                        value={search}
                        placeholder="Pesquisar por nome, usuário, ID ou perfil..."
                        onValueChange={setSearch}
                        containerClassName="users-list-search"
                    />
                    <PremiumSelect
                        value={status}
                        aria-label="Filtrar usuários por situação"
                        onChange={(event) => setStatus(event.target.value as "all" | "active" | "inactive")}
                    >
                        <option value="all">Todas as situações</option>
                        <option value="active">Ativos</option>
                        <option value="inactive">Inativos</option>
                    </PremiumSelect>
                    <Button size="sm" variant="ghost" disabled={!hasFilters} onClick={clearFilters}>
                        Limpar filtros
                    </Button>
                </div>
            )}


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

            ) : filteredUsers.length === 0 ? (

                <EmptyState
                    icon={<UsersRound />}
                    title="Nenhum usuário corresponde aos filtros"
                    description="Tente pesquisar outro nome, usuário ou perfil, ou limpe os filtros atuais."
                    action={<Button size="sm" onClick={clearFilters}>Limpar filtros</Button>}
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

                            {filteredUsers.map(
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

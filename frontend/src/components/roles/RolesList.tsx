// ============================================================
// DUET CORE - ROLES - LIST
// ============================================================
//
// Painel visual da coleção de Roles.
//
// Responsabilidade:
// - apresentar quantidade de Roles;
// - apresentar loading;
// - apresentar estado vazio;
// - renderizar RoleCard;
// - encaminhar configuração e exclusão.
//
// Este componente NÃO:
// - carrega Roles;
// - exclui Roles;
// - busca permissões;
// - executa chamadas HTTP.
// ============================================================

import RoleCard
    from "./RoleCard";

import { CardGridSkeleton }
    from "../ui/Skeletons";

import type {
    Role,
} from "../../types/roles";
import { UsersRound } from "lucide-react";
import EmptyState from "../ui/EmptyState";
import { useMemo, useState } from "react";
import { TextField } from "../ui/TextField";
import { Button } from "../ui/Button";


// ============================================================
// PROPS
// ============================================================

interface RolesListProps {
    roles: Role[];

    canEdit: boolean;

    canDelete: boolean;

    selectedRole:
        Role | null;

    loadingRoles: boolean;

    onConfigure:
        (role: Role) => void | Promise<void>;

    onDelete:
        (roleId: number) => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function RolesList({
    roles,
    canEdit,
    canDelete,
    selectedRole,
    loadingRoles,
    onConfigure,
    onDelete,
}: RolesListProps) {

    const [search, setSearch] = useState("");
    const filteredRoles = useMemo(() => {
        const term = search.trim().toLocaleLowerCase("pt-BR");
        if (!term) return roles;

        return roles.filter((role) => [role.name, role.description ?? "", String(role.id)]
            .some((value) => value.toLocaleLowerCase("pt-BR").includes(term)));
    }, [roles, search]);
    const hasFilter = Boolean(search.trim());

    return (
        <section className="roles-panel">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="roles-panel-header">

                <div className="roles-panel-title">

                    <h2>
                        Perfis cadastrados
                    </h2>

                    <span className="roles-panel-count">
                        {hasFilter ? `${filteredRoles.length}/${roles.length}` : roles.length}
                    </span>

                </div>

            </div>

            {roles.length > 0 && (
                <div className="roles-list-toolbar">
                    <TextField
                        label="Pesquisar perfis de acesso"
                        labelHidden
                        type="search"
                        value={search}
                        placeholder="Pesquisar por nome, descrição ou ID..."
                        onChange={(event) => setSearch(event.target.value)}
                    />
                    <Button size="sm" variant="ghost" disabled={!hasFilter} onClick={() => setSearch("")}>
                        Limpar
                    </Button>
                </div>
            )}


            {/* ==================================================
                CONTEÚDO
                ================================================== */}

            {loadingRoles ? (
                <CardGridSkeleton count={3} />

            ) : roles.length === 0 ? (

                <EmptyState
                    icon={<UsersRound />}
                    title="Nenhum perfil cadastrado"
                    description="Crie um perfil para organizar permissões e responsabilidades da equipe."
                />

            ) : filteredRoles.length === 0 ? (

                <EmptyState
                    icon={<UsersRound />}
                    title="Nenhum perfil corresponde à pesquisa"
                    description="Tente outro nome ou descrição, ou remova o filtro atual."
                    action={<Button size="sm" onClick={() => setSearch("")}>Limpar pesquisa</Button>}
                />

            ) : (

                <div className="roles-list">

                    {filteredRoles.map(
                        (role) => (

                            <RoleCard
                                canEdit={canEdit}
                                canDelete={canDelete}
                                key={role.id}
                                role={role}
                                selected={
                                    selectedRole?.id ===
                                    role.id
                                }
                                onConfigure={
                                    onConfigure
                                }
                                onDelete={
                                    onDelete
                                }
                            />

                        )
                    )}

                </div>

            )}

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default RolesList;

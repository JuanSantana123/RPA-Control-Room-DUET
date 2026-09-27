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
                        {roles.length}
                    </span>

                </div>

            </div>


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

            ) : (

                <div className="roles-list">

                    {roles.map(
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

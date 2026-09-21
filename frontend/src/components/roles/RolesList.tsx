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

import type {
    Role,
} from "../../types/roles";


// ============================================================
// PROPS
// ============================================================

interface RolesListProps {
    roles: Role[];

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

                <div className="roles-empty-state">

                    <div className="roles-empty-icon">
                        ⏳
                    </div>

                    Carregando Roles...

                </div>

            ) : roles.length === 0 ? (

                <div className="roles-empty-state">

                    <div className="roles-empty-icon">
                        👥
                    </div>

                    Nenhuma Role cadastrada.

                </div>

            ) : (

                <div className="roles-list">

                    {roles.map(
                        (role) => (

                            <RoleCard
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
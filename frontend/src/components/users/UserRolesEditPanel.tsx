// ============================================================
// DUET CORE - USERS - ROLE EDIT PANEL
// ============================================================
//
// Painel visual para alteração das Roles de um usuário.
//
// Responsabilidade:
// - apresentar as Roles disponíveis;
// - indicar as Roles atualmente selecionadas;
// - encaminhar marcação/desmarcação;
// - permitir salvar ou cancelar.
//
// Este componente NÃO:
// - executa PUT;
// - busca usuários;
// - carrega Roles;
// - controla mensagens globais.
//
// A persistência pertence ao hook useUserRoles.
// ============================================================

import type {
    UserAvailableRole,
} from "../../types/users";


// ============================================================
// PROPS
// ============================================================

interface UserRolesEditPanelProps {
    roles:
        UserAvailableRole[];

    editingRoleIds:
        number[];

    onToggleRole:
        (roleId: number) => void;

    onCancel:
        () => void;

    onSave:
        () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function UserRolesEditPanel({
    roles,
    editingRoleIds,
    onToggleRole,
    onCancel,
    onSave,
}: UserRolesEditPanelProps) {

    return (
        <section className="users-panel users-edit-panel">

            <div className="users-panel-header">

                <div className="users-panel-heading">

                    <div className="users-panel-icon">
                        🔐
                    </div>

                    <div>

                        <h2>
                            Editar Roles do usuário
                        </h2>

                        <p>
                            Atualize os perfis de acesso associados
                        </p>

                    </div>

                </div>

            </div>


            <div className="users-edit-content">

                <p className="users-edit-description">
                    Selecione as Roles que este usuário deverá possuir.
                </p>


                <div className="users-role-selection">

                    {roles.map(
                        (role) => (

                            <label
                                key={role.id}
                                className="users-role-option"
                            >

                                <input
                                    type="checkbox"
                                    checked={
                                        editingRoleIds.includes(
                                            role.id
                                        )
                                    }
                                    onChange={() =>
                                        onToggleRole(
                                            role.id
                                        )
                                    }
                                />

                                <span>
                                    {role.name}
                                </span>

                            </label>

                        )
                    )}

                </div>


                <div className="users-edit-actions">

                    <button
                        className="users-secondary-button"
                        onClick={onCancel}
                    >
                        Cancelar
                    </button>

                    <button
                        className="users-primary-button"
                        onClick={onSave}
                    >
                        Salvar Roles
                    </button>

                </div>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default UserRolesEditPanel;
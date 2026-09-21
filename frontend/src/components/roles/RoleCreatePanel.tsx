// ============================================================
// DUET CORE - ROLES - CREATE PANEL
// ============================================================
//
// Formulário visual de criação de uma Role.
//
// Responsabilidade:
// - apresentar nome e descrição;
// - refletir o estado atual do formulário;
// - encaminhar alterações dos campos;
// - encaminhar criação e cancelamento.
//
// Este componente NÃO:
// - chama POST /roles;
// - valida regras de criação;
// - altera diretamente a coleção de Roles;
// - controla mensagens globais.
//
// Essas responsabilidades pertencem a useRolesData.
// ============================================================


// ============================================================
// PROPS
// ============================================================

interface RoleCreatePanelProps {
    roleName: string;

    setRoleName:
        (value: string) => void;

    roleDescription: string;

    setRoleDescription:
        (value: string) => void;

    creatingRole: boolean;

    onCancel:
        () => void;

    onCreate:
        () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function RoleCreatePanel({
    roleName,
    setRoleName,
    roleDescription,
    setRoleDescription,
    creatingRole,
    onCancel,
    onCreate,
}: RoleCreatePanelProps) {

    return (
        <section className="roles-create-panel">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="roles-create-header">

                <div className="roles-create-icon">
                    👤
                </div>


                <div>

                    <h2>
                        Criar nova Role
                    </h2>

                    <p>
                        Defina um nome e uma descrição para o novo perfil.
                    </p>

                </div>

            </div>


            {/* ==================================================
                CAMPOS
                ================================================== */}

            <div className="roles-create-fields">

                <div className="roles-field-group">

                    <label>
                        Nome da Role
                    </label>

                    <input
                        type="text"
                        placeholder="Ex.: Administrador"
                        value={roleName}
                        disabled={creatingRole}
                        onChange={(event) =>
                            setRoleName(
                                event.target.value
                            )
                        }
                    />

                </div>


                <div className="roles-field-group">

                    <label>
                        Descrição
                    </label>

                    <input
                        type="text"
                        placeholder="Descreva a finalidade deste perfil"
                        value={roleDescription}
                        disabled={creatingRole}
                        onChange={(event) =>
                            setRoleDescription(
                                event.target.value
                            )
                        }
                    />

                </div>

            </div>


            {/* ==================================================
                AÇÕES
                ================================================== */}

            <div className="roles-create-actions">

                <button
                    className="roles-secondary-button"
                    onClick={onCancel}
                    disabled={creatingRole}
                >
                    Cancelar
                </button>


                <button
                    className="roles-primary-button"
                    onClick={onCreate}
                    disabled={creatingRole}
                >
                    {creatingRole
                        ? "Criando..."
                        : "Criar Role"
                    }
                </button>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default RoleCreatePanel;
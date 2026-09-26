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

import { UserRound } from "lucide-react";
import { Button } from "../ui/Button";
import { TextField } from "../ui/TextField";


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
                    <UserRound size={18} strokeWidth={1.8} aria-hidden="true" />
                </div>


                <div>

                    <h2>
                        Criar novo perfil
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

                <TextField
                        id="new-role-name"
                        label="Nome do perfil"
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


                <TextField
                        id="new-role-description"
                        label="Descrição"
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


            {/* ==================================================
                AÇÕES
                ================================================== */}

            <div className="roles-create-actions">

                <Button
                    onClick={onCancel}
                    disabled={creatingRole}
                >
                    Cancelar
                </Button>


                <Button
                    variant="primary"
                    onClick={onCreate}
                    busy={creatingRole}
                    loadingLabel="Criando perfil"
                >
                    Criar perfil
                </Button>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default RoleCreatePanel;

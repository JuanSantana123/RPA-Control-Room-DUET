// ============================================================
// DUET CORE - ROLES - ROLE CARD
// ============================================================
//
// Representação visual de uma Role na lista.
//
// Responsabilidade:
// - apresentar nome e descrição;
// - indicar visualmente a Role selecionada;
// - disponibilizar configuração;
// - disponibilizar exclusão.
//
// Este componente NÃO:
// - seleciona permissões diretamente;
// - exclui Roles diretamente;
// - executa chamadas HTTP;
// - controla estado global.
//
// As operações são recebidas através de callbacks.
// ============================================================

import type {
    Role,
} from "../../types/roles";
import { UserRound } from "lucide-react";
import { Button } from "../ui/Button";


// ============================================================
// PROPS
// ============================================================

interface RoleCardProps {
    role: Role;

    canEdit: boolean;

    canDelete: boolean;

    selected: boolean;

    onConfigure:
        (role: Role) => void | Promise<void>;

    onDelete:
        (roleId: number) => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function RoleCard({
    role,
    canEdit,
    canDelete,
    selected,
    onConfigure,
    onDelete,
}: RoleCardProps) {

    return (
        <div
            className={`role-card ${
                selected
                    ? "role-card-selected"
                    : ""
            }`}
        >

            {/* ==================================================
                INFORMAÇÕES
                ================================================== */}

            <div className="role-card-info">

                <h3 className="role-card-title">
                    <span className="role-card-title-icon">
                        <UserRound size={16} strokeWidth={1.8} aria-hidden="true" />
                    </span>
                    {role.name}
                </h3>

                <p className="role-card-description">
                    {role.description ||
                        "Sem descrição cadastrada"}
                </p>

            </div>


            {/* ==================================================
                AÇÕES
                ================================================== */}

            <div className="role-card-actions">

                <Button
                    size="sm"
                    className="role-card-configure"
                    onClick={() =>
                        onConfigure(role)
                    }
                >
                    {canEdit ? "Configurar" : "Consultar"}
                </Button>

                {canDelete && <Button
                    size="sm"
                    variant="danger"
                    onClick={() =>
                        onDelete(role.id)
                    }
                >
                    Excluir
                </Button>}

            </div>

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default RoleCard;

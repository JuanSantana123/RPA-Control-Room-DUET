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


// ============================================================
// PROPS
// ============================================================

interface RoleCardProps {
    role: Role;

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

                <button
                    className="role-card-configure"
                    onClick={() =>
                        onConfigure(role)
                    }
                >
                    Configurar
                </button>


                <button
                    className="roles-danger-button"
                    onClick={() =>
                        onDelete(role.id)
                    }
                >
                    Excluir
                </button>

            </div>

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default RoleCard;
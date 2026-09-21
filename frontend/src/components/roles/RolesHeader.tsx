// ============================================================
// DUET CORE - ROLES - HEADER
// ============================================================
//
// Cabeçalho visual da área de Roles.
//
// Responsabilidade:
// - apresentar identificação da área;
// - apresentar título e descrição;
// - disponibilizar a criação de uma nova Role.
//
// O formulário só pode ser aberto pelo cabeçalho quando ele
// ainda não estiver sendo exibido.
//
// Este componente NÃO:
// - cria Roles;
// - executa chamadas HTTP;
// - controla o formulário;
// - gerencia permissões.
// ============================================================


// ============================================================
// PROPS
// ============================================================

interface RolesHeaderProps {
    showCreateForm: boolean;

    onCreate:
        () => void;
}


// ============================================================
// COMPONENTE
// ============================================================

function RolesHeader({
    showCreateForm,
    onCreate,
}: RolesHeaderProps) {

    return (
        <div className="roles-page-header">

            <div>

                <p className="roles-eyebrow">
                    ACCESS CONTROL
                </p>

                <h1>
                    Roles
                </h1>

                <p>
                    Gerencie os perfis de acesso e suas permissões.
                </p>

            </div>


            {!showCreateForm && (

                <button
                    className="roles-primary-button"
                    onClick={onCreate}
                >
                    + Nova Role
                </button>

            )}

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default RolesHeader;
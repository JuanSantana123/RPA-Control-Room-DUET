// ============================================================

import { ShieldPlus } from "lucide-react";
import { Button } from "../ui/Button";
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
        <header className="page-heading roles-page-header">

            <div>

                <p className="page-eyebrow roles-eyebrow">
                    CONTROLE DE ACESSO
                </p>

                <h1>
                    Perfis de acesso
                </h1>

                <p>
                    Gerencie os perfis de acesso e suas permissões.
                </p>

            </div>


            {!showCreateForm && (

                <Button
                    variant="primary"
                    onClick={onCreate}
                >
                    <ShieldPlus size={17} strokeWidth={1.9} aria-hidden="true" />
                    Novo perfil
                </Button>

            )}

        </header>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default RolesHeader;

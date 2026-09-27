// ============================================================

import { ShieldPlus } from "lucide-react";
import { Button } from "../ui/Button";
import AccessModeBadge from "../ui/AccessModeBadge";
import PageHeader from "../ui/PageHeader";
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
    canCreate: boolean;
    readOnly: boolean;
    showCreateForm: boolean;

    onCreate:
        () => void;
}


// ============================================================
// COMPONENTE
// ============================================================

function RolesHeader({
    canCreate,
    readOnly,
    showCreateForm,
    onCreate,
}: RolesHeaderProps) {

    const actions = <>
        {readOnly && <AccessModeBadge />}
        {canCreate && !showCreateForm && <Button
                    variant="primary"
                    onClick={onCreate}
                >
                    <ShieldPlus size={17} strokeWidth={1.9} aria-hidden="true" />
                    Novo perfil
                </Button>}
    </>;

    return <PageHeader eyebrow="CONTROLE DE ACESSO" title="Perfis de acesso" description="Defina responsabilidades e permissões com clareza e rastreabilidade." actions={actions} />;
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default RolesHeader;

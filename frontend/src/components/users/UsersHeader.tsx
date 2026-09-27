// ============================================================
// DUET CORE - USERS - HEADER
// ============================================================
//
// Cabeçalho visual da área de gerenciamento de usuários.
//
// Responsabilidade:
// - identificar a área USER MANAGEMENT;
// - apresentar título;
// - apresentar descrição.
//
// Este componente NÃO:
// - possui estado;
// - executa chamadas HTTP;
// - controla permissões;
// - implementa ações de usuário.
// ============================================================


import AccessModeBadge from "../ui/AccessModeBadge";
import PageHeader from "../ui/PageHeader";

// ============================================================
// COMPONENTE
// ============================================================

function UsersHeader({ readOnly }: { readOnly: boolean }) {

    return <PageHeader eyebrow="GESTÃO DE USUÁRIOS" title="Usuários" description="Gerencie contas, perfis de acesso e credenciais de autenticação." actions={readOnly ? <AccessModeBadge /> : undefined} />;
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default UsersHeader;

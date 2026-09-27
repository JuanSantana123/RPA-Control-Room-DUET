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

// ============================================================
// COMPONENTE
// ============================================================

function UsersHeader({ readOnly }: { readOnly: boolean }) {

    return (
        <header className="page-heading users-page-header">

            <div>

                <p className="page-eyebrow users-page-eyebrow">
                    GESTÃO DE USUÁRIOS
                </p>

                <h1>
                    Usuários
                </h1>

                <p>
                    Gerencie usuários, perfis de acesso e credenciais.
                </p>

            </div>

            {readOnly && <AccessModeBadge />}

        </header>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default UsersHeader;

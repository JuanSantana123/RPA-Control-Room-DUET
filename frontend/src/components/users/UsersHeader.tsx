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


// ============================================================
// COMPONENTE
// ============================================================

function UsersHeader() {

    return (
        <div className="users-page-header">

            <div>

                <p className="users-page-eyebrow">
                    USER MANAGEMENT
                </p>

                <h1>
                    Usuários
                </h1>

                <p>
                    Gerencie usuários, perfis de acesso e credenciais.
                </p>

            </div>

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default UsersHeader;
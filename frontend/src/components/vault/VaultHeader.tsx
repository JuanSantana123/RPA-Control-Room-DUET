// ============================================================
// DUET CORE - VAULT - HEADER
// ============================================================
//
// Cabeçalho principal do Credential Vault.
//
// Responsabilidade:
// - apresentar identificação da área;
// - apresentar título e descrição;
// - disponibilizar a ação de criação de nova pasta.
//
// Este componente NÃO:
// - controla formulário;
// - executa chamadas HTTP;
// - conhece a árvore de pastas.
// ============================================================


// ============================================================
// PROPS
// ============================================================

interface VaultHeaderProps {
    onNewFolder:
        () => void;
}


// ============================================================
// COMPONENTE
// ============================================================

function VaultHeader({
    onNewFolder,
}: VaultHeaderProps) {

    return (
        <section className="page-heading">

            <div>

                <div className="page-eyebrow">
                    CREDENTIAL VAULT
                </div>

                <h1>
                    Vault
                </h1>

                <p>
                    Gerenciamento de credenciais.
                </p>

            </div>


            <button
                type="button"
                className="primary-button"
                onClick={onNewFolder}
            >
                + Nova pasta
            </button>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default VaultHeader;
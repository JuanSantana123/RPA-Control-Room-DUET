// ============================================================
// DUET CORE - VAULT CREDENTIAL TABS
// ============================================================
//
// Componente visual responsável EXCLUSIVAMENTE por alternar
// entre os dois contextos de credenciais do Vault:
//
// - Credenciais de Automação;
// - Credenciais de Dispositivo.
//
// RESPONSABILIDADE DESTE COMPONENTE:
//
// - renderizar as abas;
// - indicar visualmente qual aba está ativa;
// - comunicar a alteração para a página Vault.
//
// ESTE COMPONENTE NÃO:
//
// - executa chamadas HTTP;
// - carrega credenciais;
// - altera pastas;
// - cria/edita/exclui credenciais;
// - manipula segredos;
// - conhece regras de RBAC.
//
// A página Vault.tsx continua responsável por coordenar
// qual conteúdo deve ser exibido em cada aba.
// ============================================================


// ============================================================
// TIPOS
// ============================================================

export type VaultCredentialSection =
    | "automation"
    | "device";


type VaultCredentialTabsProps = {

    // Seção atualmente selecionada pela página.
    activeSection: VaultCredentialSection;

    // Callback disparado quando o usuário troca de aba.
    onChange: (
        section: VaultCredentialSection
    ) => void;
};


// ============================================================
// COMPONENTE
// ============================================================

function VaultCredentialTabs({
    activeSection,
    onChange,
}: VaultCredentialTabsProps) {

    return (

        <div
            className="vault-credential-tabs"
            role="tablist"
            aria-label="Tipos de credenciais do Vault"
        >

            {/* ==================================================
                CREDENCIAIS DE AUTOMAÇÃO
                ================================================== */}

            <button
                type="button"
                role="tab"
                id="vault-tab-automation"
                aria-selected={
                    activeSection === "automation"
                }
                aria-controls="vault-panel-automation"
                className={[
                    "vault-credential-tab",
                    activeSection === "automation"
                        ? "is-active"
                        : "",
                ]
                    .filter(Boolean)
                    .join(" ")}
                onClick={
                    () => onChange(
                        "automation"
                    )
                }
            >

                <span className="vault-credential-tab-title">
                    Credenciais de Automação
                </span>

                <span className="vault-credential-tab-description">
                    Segredos utilizados por robôs, sistemas e integrações
                </span>

            </button>


            {/* ==================================================
                CREDENCIAIS DE DISPOSITIVO
                ================================================== */}

            <button
                type="button"
                role="tab"
                id="vault-tab-device"
                aria-selected={
                    activeSection === "device"
                }
                aria-controls="vault-panel-device"
                className={[
                    "vault-credential-tab",
                    activeSection === "device"
                        ? "is-active"
                        : "",
                ]
                    .filter(Boolean)
                    .join(" ")}
                onClick={
                    () => onChange(
                        "device"
                    )
                }
            >

                <span className="vault-credential-tab-title">
                    Credenciais de Dispositivo
                </span>

                <span className="vault-credential-tab-description">
                    Identidades Windows utilizadas pelos Devices
                </span>

            </button>

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default VaultCredentialTabs;

// ============================================================

import { FolderPlus } from "lucide-react";
import { Button } from "../ui/Button";
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
    canCreateFolders: boolean;
    onNewFolder:
        () => void;
}


// ============================================================
// COMPONENTE
// ============================================================

function VaultHeader({
    canCreateFolders,
    onNewFolder,
}: VaultHeaderProps) {

    return (
        <section className="page-heading">

            <div>

                <div className="page-eyebrow">
                    GESTÃO DE CREDENCIAIS
                </div>

                <h1>
                    Vault
                </h1>

                <p>
                    Gerenciamento de credenciais.
                </p>

            </div>


            {canCreateFolders && (
                <Button onClick={onNewFolder}>
                    <FolderPlus size={17} strokeWidth={1.9} aria-hidden="true" />
                    Nova pasta
                </Button>
            )}

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default VaultHeader;

// ============================================================

import { FolderPlus } from "lucide-react";
import { Button } from "../ui/Button";
import PageHeader from "../ui/PageHeader";
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

    return <PageHeader
        eyebrow="GESTÃO DE CREDENCIAIS"
        title="Vault"
        description="Organize credenciais protegidas para pessoas, robôs e Devices."
        actions={canCreateFolders ? <Button onClick={onNewFolder}>
                    <FolderPlus size={17} strokeWidth={1.9} aria-hidden="true" />
                    Nova pasta
                </Button> : undefined}
    />;
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default VaultHeader;

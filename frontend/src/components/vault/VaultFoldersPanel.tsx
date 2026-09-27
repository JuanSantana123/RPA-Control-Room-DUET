// ============================================================
// DUET CORE - VAULT - FOLDERS PANEL
// ============================================================
//
// Painel da árvore de pastas do Credential Vault.
//
// Responsabilidade:
// - apresentar loading;
// - apresentar estado vazio;
// - renderizar os nós raiz;
// - encaminhar ações aos VaultFolderNode.
//
// Este componente NÃO:
// - carrega pastas;
// - modifica estado do backend;
// - implementa CRUD.
// ============================================================

import VaultFolderNode
    from "./VaultFolderNode";

import { CardGridSkeleton }
    from "../ui/Skeletons";

import type {
    VaultFolder,
} from "../../types/vault";
import { FolderOpen } from "lucide-react";
import EmptyState from "../ui/EmptyState";
import AccessModeBadge from "../ui/AccessModeBadge";
import PanelHeader from "../ui/PanelHeader";


// ============================================================
// PROPS
// ============================================================

interface VaultFoldersPanelProps {
    folders:
        VaultFolder[];

    selectedFolder:
        VaultFolder | null;

    loading:
        boolean;

    canCreate: boolean;
    canDelete: boolean;

    onSelect:
        (folder: VaultFolder) => void;

    onNewSubfolder:
        (folder: VaultFolder) => void;

    onDelete:
        (folder: VaultFolder) =>
            void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function VaultFoldersPanel({
    folders,
    selectedFolder,
    loading,
    canCreate,
    canDelete,
    onSelect,
    onNewSubfolder,
    onDelete,
}: VaultFoldersPanelProps) {

    return (
        <section className="content-panel vault-panel vault-folders-panel">

            <PanelHeader
                icon={<FolderOpen />}
                title="Pastas"
                description="Organize credenciais por contexto de automação."
                actions={!canCreate && !canDelete ? <AccessModeBadge /> : undefined}
            />


            {loading ? (
                <CardGridSkeleton count={2} />

            ) : folders.length === 0 ? (

                <EmptyState
                    compact
                    icon={<FolderOpen />}
                    title="Nenhuma pasta cadastrada"
                    description="Crie uma pasta para organizar credenciais por processo ou equipe."
                />

            ) : (

                <div className="vault-folder-list">

                    {folders.map(
                        (folder) => (

                            <VaultFolderNode
                                key={folder.id}
                                folder={folder}
                                selectedFolder={
                                    selectedFolder
                                }
                                canCreate={canCreate}
                                canDelete={canDelete}
                                onSelect={
                                    onSelect
                                }
                                onNewSubfolder={
                                    onNewSubfolder
                                }
                                onDelete={
                                    onDelete
                                }
                            />

                        )
                    )}

                </div>

            )}

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default VaultFoldersPanel;

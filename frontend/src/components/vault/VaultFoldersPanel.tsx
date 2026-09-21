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

import type {
    VaultFolder,
} from "../../types/vault";


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
    onSelect,
    onNewSubfolder,
    onDelete,
}: VaultFoldersPanelProps) {

    return (
        <section className="content-panel vault-panel vault-folders-panel">

            <div className="vault-panel-header">

                <h2>
                    Pastas
                </h2>

            </div>


            {loading ? (

                <p>
                    Carregando pastas...
                </p>

            ) : folders.length === 0 ? (

                <p className="vault-empty-state">
                    Nenhuma pasta cadastrada.
                </p>

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
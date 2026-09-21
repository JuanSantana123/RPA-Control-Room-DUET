// ============================================================
// DUET CORE - VAULT - FOLDER NODE
// ============================================================
//
// Representa um nó da árvore hierárquica do Vault.
//
// Responsabilidade:
// - apresentar uma pasta;
// - permitir seleção;
// - permitir criação de subpasta;
// - permitir exclusão;
// - renderizar recursivamente seus filhos.
//
// Este componente NÃO:
// - executa chamadas HTTP;
// - mantém a pasta selecionada;
// - cria ou exclui pastas diretamente.
// ============================================================

import type {
    VaultFolder,
} from "../../types/vault";


// ============================================================
// PROPS
// ============================================================

interface VaultFolderNodeProps {
    folder:
        VaultFolder;

    selectedFolder:
        VaultFolder | null;

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

function VaultFolderNode({
    folder,
    selectedFolder,
    onSelect,
    onNewSubfolder,
    onDelete,
}: VaultFolderNodeProps) {

    return (
        <div className="vault-folder-item">

            {/* ==================================================
                LINHA DA PASTA
                ================================================== */}

            <div className="vault-folder-row">

                <button
                    type="button"
                    onClick={() =>
                        onSelect(
                            folder
                        )
                    }
                    className={
                        `vault-folder-select-button ${
                            selectedFolder?.id ===
                            folder.id
                                ? "selected"
                                : ""
                        }`
                    }
                >
                    📁 {folder.name}
                </button>


                <button
                    type="button"
                    className="vault-folder-action-button"
                    onClick={() =>
                        onNewSubfolder(
                            folder
                        )
                    }
                >
                    + Subpasta
                </button>


                <button
                    type="button"
                    className="vault-folder-action-button"
                    onClick={() =>
                        onDelete(
                            folder
                        )
                    }
                >
                    Excluir
                </button>

            </div>


            {/* ==================================================
                SUBPASTAS
                ================================================== */}

            {folder.children &&
                folder.children.length > 0 && (

                    <>
                        {folder.children.map(
                            (childFolder) => (

                                <VaultFolderNode
                                    key={
                                        childFolder.id
                                    }
                                    folder={
                                        childFolder
                                    }
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
                    </>

                )}

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default VaultFolderNode;
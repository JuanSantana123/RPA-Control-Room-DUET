// ============================================================
// DUET CORE - VAULT - FOLDER CREATE PANEL
// ============================================================
//
// Formulário visual para criação de pastas do Vault.
//
// Responsabilidade:
// - receber nome da nova pasta;
// - permitir seleção da pasta pai;
// - renderizar hierarquicamente todas as pastas existentes;
// - encaminhar criação;
// - encaminhar cancelamento.
//
// Este componente NÃO:
// - executa POST;
// - carrega pastas;
// - controla mensagens globais.
// ============================================================

import type {
    ReactElement,
} from "react";

import type {
    VaultFolder,
} from "../../types/vault";


// ============================================================
// PROPS
// ============================================================

interface VaultFolderCreatePanelProps {
    folders:
        VaultFolder[];

    newFolderName:
        string;

    setNewFolderName:
        (value: string) => void;

    newFolderParentId:
        number | null;

    setNewFolderParentId:
        (value: number | null) => void;

    creatingFolder:
        boolean;

    onCreate:
        () => void | Promise<void>;

    onCancel:
        () => void;
}


// ============================================================
// COMPONENTE
// ============================================================

function VaultFolderCreatePanel({
    folders,
    newFolderName,
    setNewFolderName,
    newFolderParentId,
    setNewFolderParentId,
    creatingFolder,
    onCreate,
    onCancel,
}: VaultFolderCreatePanelProps) {

    // ========================================================
    // OPÇÕES HIERÁRQUICAS
    // ========================================================

    const renderizarOpcoesPastas =
        (
            listaPastas: VaultFolder[],
            nivel: number = 0
        ): ReactElement[] => {

            const opcoes:
                ReactElement[] = [];


            listaPastas.forEach(
                (folder) => {

                    opcoes.push(
                        <option
                            key={folder.id}
                            value={folder.id}
                        >
                            {"— ".repeat(nivel)}
                            📁 {folder.name}
                        </option>
                    );


                    if (
                        folder.children &&
                        folder.children.length > 0
                    ) {

                        opcoes.push(
                            ...renderizarOpcoesPastas(
                                folder.children,
                                nivel + 1
                            )
                        );
                    }
                }
            );


            return opcoes;
        };


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <section className="content-panel vault-form-panel vault-create-folder-panel">

            <h2>
                Nova pasta
            </h2>


            <input
                type="text"
                className="form-input"
                placeholder="Nome da pasta"
                value={newFolderName}
                disabled={creatingFolder}
                onChange={(event) =>
                    setNewFolderName(
                        event.target.value
                    )
                }
            />


            <select
                className="form-input"
                value={
                    newFolderParentId === null
                        ? ""
                        : newFolderParentId
                }
                disabled={creatingFolder}
                onChange={(event) => {

                    const value =
                        event.target.value;

                    setNewFolderParentId(
                        value === ""
                            ? null
                            : Number(value)
                    );
                }}
            >

                <option value="">
                    Raiz do Vault
                </option>

                {renderizarOpcoesPastas(
                    folders
                )}

            </select>


            <button
                type="button"
                className="primary-button"
                onClick={onCreate}
                disabled={creatingFolder}
            >
                {creatingFolder
                    ? "Criando..."
                    : "Criar pasta"
                }
            </button>


            <button
                type="button"
                className="secondary-button"
                onClick={onCancel}
                disabled={creatingFolder}
            >
                Cancelar
            </button>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default VaultFolderCreatePanel;
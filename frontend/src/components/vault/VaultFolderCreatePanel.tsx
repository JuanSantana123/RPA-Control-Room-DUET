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
import PremiumSelect from "../ui/PremiumSelect";
import { Button } from "../ui/Button";
import { Folder } from "lucide-react";


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
                            {folder.name}
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
                <Folder size={18} strokeWidth={1.8} aria-hidden="true" />
                Nova pasta
            </h2>


            <input
                id="vault-new-folder-name"
                type="text"
                aria-label="Nome da nova pasta"
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


            <PremiumSelect
                id="vault-new-folder-parent"
                aria-label="Pasta superior"
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

            </PremiumSelect>


            <Button
                onClick={onCreate}
                busy={creatingFolder}
                loadingLabel="Criando pasta"
            >
                Criar pasta
            </Button>


            <Button
                variant="secondary"
                onClick={onCancel}
                disabled={creatingFolder}
            >
                Cancelar
            </Button>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default VaultFolderCreatePanel;

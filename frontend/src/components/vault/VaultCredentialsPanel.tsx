// ============================================================
// DUET CORE - VAULT - CREDENTIALS PANEL
// ============================================================
//
// Painel principal das credenciais da pasta selecionada.
//
// Responsabilidade:
// - identificar a pasta atual;
// - controlar visualmente disponibilidade de "Nova credencial";
// - renderizar formulário de criação;
// - renderizar formulário de edição;
// - apresentar loading / vazio / lista;
// - compor VaultCredentialCard.
//
// REGRA EXISTENTE:
// O botão "Nova credencial" somente aparece quando existe uma
// pasta selecionada e ela NÃO é uma pasta raiz.
//
// selectedFolder.parent_id !== null
//
// Este componente NÃO:
// - executa HTTP;
// - implementa validações;
// - controla segredos;
// - persiste alterações.
// ============================================================

import VaultCredentialCard
    from "./VaultCredentialCard";

import VaultCredentialCreateForm
    from "./VaultCredentialCreateForm";

import VaultCredentialEditForm
    from "./VaultCredentialEditForm";

import type {
    EditCredentialField,
    NewCredentialField,
    VaultCredential,
    VaultFolder,
} from "../../types/vault";


// ============================================================
// PROPS
// ============================================================

interface VaultCredentialsPanelProps {
    selectedFolder:
        VaultFolder | null;

    credentials:
        VaultCredential[];

    loadingCredentials:
        boolean;


    // --------------------------------------------------------
    // CRIAÇÃO
    // --------------------------------------------------------

    showNewCredentialForm:
        boolean;

    newCredentialName:
        string;

    setNewCredentialName:
        (value: string) => void;

    newCredentialFields:
        NewCredentialField[];

    creatingCredential:
        boolean;

    onOpenCreate:
        () => void;

    onUpdateCreateField:
        (
            index: number,
            property:
                keyof NewCredentialField,
            value:
                string | boolean
        ) => void;

    onAddCreateField:
        () => void;

    onRemoveCreateField:
        (index: number) => void;

    onSaveCreate:
        () => void | Promise<void>;

    onCancelCreate:
        () => void;


    // --------------------------------------------------------
    // EDIÇÃO
    // --------------------------------------------------------

    editingCredential:
        VaultCredential | null;

    editCredentialFields:
        EditCredentialField[];

    updatingCredential:
        boolean;

    onEdit:
        (credential: VaultCredential) =>
            void;

    onUpdateEditField:
        (
            index: number,
            property:
                keyof EditCredentialField,
            value:
                string | boolean
        ) => void;

    onAddEditField:
        () => void;

    onRemoveEditField:
        (index: number) => void;

    onSaveEdit:
        () => void | Promise<void>;

    onCancelEdit:
        () => void;


    // --------------------------------------------------------
    // EXCLUSÃO
    // --------------------------------------------------------

    onDelete:
        (credential: VaultCredential) =>
            void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function VaultCredentialsPanel({
    selectedFolder,
    credentials,
    loadingCredentials,

    showNewCredentialForm,
    newCredentialName,
    setNewCredentialName,
    newCredentialFields,
    creatingCredential,
    onOpenCreate,
    onUpdateCreateField,
    onAddCreateField,
    onRemoveCreateField,
    onSaveCreate,
    onCancelCreate,

    editingCredential,
    editCredentialFields,
    updatingCredential,
    onEdit,
    onUpdateEditField,
    onAddEditField,
    onRemoveEditField,
    onSaveEdit,
    onCancelEdit,

    onDelete,
}: VaultCredentialsPanelProps) {

    return (
        <section className="vault-credentials-panel">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="vault-panel-header">

                <h2>
                    {selectedFolder
                        ? `Credenciais — ${selectedFolder.name}`
                        : "Credenciais"
                    }
                </h2>


                {selectedFolder &&
                    selectedFolder.parent_id !==
                        null && (

                        <button
                            type="button"
                            className="primary-button"
                            onClick={
                                onOpenCreate
                            }
                        >
                            + Nova credencial
                        </button>

                    )}

            </div>


            {/* ==================================================
                CRIAÇÃO
                ================================================== */}

            {showNewCredentialForm && (

                <VaultCredentialCreateForm
                    name={
                        newCredentialName
                    }
                    setName={
                        setNewCredentialName
                    }
                    fields={
                        newCredentialFields
                    }
                    creating={
                        creatingCredential
                    }
                    onUpdateField={
                        onUpdateCreateField
                    }
                    onAddField={
                        onAddCreateField
                    }
                    onRemoveField={
                        onRemoveCreateField
                    }
                    onSave={
                        onSaveCreate
                    }
                    onCancel={
                        onCancelCreate
                    }
                />

            )}


            {/* ==================================================
                EDIÇÃO
                ================================================== */}

            {editingCredential && (

                <VaultCredentialEditForm
                    credential={
                        editingCredential
                    }
                    fields={
                        editCredentialFields
                    }
                    updating={
                        updatingCredential
                    }
                    onUpdateField={
                        onUpdateEditField
                    }
                    onAddField={
                        onAddEditField
                    }
                    onRemoveField={
                        onRemoveEditField
                    }
                    onSave={
                        onSaveEdit
                    }
                    onCancel={
                        onCancelEdit
                    }
                />

            )}


            {/* ==================================================
                LISTA
                ================================================== */}

            {!selectedFolder ? (

                <p className="vault-empty-state">
                    Selecione uma pasta para visualizar suas credenciais.
                </p>

            ) : loadingCredentials ? (

                <p>
                    Carregando credenciais...
                </p>

            ) : credentials.length === 0 ? (

                <p className="vault-empty-state">
                    Nenhuma credencial cadastrada nesta pasta.
                </p>

            ) : (

                <div className="vault-credentials-list">

                    {credentials.map(
                        (credential) => (

                            <VaultCredentialCard
                                key={
                                    credential.id
                                }
                                credential={
                                    credential
                                }
                                onEdit={
                                    onEdit
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

export default VaultCredentialsPanel;
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

import { CardGridSkeleton }
    from "../ui/Skeletons";
import { KeyRound, MousePointer2, RefreshCw, Search, X } from "lucide-react";
import { Button, IconButton } from "../ui/Button";
import EmptyState from "../ui/EmptyState";
import { TextField } from "../ui/TextField";
import { useMemo, useState } from "react";

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

    refreshingCredentials: boolean;
    lastUpdatedAt: Date | null;
    onRefresh: () => void | Promise<void>;
    canCreate: boolean;
    canEdit: boolean;
    canDelete: boolean;


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
    refreshingCredentials,
    lastUpdatedAt,
    onRefresh,
    canCreate,
    canEdit,
    canDelete,

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

    const [search, setSearch] = useState({ folderId: null as number | null, value: "" });
    const selectedFolderId = selectedFolder?.id ?? null;
    const query = search.folderId === selectedFolderId ? search.value : "";
    const setQuery = (value: string) => setSearch({ folderId: selectedFolderId, value });
    const filteredCredentials = useMemo(() => {
        const normalized = query.trim().toLocaleLowerCase("pt-BR");
        if (!normalized) return credentials;
        return credentials.filter((credential) =>
            credential.name.toLocaleLowerCase("pt-BR").includes(normalized)
            || credential.fields.some((field) =>
                !field.is_secret
                && (`${field.name} ${field.value}`).toLocaleLowerCase("pt-BR").includes(normalized),
            ),
        );
    }, [credentials, query]);

    const secretFieldCount = credentials.reduce(
        (total, credential) => total + credential.fields.filter((field) => field.is_secret).length,
        0,
    );

    return (
        <section className="vault-credentials-panel">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="vault-panel-header">

                <div className="vault-panel-title-group">
                    <h2>
                        {selectedFolder
                            ? `Credenciais — ${selectedFolder.name}`
                            : "Credenciais"
                        }
                    </h2>
                    {selectedFolder && !loadingCredentials && (
                        <span>
                            {credentials.length} {credentials.length === 1 ? "credencial" : "credenciais"}
                            <i aria-hidden="true" />
                            {secretFieldCount} {secretFieldCount === 1 ? "segredo" : "segredos"}
                        </span>
                    )}
                </div>


                {!canCreate && !canEdit && !canDelete && (
                    <span className="vault-readonly-badge">Somente leitura</span>
                )}

                {canCreate && selectedFolder &&
                    selectedFolder.parent_id !==
                        null && (

                        <Button
                            onClick={
                                onOpenCreate
                            }
                        >
                            <KeyRound size={15} strokeWidth={1.9} aria-hidden="true" />
                            Nova credencial
                        </Button>

                    )}

            </div>

            {selectedFolder && (
                <div className="vault-credentials-toolbar">
                    <TextField
                        label="Buscar credenciais de automação"
                        labelHidden
                        containerClassName="vault-credentials-search"
                        type="search"
                        value={query}
                        placeholder="Buscar por nome ou campo não secreto..."
                        leadingIcon={<Search size={16} aria-hidden="true" />}
                        trailingAction={query ? (
                            <IconButton
                                size="sm"
                                label="Limpar busca de credenciais"
                                icon={<X size={14} aria-hidden="true" />}
                                onClick={() => setQuery("")}
                            />
                        ) : undefined}
                        onChange={(event) => setQuery(event.target.value)}
                    />
                    <div className="vault-credentials-refresh">
                        {lastUpdatedAt && (
                            <span title={lastUpdatedAt.toLocaleString("pt-BR")}>
                                Atualizado às {lastUpdatedAt.toLocaleTimeString("pt-BR", { hour: "2-digit", minute: "2-digit" })}
                            </span>
                        )}
                        <Button
                            variant="secondary"
                            size="sm"
                            busy={refreshingCredentials}
                            loadingLabel="Atualizando credenciais"
                            disabled={loadingCredentials}
                            onClick={() => void onRefresh()}
                        >
                            <RefreshCw size={15} aria-hidden="true" />
                            Atualizar
                        </Button>
                    </div>
                </div>
            )}


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

                <EmptyState
                    compact
                    icon={<MousePointer2 />}
                    title="Selecione uma pasta"
                    description="Escolha uma pasta ao lado para visualizar e administrar suas credenciais."
                />

            ) : loadingCredentials ? (
                <CardGridSkeleton count={3} />

            ) : credentials.length === 0 ? (

                <EmptyState
                    compact
                    icon={<KeyRound />}
                    title="Nenhuma credencial nesta pasta"
                    description={canCreate
                        ? "Adicione a primeira credencial para disponibilizá-la às automações autorizadas."
                        : "Esta pasta ainda não possui credenciais. Seu perfil tem acesso somente para consulta."}
                    action={canCreate ? <Button size="sm" onClick={onOpenCreate}>Nova credencial</Button> : undefined}
                />

            ) : filteredCredentials.length === 0 ? (

                <EmptyState
                    compact
                    icon={<Search />}
                    title="Nenhuma credencial encontrada"
                    description="A busca considera o nome e apenas campos não secretos desta pasta."
                    action={<Button size="sm" onClick={() => setQuery("")}>Limpar busca</Button>}
                />

            ) : (

                <div className="vault-credentials-list">

                    {filteredCredentials.map(
                        (credential) => (

                            <VaultCredentialCard
                                key={
                                    credential.id
                                }
                                credential={
                                    credential
                                }
                                canEdit={canEdit}
                                canDelete={canDelete}
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

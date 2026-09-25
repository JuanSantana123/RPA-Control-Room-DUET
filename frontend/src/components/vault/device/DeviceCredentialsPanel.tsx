// ============================================================
// DUET CORE - DEVICE CREDENTIALS PANEL
// ============================================================
//
// Painel de composição das Credenciais de Dispositivo.
//
// RESPONSABILIDADE:
//
// - compor toolbar, formulário, estados e lista;
// - utilizar o hook de CRUD;
// - utilizar o hook do fluxo de formulário;
// - aplicar filtro visual por nome/domínio/usuário;
// - confirmar exclusão antes de delegar ao hook.
//
// ESTE COMPONENTE NÃO:
//
// - chama Axios diretamente;
// - conhece endpoints HTTP;
// - criptografa/descriptografa senha;
// - conhece pastas das Credenciais de Automação;
// - conhece associação Agent ↔ credencial;
// - implementa regras do backend.
//
// Arquitetura:
//
// DeviceCredentialsPanel
//     ├── useDeviceCredentials
//     ├── useDeviceCredentialForm
//     ├── DeviceCredentialForm
//     └── DeviceCredentialCard
// ============================================================


import {
    useEffect,
    useMemo,
    useState,
} from "react";


import {
    Loader2,
    Plus,
    RefreshCw,
    Search,
    ShieldCheck,
} from "lucide-react";


import DeviceCredentialCard
    from "./DeviceCredentialCard";


import DeviceCredentialForm
    from "./DeviceCredentialForm";


import {
    useDeviceCredentials,
} from "../../../hooks/vault/useDeviceCredentials";


import {
    useDeviceCredentialForm,
} from "../../../hooks/vault/useDeviceCredentialForm";


import type {
    DeviceCredential,
} from "../../../types/deviceCredentials";


// ============================================================
// PROPS
// ============================================================

interface DeviceCredentialsPanelProps {

    // Mantém mensagens globais coordenadas pela página Vault.
    setError:
        (message: string) => void;

    setSuccessMessage:
        (message: string) => void;

    // Token opcional usado pelo VaultHeader.
    //
    // Sempre que o valor aumenta, o painel abre o formulário
    // de criação. Assim o Header não precisa conhecer detalhes
    // internos do formulário.
    createRequestToken?:
        number;
}


// ============================================================
// COMPONENTE
// ============================================================

function DeviceCredentialsPanel({
    setError,
    setSuccessMessage,
    createRequestToken = 0,
}: DeviceCredentialsPanelProps) {

    // ========================================================
    // CRUD
    // ========================================================

    const {
        credentials,

        loadingCredentials,
        creatingCredential,
        updatingCredentialId,
        deletingCredentialId,

        carregarCredenciais,
        criarCredencial,
        editarCredencial,
        excluirCredencial,
    } = useDeviceCredentials({
        setError,
        setSuccessMessage,
    });


    // ========================================================
    // FORMULÁRIO
    // ========================================================

    const {
        formMode,
        formData,
        editingCredential,

        openCreateForm,
        openEditForm,
        updateField,
        closeForm,
        submitForm,
    } = useDeviceCredentialForm({
        setError,
        setSuccessMessage,
        createCredential:
            criarCredencial,
        updateCredential:
            editarCredencial,
    });


    // ========================================================
    // BUSCA
    // ========================================================

    const [
        searchTerm,
        setSearchTerm,
    ] = useState(
        ""
    );


    // ========================================================
    // AÇÃO EXTERNA DE CRIAÇÃO
    // ========================================================
    //
    // O VaultHeader poderá solicitar a abertura do formulário
    // incrementando createRequestToken.
    //
    // Token 0 representa "nenhuma solicitação ainda".
    // ========================================================

    useEffect(
        () => {

            if (
                createRequestToken > 0
            ) {

                openCreateForm();
            }

        },
        [
            createRequestToken,
        ]
    );


    // ========================================================
    // FILTRAGEM LOCAL
    // ========================================================
    //
    // Nenhum segredo participa do filtro.
    // ========================================================

    const filteredCredentials =
        useMemo(
            () => {

                const query =
                    searchTerm
                        .trim()
                        .toLocaleLowerCase(
                            "pt-BR"
                        );


                if (
                    !query
                ) {

                    return credentials;
                }


                return credentials.filter(
                    (credential) => {

                        const name =
                            credential.name
                                ?.toLocaleLowerCase(
                                    "pt-BR"
                                ) || "";

                        const domain =
                            credential.domain
                                ?.toLocaleLowerCase(
                                    "pt-BR"
                                ) || "";

                        const username =
                            credential.username
                                ?.toLocaleLowerCase(
                                    "pt-BR"
                                ) || "";

                        const account =
                            `${domain}\\${username}`;


                        return (
                            name.includes(query)
                            ||
                            domain.includes(query)
                            ||
                            username.includes(query)
                            ||
                            account.includes(query)
                        );
                    }
                );
            },
            [
                credentials,
                searchTerm,
            ]
        );


    // ========================================================
    // EXCLUSÃO
    // ========================================================

    const handleDelete =
        async (
            credential: DeviceCredential
        ) => {

            const confirmed =
                window.confirm(
                    `Deseja realmente excluir a credencial de dispositivo "${credential.name}"?`
                );


            if (
                !confirmed
            ) {

                return;
            }


            await excluirCredencial(
                credential.id
            );
        };


    // ========================================================
    // ESTADO DE SALVAMENTO
    // ========================================================

    const savingForm =
        formMode === "create"
            ? creatingCredential
            : (
                editingCredential !== null
                &&
                updatingCredentialId ===
                    editingCredential.id
            );


    // ========================================================
    // INTERFACE
    // ========================================================

    return (

        <section className="device-credentials-panel">

            {/* ==================================================
                CABEÇALHO INTERNO
                ================================================== */}

            <div className="device-credentials-panel-header">

                <div>

                    <div className="device-credentials-panel-title">

                        <ShieldCheck
                            size={18}
                            aria-hidden="true"
                        />

                        <h2>
                            Credenciais de Dispositivo
                        </h2>

                    </div>

                    <p>
                        Identidades Windows protegidas para execução
                        controlada nos Devices.
                    </p>

                </div>


                <button
                    type="button"
                    className="primary-button"
                    disabled={
                        creatingCredential
                    }
                    onClick={
                        openCreateForm
                    }
                >

                    <Plus
                        size={16}
                        aria-hidden="true"
                    />

                    Nova credencial

                </button>

            </div>


            {/* ==================================================
                FORMULÁRIO
                ================================================== */}

            {formMode && (

                <DeviceCredentialForm
                    mode={
                        formMode
                    }
                    formData={
                        formData
                    }
                    hasExistingPassword={
                        editingCredential
                            ?.has_password ??
                        false
                    }
                    saving={
                        savingForm
                    }
                    onChange={
                        updateField
                    }
                    onSubmit={
                        submitForm
                    }
                    onCancel={
                        closeForm
                    }
                />

            )}


            {/* ==================================================
                TOOLBAR
                ================================================== */}

            <div className="device-credentials-toolbar">

                <div className="device-credentials-search">

                    <Search
                        size={16}
                        aria-hidden="true"
                    />

                    <input
                        type="search"
                        value={
                            searchTerm
                        }
                        placeholder="Buscar por nome, domínio ou usuário..."
                        aria-label="Buscar credenciais de dispositivo"
                        onChange={
                            (event) =>
                                setSearchTerm(
                                    event.target.value
                                )
                        }
                    />

                </div>


                <button
                    type="button"
                    className="secondary-button"
                    disabled={
                        loadingCredentials
                    }
                    onClick={
                        () => {
                            void carregarCredenciais();
                        }
                    }
                >

                    <RefreshCw
                        size={15}
                        aria-hidden="true"
                    />

                    Atualizar

                </button>

            </div>


            {/* ==================================================
                CONTEÚDO
                ================================================== */}

            {loadingCredentials ? (

                <div className="device-credentials-state">

                    <Loader2
                        size={22}
                        className="spin"
                        aria-hidden="true"
                    />

                    <strong>
                        Carregando credenciais...
                    </strong>

                    <span>
                        Consultando identidades Windows disponíveis.
                    </span>

                </div>

            ) : credentials.length === 0 ? (

                <div className="device-credentials-state">

                    <ShieldCheck
                        size={26}
                        aria-hidden="true"
                    />

                    <strong>
                        Nenhuma credencial de dispositivo
                    </strong>

                    <span>
                        Crie a primeira identidade Windows para
                        utilização pelos Devices.
                    </span>


                    <button
                        type="button"
                        className="primary-button"
                        onClick={
                            openCreateForm
                        }
                    >

                        <Plus
                            size={16}
                            aria-hidden="true"
                        />

                        Criar credencial

                    </button>

                </div>

            ) : filteredCredentials.length === 0 ? (

                <div className="device-credentials-state">

                    <Search
                        size={24}
                        aria-hidden="true"
                    />

                    <strong>
                        Nenhuma credencial encontrada
                    </strong>

                    <span>
                        Ajuste o termo informado na busca.
                    </span>

                </div>

            ) : (

                <div className="device-credentials-list">

                    {filteredCredentials.map(
                        (credential) => (

                            <DeviceCredentialCard
                                key={
                                    credential.id
                                }
                                credential={
                                    credential
                                }
                                deleting={
                                    deletingCredentialId ===
                                    credential.id
                                }
                                onEdit={
                                    openEditForm
                                }
                                onDelete={
                                    handleDelete
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

export default DeviceCredentialsPanel;

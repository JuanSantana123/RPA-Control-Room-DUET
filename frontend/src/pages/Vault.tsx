// ============================================================
// DUET CORE - VAULT PAGE
// ============================================================
//
// Página principal do Credential Vault.
//
// Responsabilidade:
// - compor a interface do Vault;
// - coordenar os hooks especializados;
// - conectar a árvore de pastas às credenciais;
// - apresentar mensagens globais;
// - encaminhar as ações para os componentes visuais.
//
// Arquitetura:
//
// Vault
//   │
//   ├── useVaultFolders
//   │     ├── árvore de pastas
//   │     ├── seleção
//   │     ├── criação
//   │     └── exclusão
//   │
//   ├── useVaultCredentials
//   │     ├── carregamento
//   │     └── exclusão
//   │
//   ├── useVaultCredentialCreation
//   │     ├── formulário
//   │     ├── campos dinâmicos
//   │     └── criação
//   │
//   ├── useVaultCredentialEditing
//   │     ├── edição de campos
//   │     ├── proteção de segredos
//   │     └── atualização
//   │
//   ├── VaultHeader
//   ├── VaultFolderCreatePanel
//   ├── VaultFoldersPanel
//   └── VaultCredentialsPanel
//
// REGRA CRÍTICA:
// A página não manipula valores secretos. A semântica
// keep_existing permanece isolada no hook de edição.
//
// Esta página NÃO:
// - executa chamadas HTTP diretamente;
// - implementa CRUD;
// - percorre árvores recursivamente;
// - manipula campos de credenciais diretamente.
//
// Ela funciona como camada de composição.
// ============================================================

import {
    useState,
} from "react";

import VaultHeader
    from "../components/vault/VaultHeader";

import VaultFolderCreatePanel
    from "../components/vault/VaultFolderCreatePanel";

import VaultFoldersPanel
    from "../components/vault/VaultFoldersPanel";

import VaultCredentialsPanel
    from "../components/vault/VaultCredentialsPanel";

import {
    useVaultFolders,
} from "../hooks/vault/useVaultFolders";

import {
    useVaultCredentials,
} from "../hooks/vault/useVaultCredentials";

import {
    useVaultCredentialCreation,
} from "../hooks/vault/useVaultCredentialCreation";

import {
    useVaultCredentialEditing,
} from "../hooks/vault/useVaultCredentialEditing";

import type {
    VaultFolder,
} from "../types/vault";


// ============================================================
// PÁGINA VAULT
// ============================================================

function Vault() {

    // ========================================================
    // MENSAGENS GLOBAIS
    // ========================================================
    //
    // Permanecem na página porque são compartilhadas entre
    // operações de pastas e credenciais.
    // ========================================================

    const [
        error,
        setError,
    ] = useState("");


    const [
        successMessage,
        setSuccessMessage,
    ] = useState("");


    // ========================================================
    // CREDENCIAIS
    // ========================================================
    //
    // Primeiro inicializamos a camada responsável pela lista
    // de credenciais, pois suas funções de reload são utilizadas
    // pelos hooks de criação e edição.
    // ========================================================

    const {
        credentials,
        loadingCredentials,

        carregarCredenciais,
        limparCredenciais,
        excluirCredencial,
    } = useVaultCredentials({
        setError,
        setSuccessMessage,
    });


    // ========================================================
    // CRIAÇÃO DE CREDENCIAL
    // ========================================================

    const {
        showNewCredentialForm,

        newCredentialName,
        setNewCredentialName,

        newCredentialFields,
        creatingCredential,

        abrirNovaCredencial,
        fecharNovaCredencial,

        adicionarCampo,
        removerCampo,
        atualizarCampo,

        cancelarNovaCredencial,
        criarCredencial,
    } = useVaultCredentialCreation({
        setError,
        setSuccessMessage,

        reloadCredentials:
            carregarCredenciais,
    });


    // ========================================================
    // EDIÇÃO DE CREDENCIAL
    // ========================================================

    const {
        editingCredential,
        editCredentialFields,
        updatingCredential,

        iniciarEdicaoCredencial,
        atualizarCampoEdicao,
        adicionarCampoEdicao,
        removerCampoEdicao,
        cancelarEdicaoCredencial,
        salvarEdicaoCredencial,
    } = useVaultCredentialEditing({
        setError,
        setSuccessMessage,

        reloadCredentials:
            carregarCredenciais,

        closeCreationForm:
            fecharNovaCredencial,
    });


    // ========================================================
    // CALLBACK - SELEÇÃO DE PASTA
    // ========================================================
    //
    // Preserva o fluxo existente:
    //
    // 1. fecha o formulário de nova credencial;
    // 2. carrega as credenciais da pasta escolhida.
    //
    // A própria seleção da pasta continua pertencendo ao
    // useVaultFolders.
    // ========================================================

    const handleFolderSelected =
        (
            folder: VaultFolder
        ) => {

            fecharNovaCredencial();

            carregarCredenciais(
                folder.id
            );
        };


    // ========================================================
    // CALLBACK - PASTA SELECIONADA EXCLUÍDA
    // ========================================================
    //
    // O Vault original limpa as credenciais exibidas quando
    // a pasta atualmente selecionada é excluída.
    // ========================================================

    const handleSelectedFolderDeleted =
        () => {

            limparCredenciais();
        };


    // ========================================================
    // PASTAS
    // ========================================================

    const {
        folders,
        selectedFolder,
        loadingFolders,

        showNewFolderForm,

        newFolderName,
        setNewFolderName,

        newFolderParentId,
        setNewFolderParentId,

        creatingFolder,

        abrirNovaPasta,
        abrirNovaSubpasta,
        cancelarNovaPasta,

        criarPasta,
        selecionarPasta,
        excluirPasta,
    } = useVaultFolders({
        setError,
        setSuccessMessage,

        onFolderSelected:
            handleFolderSelected,

        onSelectedFolderDeleted:
            handleSelectedFolderDeleted,
    });


    // ========================================================
    // CRIAR CREDENCIAL
    // ========================================================
    //
    // O hook recebe a pasta selecionada no momento da ação,
    // preservando o folder_id utilizado pelo Vault original.
    // ========================================================

    const handleCreateCredential =
        async () => {

            await criarCredencial(
                selectedFolder
            );
        };


    // ========================================================
    // SALVAR EDIÇÃO
    // ========================================================

    const handleSaveCredentialEdit =
        async () => {

            await salvarEdicaoCredencial(
                selectedFolder?.id ??
                null
            );
        };


    // ========================================================
    // EXCLUIR CREDENCIAL
    // ========================================================

    const handleDeleteCredential =
        async (
            credential:
                Parameters<
                    typeof excluirCredencial
                >[0]
        ) => {

            await excluirCredencial(
                credential,
                selectedFolder?.id ??
                null
            );
        };


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="page-container vault-page">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <VaultHeader
                onNewFolder={
                    abrirNovaPasta
                }
            />


            {/* ==================================================
                NOVA PASTA
                ================================================== */}

            {showNewFolderForm && (

                <VaultFolderCreatePanel
                    folders={
                        folders
                    }
                    newFolderName={
                        newFolderName
                    }
                    setNewFolderName={
                        setNewFolderName
                    }
                    newFolderParentId={
                        newFolderParentId
                    }
                    setNewFolderParentId={
                        setNewFolderParentId
                    }
                    creatingFolder={
                        creatingFolder
                    }
                    onCreate={
                        criarPasta
                    }
                    onCancel={
                        cancelarNovaPasta
                    }
                />

            )}


            {/* ==================================================
                ERRO
                ================================================== */}

            {error && (

                <div className="alert-message error">
                    {error}
                </div>

            )}


            {/* ==================================================
                SUCESSO
                ================================================== */}

            {successMessage && (

                <div className="alert-message success">
                    {successMessage}
                </div>

            )}


            {/* ==================================================
                CONTEÚDO
                ================================================== */}

            <div className="vault-layout">

                {/* ==================================================
                    ÁRVORE DE PASTAS
                    ================================================== */}

                <VaultFoldersPanel
                    folders={
                        folders
                    }
                    selectedFolder={
                        selectedFolder
                    }
                    loading={
                        loadingFolders
                    }
                    onSelect={
                        selecionarPasta
                    }
                    onNewSubfolder={
                        abrirNovaSubpasta
                    }
                    onDelete={
                        excluirPasta
                    }
                />


                {/* ==================================================
                    CREDENCIAIS
                    ================================================== */}

                <VaultCredentialsPanel
                    selectedFolder={
                        selectedFolder
                    }
                    credentials={
                        credentials
                    }
                    loadingCredentials={
                        loadingCredentials
                    }

                    // ----------------------------------------------
                    // CRIAÇÃO
                    // ----------------------------------------------

                    showNewCredentialForm={
                        showNewCredentialForm
                    }
                    newCredentialName={
                        newCredentialName
                    }
                    setNewCredentialName={
                        setNewCredentialName
                    }
                    newCredentialFields={
                        newCredentialFields
                    }
                    creatingCredential={
                        creatingCredential
                    }
                    onOpenCreate={
                        abrirNovaCredencial
                    }
                    onUpdateCreateField={
                        atualizarCampo
                    }
                    onAddCreateField={
                        adicionarCampo
                    }
                    onRemoveCreateField={
                        removerCampo
                    }
                    onSaveCreate={
                        handleCreateCredential
                    }
                    onCancelCreate={
                        cancelarNovaCredencial
                    }

                    // ----------------------------------------------
                    // EDIÇÃO
                    // ----------------------------------------------

                    editingCredential={
                        editingCredential
                    }
                    editCredentialFields={
                        editCredentialFields
                    }
                    updatingCredential={
                        updatingCredential
                    }
                    onEdit={
                        iniciarEdicaoCredencial
                    }
                    onUpdateEditField={
                        atualizarCampoEdicao
                    }
                    onAddEditField={
                        adicionarCampoEdicao
                    }
                    onRemoveEditField={
                        removerCampoEdicao
                    }
                    onSaveEdit={
                        handleSaveCredentialEdit
                    }
                    onCancelEdit={
                        cancelarEdicaoCredencial
                    }

                    // ----------------------------------------------
                    // EXCLUSÃO
                    // ----------------------------------------------

                    onDelete={
                        handleDeleteCredential
                    }
                />

            </div>

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default Vault;
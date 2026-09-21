// ============================================================
// DUET CORE - VAULT - FOLDERS HOOK
// ============================================================
//
// Hook responsável pelo gerenciamento das pastas do Vault.
//
// Responsabilidade:
// - carregar a árvore de pastas;
// - controlar pasta selecionada;
// - controlar formulário de nova pasta;
// - criar pasta;
// - excluir pasta;
// - selecionar pasta.
//
// Integrações:
// - GET    /vault/folders
// - POST   /vault/folders
// - DELETE /vault/folders/{folder_id}
//
// Este hook NÃO:
// - carrega credenciais;
// - cria credenciais;
// - edita credenciais;
// - renderiza a árvore.
//
// A página conecta a seleção de pasta ao hook de credenciais.
// ============================================================

import {
    useCallback,
    useEffect,
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    VaultFolder,
} from "../../types/vault";


// ============================================================
// PROPS
// ============================================================

interface UseVaultFoldersProps {
    setError:
        (message: string) => void;

    setSuccessMessage:
        (message: string) => void;

    onFolderSelected:
        (folder: VaultFolder) => void;

    onSelectedFolderDeleted:
        () => void;
}


// ============================================================
// HOOK
// ============================================================

export function useVaultFolders({
    setError,
    setSuccessMessage,
    onFolderSelected,
    onSelectedFolderDeleted,
}: UseVaultFoldersProps) {

    // ========================================================
    // ÁRVORE / SELEÇÃO
    // ========================================================

    const [
        folders,
        setFolders,
    ] = useState<VaultFolder[]>([]);


    const [
        selectedFolder,
        setSelectedFolder,
    ] = useState<VaultFolder | null>(
        null
    );


    const [
        loadingFolders,
        setLoadingFolders,
    ] = useState(true);


    // ========================================================
    // NOVA PASTA
    // ========================================================

    const [
        showNewFolderForm,
        setShowNewFolderForm,
    ] = useState(false);


    const [
        newFolderName,
        setNewFolderName,
    ] = useState("");


    const [
        newFolderParentId,
        setNewFolderParentId,
    ] = useState<number | null>(
        null
    );


    const [
        creatingFolder,
        setCreatingFolder,
    ] = useState(false);


    // ========================================================
    // CARREGAR PASTAS
    // ========================================================

    const carregarPastas =
        useCallback(
            async () => {

                try {

                    setLoadingFolders(true);
                    setError("");


                    const response =
                        await api.get(
                            "/vault/folders"
                        );


                    setFolders(
                        response.data.folders ||
                        []
                    );

                } catch (err) {

                    console.error(
                        "Erro ao buscar pastas do Vault:",
                        err
                    );


                    setError(
                        "Não foi possível carregar as pastas do Vault."
                    );

                } finally {

                    setLoadingFolders(false);
                }
            },
            [
                setError,
            ]
        );


    // ========================================================
    // CARGA INICIAL
    // ========================================================

    useEffect(() => {

        carregarPastas();

    }, [
        carregarPastas,
    ]);


    // ========================================================
    // ABRIR NOVA PASTA NA RAIZ
    // ========================================================

    const abrirNovaPasta =
        () => {

            setShowNewFolderForm(true);
            setError("");
        };


    // ========================================================
    // ABRIR NOVA SUBPASTA
    // ========================================================

    const abrirNovaSubpasta =
        (
            folder: VaultFolder
        ) => {

            setShowNewFolderForm(true);

            setNewFolderParentId(
                folder.id
            );

            setError("");
            setSuccessMessage("");
        };


    // ========================================================
    // CANCELAR NOVA PASTA
    // ========================================================

    const cancelarNovaPasta =
        () => {

            setShowNewFolderForm(false);
            setNewFolderName("");
            setNewFolderParentId(null);
            setError("");
        };


    // ========================================================
    // CRIAR PASTA
    // ========================================================

    const criarPasta =
        async () => {

            if (
                !newFolderName.trim()
            ) {

                setError(
                    "Informe o nome da pasta."
                );

                return;
            }


            try {

                setCreatingFolder(true);
                setError("");


                const response =
                    await api.post(
                        "/vault/folders",
                        {
                            name:
                                newFolderName.trim(),

                            parent_id:
                                newFolderParentId,
                        }
                    );


                if (
                    response.data.status !==
                    "success"
                ) {

                    setError(
                        response.data.message ||
                        "Não foi possível criar a pasta."
                    );

                    return;
                }


                setSuccessMessage(
                    `Pasta "${newFolderName.trim()}" criada com sucesso.`
                );


                setShowNewFolderForm(false);
                setNewFolderName("");
                setNewFolderParentId(null);


                await carregarPastas();

            } catch (err: any) {

                console.error(
                    "Erro ao criar pasta:",
                    err
                );


                setError(
                    err.response?.data?.detail ||
                    err.response?.data?.message ||
                    "Não foi possível criar a pasta."
                );

            } finally {

                setCreatingFolder(false);
            }
        };


    // ========================================================
    // SELECIONAR PASTA
    // ========================================================

    const selecionarPasta =
        (
            folder: VaultFolder
        ) => {

            setSelectedFolder(
                folder
            );

            setError("");


            // A página utiliza este callback para carregar
            // as credenciais e fechar o formulário de criação.
            onFolderSelected(
                folder
            );
        };


    // ========================================================
    // EXCLUIR PASTA
    // ========================================================

    const excluirPasta =
        async (
            folder: VaultFolder
        ) => {

            const confirmar =
                window.confirm(
                    `Deseja realmente excluir a pasta "${folder.name}"?`
                );


            if (!confirmar) {
                return;
            }


            try {

                setError("");
                setSuccessMessage("");


                const response =
                    await api.delete(
                        `/vault/folders/${folder.id}`
                    );


                if (
                    response.data?.status !==
                    "success"
                ) {

                    setError(
                        response.data?.message ||
                        "Não foi possível excluir a pasta."
                    );

                    return;
                }


                setSuccessMessage(
                    `Pasta "${folder.name}" excluída com sucesso.`
                );


                if (
                    selectedFolder?.id ===
                    folder.id
                ) {

                    setSelectedFolder(
                        null
                    );

                    onSelectedFolderDeleted();
                }


                await carregarPastas();

            } catch (error: any) {

                console.error(
                    "Erro ao excluir pasta:",
                    error
                );


                console.error(
                    "Resposta da API:",
                    error?.response?.data
                );


                setError(
                    error?.response?.data?.message ||
                    error?.response?.data?.detail ||
                    "Erro ao excluir a pasta."
                );
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
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
    };
}
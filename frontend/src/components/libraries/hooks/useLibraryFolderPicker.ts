/**
 * HOOK - SELETOR DE PASTA
 * ========================
 *
 * Centraliza somente o fluxo de seleção/movimentação
 * de destino no catálogo.
 */

import {
    useMemo,
    useState,
} from "react";

import {
    moveLibrary,
    updateLibraryFolder,
} from "../services/librariesApi";

import {
    obterMensagemErro,
} from "../utils/libraryErrors";

import type {
    FolderPickerMode,
    LibraryCatalogItem,
    LibraryFolderTreeNode,
} from "../types/libraries";


interface UseLibraryFolderPickerOptions {
    folderDestinationId:
        number | null;

    setFolderDestinationId:
        React.Dispatch<
            React.SetStateAction<
                number | null
            >
        >;

    libraryDestinationId:
        number | null;

    setLibraryDestinationId:
        React.Dispatch<
            React.SetStateAction<
                number | null
            >
        >;

    setLibraryError:
        React.Dispatch<
            React.SetStateAction<string>
        >;

    setLibrarySuccess:
        React.Dispatch<
            React.SetStateAction<string>
        >;

    setExpandedFolders:
        React.Dispatch<
            React.SetStateAction<
                Set<number>
            >
        >;

    carregarBibliotecas:
        () => Promise<void>;

    obterPastasBloqueadas:
        (
            mode:
                FolderPickerMode,

            folder:
                LibraryFolderTreeNode |
                null
        ) => Set<number>;

    closeFolderMenu:
        () => void;

    closeLibraryMenu:
        () => void;
}


export function useLibraryFolderPicker({
    folderDestinationId,
    setFolderDestinationId,
    libraryDestinationId,
    setLibraryDestinationId,
    setLibraryError,
    setLibrarySuccess,
    setExpandedFolders,
    carregarBibliotecas,
    obterPastasBloqueadas,
    closeFolderMenu,
    closeLibraryMenu,
}: UseLibraryFolderPickerOptions) {
    const [
        mode,
        setMode,
    ] = useState<
        FolderPickerMode
    >(null);

    const [
        selectedFolderId,
        setSelectedFolderId,
    ] = useState<
        number | null
    >(null);

    const [
        folderItem,
        setFolderItem,
    ] = useState<
        LibraryFolderTreeNode | null
    >(null);

    const [
        libraryItem,
        setLibraryItem,
    ] = useState<
        LibraryCatalogItem | null
    >(null);

    const [
        saving,
        setSaving,
    ] = useState(false);


    const blockedFolderIds =
        useMemo(
            () =>
                obterPastasBloqueadas(
                    mode,
                    folderItem
                ),
            [
                mode,
                folderItem,
                obterPastasBloqueadas,
            ]
        );


    const title = useMemo(
        () => {
            switch (mode) {
                case "folder-create-location":
                    return "Escolha onde criar a pasta";

                case "folder-move":
                    return "Mover pasta";

                case "library-create-location":
                    return "Escolha onde salvar a biblioteca";

                case "library-move":
                    return "Mover biblioteca";

                default:
                    return "Selecionar pasta";
            }
        },
        [
            mode,
        ]
    );


    const description =
        useMemo(
            () => {
                switch (mode) {
                    case "folder-create-location":
                        return "Selecione a pasta pai. A raiz também é um destino válido.";

                    case "folder-move":
                        return folderItem
                            ? `Escolha o novo local de “${folderItem.name}”.`
                            : "Escolha o novo local da pasta.";

                    case "library-create-location":
                        return "Este local organiza a biblioteca no catálogo e não altera o namespace Python.";

                    case "library-move":
                        return libraryItem
                            ? `Escolha o novo local de “${libraryItem.name}”.`
                            : "Escolha o novo local da biblioteca.";

                    default:
                        return undefined;
                }
            },
            [
                mode,
                folderItem,
                libraryItem,
            ]
        );


    const confirmLabel =
        useMemo(
            () => {
                if (
                    mode ===
                    "folder-move"
                ) {
                    return "Mover pasta";
                }

                if (
                    mode ===
                    "library-move"
                ) {
                    return "Mover biblioteca";
                }

                return "Selecionar";
            },
            [
                mode,
            ]
        );


    const openFolderCreateLocation =
        () => {
            setSelectedFolderId(
                folderDestinationId
            );

            setFolderItem(null);
            setLibraryItem(null);

            setMode(
                "folder-create-location"
            );
        };


    const openFolderMove = (
        folder:
            LibraryFolderTreeNode
    ) => {
        closeFolderMenu();

        setFolderItem(
            folder
        );

        setLibraryItem(null);

        setSelectedFolderId(
            folder.parent_id
        );

        setMode(
            "folder-move"
        );
    };


    const openLibraryCreateLocation =
        () => {
            setSelectedFolderId(
                libraryDestinationId
            );

            setFolderItem(null);
            setLibraryItem(null);

            setMode(
                "library-create-location"
            );
        };


    const openLibraryMove = (
        library:
            LibraryCatalogItem
    ) => {
        closeLibraryMenu();

        setFolderItem(null);

        setLibraryItem(
            library
        );

        setSelectedFolderId(
            library.folder_id
        );

        setMode(
            "library-move"
        );
    };


    const close = () => {
        if (saving) {
            return;
        }

        setMode(null);
        setFolderItem(null);
        setLibraryItem(null);
        setSelectedFolderId(null);
    };


    const confirm = async () => {
        if (!mode) {
            return;
        }

        if (
            mode ===
            "folder-create-location"
        ) {
            setFolderDestinationId(
                selectedFolderId
            );

            close();

            return;
        }

        if (
            mode ===
            "library-create-location"
        ) {
            setLibraryDestinationId(
                selectedFolderId
            );

            close();

            return;
        }

        try {
            setSaving(true);

            setLibraryError("");
            setLibrarySuccess("");

            if (
                mode ===
                "folder-move"
            ) {
                if (!folderItem) {
                    throw new Error(
                        "Pasta não identificada."
                    );
                }

                await updateLibraryFolder(
                    folderItem.id,
                    {
                        parent_id:
                            selectedFolderId,
                    }
                );

                if (
                    selectedFolderId !==
                    null
                ) {
                    setExpandedFolders(
                        (
                            current
                        ) => {
                            const next =
                                new Set(
                                    current
                                );

                            next.add(
                                selectedFolderId
                            );

                            return next;
                        }
                    );
                }

                setLibrarySuccess(
                    "Pasta movida com sucesso."
                );

            } else {
                if (!libraryItem) {
                    throw new Error(
                        "Biblioteca não identificada."
                    );
                }

                await moveLibrary(
                    libraryItem.id,
                    selectedFolderId
                );

                if (
                    selectedFolderId !==
                    null
                ) {
                    setExpandedFolders(
                        (
                            current
                        ) => {
                            const next =
                                new Set(
                                    current
                                );

                            next.add(
                                selectedFolderId
                            );

                            return next;
                        }
                    );
                }

                setLibrarySuccess(
                    "Biblioteca movida com sucesso."
                );
            }

            setMode(null);
            setFolderItem(null);
            setLibraryItem(null);
            setSelectedFolderId(null);

            await carregarBibliotecas();

        } catch (error) {
            console.error(
                "Erro ao mover item do catálogo:",
                error
            );

            setLibraryError(
                obterMensagemErro(
                    error,
                    "Não foi possível concluir a movimentação."
                )
            );

        } finally {
            setSaving(false);
        }
    };


    return {
        mode,
        selectedFolderId,
        blockedFolderIds,
        saving,
        title,
        description,
        confirmLabel,

        setSelectedFolderId,

        openFolderCreateLocation,
        openFolderMove,
        openLibraryCreateLocation,
        openLibraryMove,
        close,
        confirm,
    };
}


export default useLibraryFolderPicker;

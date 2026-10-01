/**
 * HOOK - IMPORTAÇÃO STANDALONE
 * =============================
 *
 * Responsável somente pelo fluxo de importação direta
 * de uma biblioteca Python para o catálogo global.
 */

import {
    useState,
} from "react";

import {
    importStandaloneLibrary,
} from "../services/librariesApi";

import {
    obterMensagemErro,
} from "../utils/libraryErrors";

import type {
    ImportLibraryPayload,
    LibraryCatalogItem,
    LibraryFolderTreeNode,
} from "../types/libraries";


interface UseLibraryImportOptions {
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

    setSelectedFolder:
        React.Dispatch<
            React.SetStateAction<
                LibraryFolderTreeNode | null
            >
        >;

    setSelectedLibrary:
        React.Dispatch<
            React.SetStateAction<
                LibraryCatalogItem | null
            >
        >;

    carregarBibliotecas:
        () => Promise<void>;

    carregarVersoes:
        (
            library:
                LibraryCatalogItem
        ) => Promise<void>;

    closeFolderMenu:
        () => void;

    closeLibraryMenu:
        () => void;
}


export function useLibraryImport({
    setLibraryError,
    setLibrarySuccess,
    setExpandedFolders,
    setSelectedFolder,
    setSelectedLibrary,
    carregarBibliotecas,
    carregarVersoes,
    closeFolderMenu,
    closeLibraryMenu,
}: UseLibraryImportOptions) {
    const [
        open,
        setOpen,
    ] = useState(false);

    const [
        destinationId,
        setDestinationId,
    ] = useState<
        number | null
    >(null);

    const [
        importing,
        setImporting,
    ] = useState(false);


    const openImport = (
        folderId:
            number | null = null
    ) => {
        setLibraryError("");
        setLibrarySuccess("");

        closeFolderMenu();
        closeLibraryMenu();

        setDestinationId(
            folderId
        );

        setOpen(true);
    };


    const closeImport = () => {
        if (importing) {
            return;
        }

        setOpen(false);
        setDestinationId(null);
    };


    const importLibrary = async (
        payload:
            ImportLibraryPayload
    ) => {
        try {
            setImporting(true);

            setLibraryError("");
            setLibrarySuccess("");

            const response =
                await importStandaloneLibrary(
                    payload
                );

            const imported =
                response.library;

            setOpen(false);

            if (
                payload.folderId !==
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
                            payload.folderId!
                        );

                        return next;
                    }
                );
            }

            await carregarBibliotecas();

            if (imported) {
                const libraryItem:
                    LibraryCatalogItem = {
                        ...imported,
                        type: "library",
                    };

                setSelectedLibrary(
                    libraryItem
                );

                setSelectedFolder(
                    null
                );

                await carregarVersoes(
                    libraryItem
                );
            }

            setLibrarySuccess(
                "Biblioteca importada e publicada com sucesso."
            );

        } catch (error) {
            console.error(
                "Erro ao importar biblioteca:",
                error
            );

            setLibraryError(
                obterMensagemErro(
                    error,
                    "Não foi possível importar a biblioteca."
                )
            );

        } finally {
            setImporting(false);
        }
    };


    return {
        open,
        destinationId,
        importing,

        openImport,
        closeImport,
        importLibrary,
    };
}


export default useLibraryImport;

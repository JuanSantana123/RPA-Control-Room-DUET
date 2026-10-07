/**
 * HOOK - AÇÕES DESTRUTIVAS
 * =========================
 *
 * Responsável por:
 * - solicitar confirmação;
 * - excluir pasta;
 * - desativar Library;
 * - limpar seleção quando necessário.
 */

import {
    useState,
} from "react";

import {
    deactivateLibrary,
    deleteLibraryFolder,
} from "../services/librariesApi";

import {
    obterMensagemErro,
} from "../utils/libraryErrors";

import type {
    LibraryCatalogItem,
    LibraryConfirmationState,
    LibraryFolderTreeNode,
    LibraryVersionItem,
} from "../types/libraries";


interface UseLibraryDestructiveActionsOptions {
    selectedFolder:
        LibraryFolderTreeNode | null;

    selectedLibrary:
        LibraryCatalogItem | null;

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

    setVersions:
        React.Dispatch<
            React.SetStateAction<
                LibraryVersionItem[]
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

    carregarBibliotecas:
        () => Promise<void>;

    closeFolderMenu:
        () => void;

    closeLibraryMenu:
        () => void;
}


export function useLibraryDestructiveActions({
    selectedFolder,
    selectedLibrary,
    setSelectedFolder,
    setSelectedLibrary,
    setVersions,
    setLibraryError,
    setLibrarySuccess,
    carregarBibliotecas,
    closeFolderMenu,
    closeLibraryMenu,
}: UseLibraryDestructiveActionsOptions) {
    const [
        confirmation,
        setConfirmation,
    ] = useState<
        LibraryConfirmationState
    >(null);

    const [
        confirming,
        setConfirming,
    ] = useState(false);


    const requestDeleteFolder = (
        folder:
            LibraryFolderTreeNode
    ) => {
        closeFolderMenu();

        setConfirmation({
            kind: "delete-folder",
            folder,
        });
    };


    const requestDeactivateLibrary = (
        library:
            LibraryCatalogItem
    ) => {
        closeLibraryMenu();

        setConfirmation({
            kind:
                "deactivate-library",

            library,
        });
    };


    const cancel = () => {
        if (confirming) {
            return;
        }

        setConfirmation(null);
    };


    const confirm = async () => {
        if (!confirmation) {
            return;
        }

        try {
            setConfirming(true);

            setLibraryError("");
            setLibrarySuccess("");

            if (
                confirmation.kind ===
                "delete-folder"
            ) {
                await deleteLibraryFolder(
                    confirmation.folder.id
                );

                if (
                    selectedFolder?.id ===
                    confirmation.folder.id
                ) {
                    setSelectedFolder(
                        null
                    );
                }

                setLibrarySuccess(
                    "Pasta excluída com sucesso."
                );

            } else {
                await deactivateLibrary(
                    confirmation.library.id
                );

                if (
                    selectedLibrary?.id ===
                    confirmation.library.id
                ) {
                    setSelectedLibrary(
                        null
                    );

                    setVersions([]);
                }

                setLibrarySuccess(
                    "Biblioteca desativada com sucesso."
                );
            }

            setConfirmation(null);

            await carregarBibliotecas();

        } catch (error) {
            console.error(
                "Erro em ação destrutiva de Bibliotecas:",
                error
            );

            setLibraryError(
                obterMensagemErro(
                    error,
                    "Não foi possível concluir a operação."
                )
            );

        } finally {
            setConfirming(false);
        }
    };


    return {
        confirmation,
        confirming,

        requestDeleteFolder,
        requestDeactivateLibrary,
        cancel,
        confirm,
    };
}


export default useLibraryDestructiveActions;

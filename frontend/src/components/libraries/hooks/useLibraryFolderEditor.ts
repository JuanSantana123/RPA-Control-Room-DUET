/**
 * HOOK - EDITOR DE PASTA
 * =======================
 *
 * Responsável somente pelo fluxo de:
 * - criar pasta;
 * - renomear pasta;
 * - estado do formulário;
 * - persistência da pasta.
 */

import {
    useMemo,
    useState,
} from "react";

import {
    createLibraryFolder,
    updateLibraryFolder,
} from "../services/librariesApi";

import {
    encontrarCaminhoPasta,
} from "../utils/libraryTree";

import {
    obterMensagemErro,
} from "../utils/libraryErrors";

import type {
    FolderEditorMode,
    LibraryFolderTreeNode,
    LibraryTreeNode,
} from "../types/libraries";


interface UseLibraryFolderEditorOptions {
    libraryTree:
        LibraryTreeNode[];

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

    closeFolderMenu:
        () => void;
}


export function useLibraryFolderEditor({
    libraryTree,
    setLibraryError,
    setLibrarySuccess,
    setExpandedFolders,
    carregarBibliotecas,
    closeFolderMenu,
}: UseLibraryFolderEditorOptions) {
    const [
        mode,
        setMode,
    ] = useState<FolderEditorMode>(
        null
    );

    const [
        item,
        setItem,
    ] = useState<
        LibraryFolderTreeNode | null
    >(null);

    const [
        name,
        setName,
    ] = useState("");

    const [
        destinationId,
        setDestinationId,
    ] = useState<
        number | null
    >(null);

    const [
        saving,
        setSaving,
    ] = useState(false);


    const destinationLabel =
        useMemo(
            () => {
                if (
                    destinationId === null
                ) {
                    return "Bibliotecas";
                }

                return [
                    "Bibliotecas",
                    ...(
                        encontrarCaminhoPasta(
                            libraryTree,
                            destinationId
                        ) || []
                    ),
                ].join(" / ");
            },
            [
                libraryTree,
                destinationId,
            ]
        );


    const close = () => {
        setMode(null);
        setItem(null);
        setName("");
        setDestinationId(null);
        setSaving(false);
    };


    const openCreate = (
        parentId: number | null
    ) => {
        setLibraryError("");
        setLibrarySuccess("");

        closeFolderMenu();

        setMode("create");
        setItem(null);
        setName("");
        setDestinationId(
            parentId
        );
    };


    const openRename = (
        folder:
            LibraryFolderTreeNode
    ) => {
        setLibraryError("");
        setLibrarySuccess("");

        closeFolderMenu();

        setMode("rename");
        setItem(folder);
        setName(folder.name);
        setDestinationId(
            folder.parent_id
        );
    };


    const save = async () => {
        const normalizedName =
            name.trim();

        if (!mode) {
            return;
        }

        if (!normalizedName) {
            setLibraryError(
                "Informe um nome para a pasta."
            );

            return;
        }

        if (
            mode === "rename" &&
            !item
        ) {
            setLibraryError(
                "Não foi possível identificar a pasta selecionada."
            );

            return;
        }

        try {
            setSaving(true);

            setLibraryError("");
            setLibrarySuccess("");

            if (mode === "create") {
                await createLibraryFolder({
                    name:
                        normalizedName,

                    parent_id:
                        destinationId,
                });

                if (
                    destinationId !== null
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
                                destinationId
                            );

                            return next;
                        }
                    );
                }

                setLibrarySuccess(
                    "Pasta criada com sucesso."
                );

            } else {
                await updateLibraryFolder(
                    item!.id,
                    {
                        name:
                            normalizedName,
                    }
                );

                setLibrarySuccess(
                    "Pasta renomeada com sucesso."
                );
            }

            close();

            await carregarBibliotecas();

        } catch (error) {
            console.error(
                "Erro ao salvar pasta de Bibliotecas:",
                error
            );

            setLibraryError(
                obterMensagemErro(
                    error,
                    "Não foi possível salvar a pasta."
                )
            );

        } finally {
            setSaving(false);
        }
    };


    return {
        mode,
        name,
        destinationId,
        destinationLabel,
        saving,

        setName,
        setDestinationId,

        openCreate,
        openRename,
        close,
        save,
    };
}


export default useLibraryFolderEditor;

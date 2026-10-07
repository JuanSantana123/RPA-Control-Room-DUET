/**
 * HOOK - EDITOR DE LIBRARY
 * =========================
 *
 * Responsável somente pelo fluxo de:
 * - criar identidade de Library;
 * - editar metadados;
 * - estado do formulário;
 * - persistência da Library.
 */

import {
    useMemo,
    useState,
} from "react";

import {
    createLibrary,
    updateLibrary,
} from "../services/librariesApi";

import {
    encontrarCaminhoPasta,
} from "../utils/libraryTree";

import {
    obterMensagemErro,
} from "../utils/libraryErrors";

import type {
    LibraryCatalogItem,
    LibraryEditorMode,
    LibraryFolderTreeNode,
    LibraryTreeNode,
} from "../types/libraries";


interface UseLibraryEditorOptions {
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

    closeFolderMenu:
        () => void;

    closeLibraryMenu:
        () => void;
}


export function useLibraryEditor({
    libraryTree,
    setLibraryError,
    setLibrarySuccess,
    setExpandedFolders,
    setSelectedFolder,
    setSelectedLibrary,
    carregarBibliotecas,
    closeFolderMenu,
    closeLibraryMenu,
}: UseLibraryEditorOptions) {
    const [
        mode,
        setMode,
    ] = useState<
        LibraryEditorMode
    >(null);

    const [
        item,
        setItem,
    ] = useState<
        LibraryCatalogItem | null
    >(null);

    const [
        name,
        setName,
    ] = useState("");

    const [
        importName,
        setImportName,
    ] = useState("");

    const [
        description,
        setDescription,
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
        setImportName("");
        setDescription("");
        setDestinationId(null);
        setSaving(false);
    };


    const openCreate = (
        folderId: number | null
    ) => {
        setLibraryError("");
        setLibrarySuccess("");

        closeFolderMenu();
        closeLibraryMenu();

        setMode("create");
        setItem(null);
        setName("");
        setImportName("");
        setDescription("");
        setDestinationId(
            folderId
        );
    };


    const openEdit = (
        library:
            LibraryCatalogItem
    ) => {
        setLibraryError("");
        setLibrarySuccess("");

        closeLibraryMenu();

        setMode("edit");
        setItem(library);
        setName(library.name);
        setImportName(
            library.import_name
        );
        setDescription(
            library.description || ""
        );
        setDestinationId(
            library.folder_id
        );
    };


    const save = async () => {
        if (!mode) {
            return;
        }

        const normalizedName =
            name.trim();

        const normalizedImportName =
            importName.trim();

        if (!normalizedName) {
            setLibraryError(
                "Informe o nome da biblioteca."
            );

            return;
        }

        if (
            mode === "create" &&
            !normalizedImportName
        ) {
            setLibraryError(
                "Informe o import_name da biblioteca."
            );

            return;
        }

        if (
            mode === "edit" &&
            !item
        ) {
            setLibraryError(
                "Não foi possível identificar a biblioteca selecionada."
            );

            return;
        }

        try {
            setSaving(true);

            setLibraryError("");
            setLibrarySuccess("");

            if (mode === "create") {
                const response =
                    await createLibrary({
                        name:
                            normalizedName,

                        import_name:
                            normalizedImportName,

                        description:
                            description.trim() ||
                            null,

                        folder_id:
                            destinationId,
                    });

                const created =
                    response.library;

                if (created) {
                    setSelectedLibrary({
                        ...created,
                        type: "library",
                    });

                    setSelectedFolder(
                        null
                    );
                }

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
                    "Biblioteca criada com sucesso."
                );

            } else {
                await updateLibrary(
                    item!.id,
                    {
                        name:
                            normalizedName,

                        description:
                            description.trim() ||
                            null,
                    }
                );

                setLibrarySuccess(
                    "Biblioteca atualizada com sucesso."
                );
            }

            close();

            await carregarBibliotecas();

        } catch (error) {
            console.error(
                "Erro ao salvar biblioteca:",
                error
            );

            setLibraryError(
                obterMensagemErro(
                    error,
                    "Não foi possível salvar a biblioteca."
                )
            );

        } finally {
            setSaving(false);
        }
    };


    return {
        mode,
        name,
        importName,
        description,
        destinationId,
        destinationLabel,
        saving,

        setName,
        setImportName,
        setDescription,
        setDestinationId,

        openCreate,
        openEdit,
        close,
        save,
    };
}


export default useLibraryEditor;

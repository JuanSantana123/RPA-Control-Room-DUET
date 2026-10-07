/**
 * HOOK - CATÁLOGO DE BIBLIOTECAS
 * ===============================
 *
 * Responsável somente pelo estado e carregamento do catálogo:
 *
 * - árvore de Libraries;
 * - totais;
 * - busca;
 * - pastas expandidas;
 * - seleção atual;
 * - versões da Library selecionada;
 * - dados derivados da árvore.
 *
 * IMPORTANTE
 * ----------
 * Este hook NÃO renderiza interface.
 * Modais, menus e confirmações continuam em componentes próprios.
 */

import {
    useCallback,
    useMemo,
    useRef,
    useState,
} from "react";

import {
    getLibrariesTree,
    getLibraryVersions,
} from "../services/librariesApi";

import {
    converterParaFolderOptions,
    encontrarCaminhoPasta,
    encontrarLibrary,
    encontrarPasta,
    filtrarArvore,
    obterIdsDescendentes,
    obterPastasDoNivel,
} from "../utils/libraryTree";

import {
    obterMensagemErro,
} from "../utils/libraryErrors";


import {
    contarItensArvore,
    filtrarArvorePorVisao,
} from "../utils/libraryCatalogView";

import type {
    FolderPickerMode,
    LibraryCatalogItem,
    LibraryFolderTreeNode,
    LibraryTreeNode,
    LibraryVersionItem,
    LibraryCatalogView,
} from "../types/libraries";


/* ============================================================
   RETORNO DO HOOK
   ============================================================ */

export interface UseLibrariesCatalogResult {
    // --------------------------------------------------------
    // CATÁLOGO
    // --------------------------------------------------------

    libraryTree: LibraryTreeNode[];
    catalogView:
        LibraryCatalogView;
    libraryFolderCount: number;

    libraryCount: number;

    loadingLibraries: boolean;

    libraryError: string;

    librarySuccess: string;

    librarySearch: string;

    expandedFolders: Set<number>;


    // --------------------------------------------------------
    // SELEÇÃO / DETALHES
    // --------------------------------------------------------

    selectedFolder:
        LibraryFolderTreeNode | null;

    selectedLibrary:
        LibraryCatalogItem | null;

    versions:
        LibraryVersionItem[];

    loadingVersions: boolean;


    // --------------------------------------------------------
    // DADOS DERIVADOS
    // --------------------------------------------------------

    folderOptions:
        ReturnType<
            typeof converterParaFolderOptions
        >;

    visibleTree:
        LibraryTreeNode[];

    selectedFolderPath:
        string[];

    selectedLibraryPath:
        string[];


    // --------------------------------------------------------
    // SETTERS NECESSÁRIOS PELA CAMADA DE INTERFACE
    // --------------------------------------------------------

    setLibraryError:
        React.Dispatch<
            React.SetStateAction<string>
        >;

    setLibrarySuccess:
        React.Dispatch<
            React.SetStateAction<string>
        >;

    setLibrarySearch:
        React.Dispatch<
            React.SetStateAction<string>
        >;

    alterarCatalogView:
        (
            view: LibraryCatalogView
        ) => void;

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

    setVersions:
        React.Dispatch<
            React.SetStateAction<
                LibraryVersionItem[]
            >
        >;


    // --------------------------------------------------------
    // AÇÕES
    // --------------------------------------------------------

    carregarBibliotecas:
        () => Promise<void>;

    carregarVersoes:
        (
            library: LibraryCatalogItem
        ) => Promise<void>;

    selecionarPasta:
        (
            folder:
                LibraryFolderTreeNode
        ) => void;

    selecionarLibrary:
        (
            library:
                LibraryCatalogItem
        ) => Promise<void>;

    alternarPasta:
        (
            folderId: number
        ) => void;

    obterPastasBloqueadas:
        (
            mode: FolderPickerMode,
            folder:
                LibraryFolderTreeNode | null
        ) => Set<number>;
}


/* ============================================================
   HOOK
   ============================================================ */

export function useLibrariesCatalog():
UseLibrariesCatalogResult {

    // ========================================================
    // ESTADOS - CATÁLOGO
    // ========================================================
    const [
        catalogView,
        setCatalogView,
    ] = useState<LibraryCatalogView>(
        "active"
    );
    const [
        libraryTree,
        setLibraryTree,
    ] = useState<LibraryTreeNode[]>([]);

    const [
        libraryFolderCount,
        setLibraryFolderCount,
    ] = useState(0);

    const [
        libraryCount,
        setLibraryCount,
    ] = useState(0);

    const [
        loadingLibraries,
        setLoadingLibraries,
    ] = useState(true);

    const [
        libraryError,
        setLibraryError,
    ] = useState("");

    const [
        librarySuccess,
        setLibrarySuccess,
    ] = useState("");

    const [
        librarySearch,
        setLibrarySearch,
    ] = useState("");

    const [
        expandedFolders,
        setExpandedFolders,
    ] = useState<Set<number>>(
        new Set()
    );


    // ========================================================
    // ESTADOS - SELEÇÃO / DETALHES
    // ========================================================

    const [
        selectedFolder,
        setSelectedFolder,
    ] = useState<
        LibraryFolderTreeNode | null
    >(null);

    const [
        selectedLibrary,
        setSelectedLibrary,
    ] = useState<
        LibraryCatalogItem | null
    >(null);

    const [
        versions,
        setVersions,
    ] = useState<
        LibraryVersionItem[]
    >([]);

    const [
        loadingVersions,
        setLoadingVersions,
    ] = useState(false);


    // Evita reabrir automaticamente as pastas raiz
    // após cada atualização do catálogo.
    const catalogInitialized =
        useRef(false);


    // ========================================================
    // DADOS DERIVADOS
    // ========================================================

    const folderOptions = useMemo(
        () =>
            converterParaFolderOptions(
                libraryTree
            ),
        [
            libraryTree,
        ]
    );


        const treeByView = useMemo(
        () =>
            filtrarArvorePorVisao(
                libraryTree,
                catalogView
            ),
        [
            libraryTree,
            catalogView,
        ]
    );


    const visibleTree = useMemo(
        () =>
            filtrarArvore(
                treeByView,
                librarySearch
            ),
        [
            treeByView,
            librarySearch,
        ]
    );


    const selectedFolderPath =
        useMemo(
            () => {
                if (!selectedFolder) {
                    return [];
                }

                return (
                    encontrarCaminhoPasta(
                        libraryTree,
                        selectedFolder.id
                    ) || [
                        selectedFolder.name,
                    ]
                );
            },
            [
                libraryTree,
                selectedFolder,
            ]
        );


    const selectedLibraryPath =
        useMemo(
            () => {
                if (
                    !selectedLibrary ||
                    selectedLibrary.folder_id ===
                        null
                ) {
                    return [];
                }

                return (
                    encontrarCaminhoPasta(
                        libraryTree,
                        selectedLibrary.folder_id
                    ) || []
                );
            },
            [
                libraryTree,
                selectedLibrary,
            ]
        );


    // ========================================================
    // CARREGAMENTO DO CATÁLOGO
    // ========================================================

    const carregarBibliotecas =
        useCallback(
            async () => {
                try {
                    setLoadingLibraries(
                        true
                    );

                    setLibraryError("");

                    const response =
                        await getLibrariesTree(
                            catalogView === "archived"
                        );

                    const tree =
                        response.tree || [];


                    const treeDaVisao =
                        filtrarArvorePorVisao(
                            tree,
                            catalogView
                        );

                    const totais =
                        contarItensArvore(
                            treeDaVisao
                        );

                    setLibraryTree(
                        tree
                    );

                    setLibraryFolderCount(
                        totais.folders
                    );

                    setLibraryCount(
                        totais.libraries
                    );


                    /*
                     * Na primeira abertura, deixa as
                     * pastas raiz expandidas.
                     */
                    if (
                        !catalogInitialized.current
                    ) {
                        setExpandedFolders(
                            new Set(
                                obterPastasDoNivel(
                                    tree
                                ).map(
                                    (
                                        folder
                                    ) =>
                                        folder.id
                                )
                            )
                        );

                        catalogInitialized.current =
                            true;
                    }


                    /*
                     * Depois de uma mutação, atualiza
                     * a referência da pasta selecionada.
                     */
                    setSelectedFolder(
                        (
                            atual
                        ) => {
                            if (!atual) {
                                return null;
                            }

                            return encontrarPasta(
                                tree,
                                atual.id
                            );
                        }
                    );


                    /*
                     * Depois de uma mutação, atualiza
                     * a referência da Library selecionada.
                     */
                    setSelectedLibrary(
                        (
                            atual
                        ) => {
                            if (!atual) {
                                return null;
                            }

                            return encontrarLibrary(
                                tree,
                                atual.id
                            );
                        }
                    );

                } catch (error) {
                    console.error(
                        "Erro ao carregar catálogo de Bibliotecas:",
                        error
                    );

                    setLibraryError(
                        obterMensagemErro(
                            error,
                            "Não foi possível carregar o catálogo de Bibliotecas."
                        )
                    );

                } finally {
                    setLoadingLibraries(
                        false
                    );
                }
            },
            [
                catalogView,
            ]
        );


    // ========================================================
    // VERSÕES
    // ========================================================

    const carregarVersoes =
        useCallback(
            async (
                library:
                    LibraryCatalogItem
            ) => {
                try {
                    setLoadingVersions(
                        true
                    );

                    setLibraryError("");

                    const response =
                        await getLibraryVersions(
                            library.id,
                            true
                        );

                    setVersions(
                        response.versions ||
                        []
                    );

                } catch (error) {
                    console.error(
                        "Erro ao carregar versões da Library:",
                        error
                    );

                    setVersions([]);

                    setLibraryError(
                        obterMensagemErro(
                            error,
                            "Não foi possível carregar as versões da Biblioteca."
                        )
                    );

                } finally {
                    setLoadingVersions(
                        false
                    );
                }
            },
            []
        );


    // ========================================================
    // SELEÇÃO
    // ========================================================

    const selecionarPasta =
        useCallback(
            (
                folder:
                    LibraryFolderTreeNode
            ) => {
                setSelectedFolder(
                    folder
                );

                setSelectedLibrary(
                    null
                );

                setVersions([]);
            },
            []
        );


    const selecionarLibrary =
        useCallback(
            async (
                library:
                    LibraryCatalogItem
            ) => {
                setSelectedLibrary(
                    library
                );

                setSelectedFolder(
                    null
                );

                await carregarVersoes(
                    library
                );
            },
            [
                carregarVersoes,
            ]
        );


    // ========================================================
    // EXPANSÃO
    // ========================================================

    const alternarPasta =
        useCallback(
            (
                folderId: number
            ) => {
                setExpandedFolders(
                    (
                        atual
                    ) => {
                        const novo =
                            new Set(
                                atual
                            );

                        if (
                            novo.has(
                                folderId
                            )
                        ) {
                            novo.delete(
                                folderId
                            );
                        } else {
                            novo.add(
                                folderId
                            );
                        }

                        return novo;
                    }
                );
            },
            []
        );
    

    // ========================================================
    // VISÃO DO CATÁLOGO
    // ========================================================

    const alterarCatalogView =
        useCallback(
            (
                view:
                    LibraryCatalogView
            ) => {
                if (
                    view ===
                    catalogView
                ) {
                    return;
                }

                /*
                 * Evita carregar seleção de uma visão na outra.
                 */
                setSelectedLibrary(
                    null
                );

                setSelectedFolder(
                    null
                );

                setVersions([]);

                setLibrarySearch("");

                setExpandedFolders(
                    new Set()
                );

                catalogInitialized.current =
                    false;

                setCatalogView(
                    view
                );
            },
            [
                catalogView,
            ]
        );

    // ========================================================
    // PASTAS BLOQUEADAS
    // ========================================================

    const obterPastasBloqueadas =
        useCallback(
            (
                mode:
                    FolderPickerMode,
                folder:
                    LibraryFolderTreeNode |
                    null
            ) => {
                if (
                    mode !==
                    "folder-move"
                ) {
                    return new Set<number>();
                }

                return obterIdsDescendentes(
                    folder
                );
            },
            []
        );


    // ========================================================
    // RETORNO
    // ========================================================

    return {
        libraryTree,
        catalogView,
        libraryFolderCount,
        libraryCount,
        loadingLibraries,
        libraryError,
        librarySuccess,
        librarySearch,
        expandedFolders,

        selectedFolder,
        selectedLibrary,
        versions,
        loadingVersions,

        folderOptions,
        visibleTree,
        selectedFolderPath,
        selectedLibraryPath,

        setLibraryError,
        setLibrarySuccess,
        setLibrarySearch,
        setExpandedFolders,
        setSelectedFolder,
        setSelectedLibrary,
        setVersions,
        alterarCatalogView,
        carregarBibliotecas,
        carregarVersoes,
        selecionarPasta,
        selecionarLibrary,
        alternarPasta,
        obterPastasBloqueadas,
    };
}


export default useLibrariesCatalog;

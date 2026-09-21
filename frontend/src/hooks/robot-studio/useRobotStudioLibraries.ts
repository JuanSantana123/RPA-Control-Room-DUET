// ============================================================
// DUET CORE - ROBOT STUDIO - LIBRARIES HOOK
// ============================================================
//
// Responsabilidade:
// - controlar os modais de Library do Studio;
// - criar Working Copy de uma nova Library;
// - carregar Libraries publicadas disponíveis;
// - selecionar Libraries e versões;
// - adicionar dependências em lote;
// - remover uma Library do projeto.
//
// Este hook NÃO deve:
// - controlar Checkout;
// - controlar permissões;
// - implementar o Explorer;
// - controlar o Monaco.
//
// O workspace é atualizado através dos setters recebidos do
// hook useRobotStudioWorkspace.
// ============================================================

import {
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    Dispatch,
    SetStateAction,
} from "react";

import type {
    AvailableProjectLibrary,
    OpenTab,
    StudioNode,
} from "../../types/robotStudio";

import {
    findNodeById,
    pathBelongsToNode,
    preserveLoadedFileContents,
} from "../../utils/robotStudioTree";


interface UseRobotStudioLibrariesParams {
    projectId?: string;

    canWriteWorkspace: boolean;
    canViewLibraries: boolean;
    canUseLibrary: boolean;
    canCreateLibrary: boolean;

    dirtyFiles: Set<string>;

    

    setExpandedFolders:
        Dispatch<
            SetStateAction<Set<string>>
        >;

    setSelectedFolderId:
        Dispatch<
            SetStateAction<string | null>
        >;

    // Permite que operações de Library sincronizem a árvore
    // oficial retornada pelo backend com o Workspace do Studio.
    setWorkspace: React.Dispatch<
        React.SetStateAction<StudioNode[]>
    >;

    setOpenTabs:
        Dispatch<
            SetStateAction<OpenTab[]>
        >;

    setActiveFileId:
        Dispatch<
            SetStateAction<string>
        >;

    setDirtyFiles:
        Dispatch<
            SetStateAction<Set<string>>
        >;

    setOutputLines:
        Dispatch<
            SetStateAction<string[]>
        >;

    openFile:
        (
            node: StudioNode
        ) => Promise<void>;

    carregarCheckout:
        (
            registrarOutput?: boolean
        ) => Promise<void>;
}


function getApiErrorMessage(
    error: any,
    fallback: string
): string {

    return (
        error?.response?.data?.detail ||
        error?.response?.data?.message ||
        fallback
    );
}


// ============================================================
// SUGESTÃO DE IMPORT_NAME
// ============================================================
//
// Mantém a transformação utilizada pelo Studio.
// ============================================================

const suggestImportName = (
    value: string
): string => {

    let normalized =
        value
            .normalize("NFD")
            .replace(
                /[\u0300-\u036f]/g,
                ""
            )
            .toLowerCase()
            .trim()
            .replace(
                /[^a-z0-9_]+/g,
                "_"
            )
            .replace(
                /_+/g,
                "_"
            )
            .replace(
                /^_+|_+$/g,
                ""
            );


    if (
        normalized &&
        /^[0-9]/.test(
            normalized
        )
    ) {
        normalized =
            `lib_${normalized}`;
    }


    return normalized;
};


export function useRobotStudioLibraries({
    projectId,
    canWriteWorkspace,
    canViewLibraries,
    canUseLibrary,
    canCreateLibrary,
    dirtyFiles,
    setWorkspace,
    setExpandedFolders,
    setSelectedFolderId,
    setOpenTabs,
    setActiveFileId,
    setDirtyFiles,
    setOutputLines,
    openFile,
    carregarCheckout,
}: UseRobotStudioLibrariesParams) {

    // ========================================================
    // MODAL PRINCIPAL
    // ========================================================

    const [
        showLibraryActions,
        setShowLibraryActions,
    ] = useState(false);


    // ========================================================
    // LIBRARIES EXISTENTES
    // ========================================================

    const [
        showAddExistingLibraries,
        setShowAddExistingLibraries,
    ] = useState(false);


    const [
        availableLibraries,
        setAvailableLibraries,
    ] =
        useState<
            AvailableProjectLibrary[]
        >([]);


    const [
        selectedExistingLibraries,
        setSelectedExistingLibraries,
    ] =
        useState<Set<number>>(
            new Set()
        );


    const [
        selectedExistingVersions,
        setSelectedExistingVersions,
    ] =
        useState<
            Record<number, number>
        >({});


    const [
        loadingAvailableLibraries,
        setLoadingAvailableLibraries,
    ] = useState(false);


    const [
        addingExistingLibraries,
        setAddingExistingLibraries,
    ] = useState(false);


    const [
        existingLibraryError,
        setExistingLibraryError,
    ] = useState("");


    // ========================================================
    // NOVA LIBRARY
    // ========================================================

    const [
        showCreateLibrary,
        setShowCreateLibrary,
    ] = useState(false);

    const [
        libraryName,
        setLibraryName,
    ] = useState("");

    const [
        libraryImportName,
        setLibraryImportName,
    ] = useState("");

    const [
        libraryImportTouched,
        setLibraryImportTouched,
    ] = useState(false);

    const [
        libraryDescription,
        setLibraryDescription,
    ] = useState("");

    const [
        libraryCreateError,
        setLibraryCreateError,
    ] = useState("");

    const [
        creatingLibrary,
        setCreatingLibrary,
    ] = useState(false);


    // ========================================================
    // ABRIR GERENCIAMENTO
    // ========================================================

    const abrirGerenciamentoBibliotecas =
        () => {

            if (
                !canWriteWorkspace
            ) {
                return;
            }


            if (
                dirtyFiles.size > 0
            ) {

                setOutputLines(
                    (current) => [
                        ...current,

                        "[DUET] Salve as alterações antes de gerenciar bibliotecas.",
                    ]
                );

                return;
            }


            setShowLibraryActions(
                true
            );
        };


    // ========================================================
    // ABRIR CRIAÇÃO
    // ========================================================

    const abrirCriacaoBiblioteca =
        () => {

            if (
                !canWriteWorkspace ||
                !canCreateLibrary
            ) {
                return;
            }


            setShowLibraryActions(
                false
            );

            setLibraryCreateError(
                ""
            );

            setShowCreateLibrary(
                true
            );
        };


    // ========================================================
    // CRIAR LIBRARY
    // ========================================================

    const criarBibliotecaProjeto =
        async () => {

            if (
                !projectId ||
                !canWriteWorkspace ||
                !canCreateLibrary ||
                creatingLibrary
            ) {
                return;
            }


            const name =
                libraryName.trim();

            const importName =
                libraryImportName.trim();

            const description =
                libraryDescription
                    .trim();


            if (
                !name ||
                !importName
            ) {
                return;
            }


            try {

                setCreatingLibrary(
                    true
                );

                setLibraryCreateError(
                    ""
                );


                const response =
                    await api.post(
                        `/development/projects/${projectId}/libraries`,
                        {
                            name,
                            import_name:
                                importName,

                            description:
                                description ||
                                null,
                        }
                    );


                const tree:
                    StudioNode[] =
                        response.data?.tree ||
                        [];


                const createdLibrary =
                    response.data
                        ?.library;


                setWorkspace(
                    tree
                );


                const namespacePath =
                    `_libraries/${
                        createdLibrary
                            ?.import_name ||
                        importName
                    }`;


                setExpandedFolders(
                    (current) => {

                        const next =
                            new Set(
                                current
                            );

                        next.add(
                            "_libraries"
                        );

                        next.add(
                            namespacePath
                        );

                        return next;
                    }
                );


                setSelectedFolderId(
                    namespacePath
                );


                setShowCreateLibrary(
                    false
                );

                setLibraryName("");

                setLibraryImportName("");

                setLibraryDescription("");

                setLibraryImportTouched(
                    false
                );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] Biblioteca criada: ${name} (${
                            createdLibrary
                                ?.import_name ||
                            importName
                        }).`,

                        "[DUET] Ela será publicada em Produção somente junto ao Release do projeto.",
                    ]
                );


                const initFile =
                    findNodeById(
                        tree,
                        `${namespacePath}/__init__.py`
                    );


                if (
                    initFile &&
                    initFile.type ===
                        "file"
                ) {

                    await openFile(
                        initFile
                    );
                }

            } catch (err: any) {

                console.error(
                    "Erro ao criar biblioteca no projeto:",
                    err
                );


                if (
                    err?.response
                        ?.status === 423
                ) {

                    await carregarCheckout(
                        false
                    );
                }


                setLibraryCreateError(
                    getApiErrorMessage(
                        err,
                        "Não foi possível criar a biblioteca."
                    )
                );

            } finally {

                setCreatingLibrary(
                    false
                );
            }
        };


    // ========================================================
    // ABRIR LIBRARIES EXISTENTES
    // ========================================================

    const abrirBibliotecasExistentes =
        async () => {

            if (
                !projectId ||
                !canWriteWorkspace ||
                !canViewLibraries ||
                !canUseLibrary
            ) {
                return;
            }


            setShowLibraryActions(
                false
            );

            setShowAddExistingLibraries(
                true
            );

            setExistingLibraryError("");

            setAvailableLibraries([]);

            setSelectedExistingLibraries(
                new Set()
            );

            setSelectedExistingVersions(
                {}
            );


            try {

                setLoadingAvailableLibraries(
                    true
                );


                const response =
                    await api.get(
                        `/libraries/projects/${projectId}/available`
                    );


                const libraries:
                    AvailableProjectLibrary[] =
                        Array.isArray(
                            response.data
                                ?.libraries
                        )
                            ? response.data
                                .libraries
                            : [];


                const defaultVersions:
                    Record<number, number> =
                        {};


                libraries.forEach(
                    (item) => {

                        defaultVersions[
                            item.library.id
                        ] =
                            item.default_version_id;
                    }
                );


                setAvailableLibraries(
                    libraries
                );

                setSelectedExistingVersions(
                    defaultVersions
                );

            } catch (err: any) {

                console.error(
                    "Erro ao carregar Bibliotecas disponíveis:",
                    err
                );


                setExistingLibraryError(
                    getApiErrorMessage(
                        err,
                        "Não foi possível carregar as bibliotecas publicadas."
                    )
                );

            } finally {

                setLoadingAvailableLibraries(
                    false
                );
            }
        };


    // ========================================================
    // MARCAR / DESMARCAR
    // ========================================================

    const alternarBibliotecaExistente =
        (
            libraryId: number
        ) => {

            setSelectedExistingLibraries(
                (current) => {

                    const next =
                        new Set(
                            current
                        );


                    if (
                        next.has(
                            libraryId
                        )
                    ) {

                        next.delete(
                            libraryId
                        );

                    } else {

                        next.add(
                            libraryId
                        );
                    }


                    return next;
                }
            );


            setExistingLibraryError(
                ""
            );
        };


    // ========================================================
    // SELECIONAR VERSÃO
    // ========================================================

    const selecionarVersaoBibliotecaExistente =
        (
            libraryId: number,
            libraryVersionId: number
        ) => {

            setSelectedExistingVersions(
                (current) => ({
                    ...current,

                    [libraryId]:
                        libraryVersionId,
                })
            );


            setExistingLibraryError(
                ""
            );
        };


    // ========================================================
    // ADICIONAR EM LOTE
    // ========================================================

    const adicionarBibliotecasExistentes =
        async () => {

            if (
                !projectId ||
                !canWriteWorkspace ||
                !canUseLibrary ||
                addingExistingLibraries
            ) {
                return;
            }


            const librariesSelecionadas =
                availableLibraries.filter(
                    (item) =>
                        selectedExistingLibraries
                            .has(
                                item.library.id
                            ) &&
                        !item.already_added
                );


            if (
                librariesSelecionadas
                    .length === 0
            ) {

                setExistingLibraryError(
                    "Selecione pelo menos uma biblioteca."
                );

                return;
            }


            const libraryVersionIds =
                librariesSelecionadas.map(
                    (item) =>
                        selectedExistingVersions[
                            item.library.id
                        ]
                );


            if (
                libraryVersionIds.some(
                    (versionId) =>
                        !versionId
                )
            ) {

                setExistingLibraryError(
                    "Todas as bibliotecas selecionadas precisam possuir uma versão."
                );

                return;
            }


            try {

                setAddingExistingLibraries(
                    true
                );

                setExistingLibraryError(
                    ""
                );


                await api.post(
                    `/libraries/projects/${projectId}/dependencies/bulk`,
                    {
                        library_version_ids:
                            libraryVersionIds,
                    }
                );


                const treeResponse =
                    await api.get(
                        `/development/projects/${projectId}/workspace/tree`
                    );


                const tree:
                    StudioNode[] =
                        treeResponse.data
                            ?.tree || [];


                setWorkspace(
                    (current) =>
                        preserveLoadedFileContents(
                            current,
                            tree
                        )
                );


                setExpandedFolders(
                    (current) => {

                        const next =
                            new Set(
                                current
                            );


                        next.add(
                            "_libraries"
                        );


                        librariesSelecionadas
                            .forEach(
                                (item) => {

                                    next.add(
                                        `_libraries/${item.library.import_name}`
                                    );
                                }
                            );


                        return next;
                    }
                );


                setShowAddExistingLibraries(
                    false
                );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] ${librariesSelecionadas.length} biblioteca(s) adicionada(s) ao projeto.`,
                    ]
                );

            } catch (err: any) {

                console.error(
                    "Erro ao adicionar Bibliotecas:",
                    err
                );


                if (
                    err?.response
                        ?.status === 423
                ) {

                    await carregarCheckout(
                        false
                    );
                }


                setExistingLibraryError(
                    getApiErrorMessage(
                        err,
                        "Não foi possível adicionar as bibliotecas."
                    )
                );

            } finally {

                setAddingExistingLibraries(
                    false
                );
            }
        };


    // ========================================================
    // REMOVER LIBRARY DO PROJETO
    // ========================================================

    const removerBibliotecaDoProjeto =
        async (
            node: StudioNode
        ) => {

            if (
                !projectId ||
                !canWriteWorkspace ||
                !canUseLibrary
            ) {
                return;
            }


            if (
                dirtyFiles.size > 0
            ) {

                setOutputLines(
                    (current) => [
                        ...current,

                        "[DUET] Salve as alterações antes de remover uma biblioteca.",
                    ]
                );

                return;
            }


            const importName =
                node.id
                    .replace(
                        /^_libraries\//,
                        ""
                    )
                    .split("/")[0];


            try {

                const dependenciesResponse =
                    await api.get(
                        `/libraries/projects/${projectId}/dependencies`
                    );


                const dependencies =
                    Array.isArray(
                        dependenciesResponse
                            .data?.dependencies
                    )
                        ? dependenciesResponse
                            .data.dependencies
                        : [];


                const dependency =
                    dependencies.find(
                        (item: any) =>
                            item.import_name ===
                            importName
                    );


                if (!dependency) {

                    setOutputLines(
                        (current) => [
                            ...current,

                            `[DUET] Não foi possível localizar a dependência da biblioteca ${importName}.`,
                        ]
                    );

                    return;
                }


                const confirmed =
                    window.confirm(
                        `Remover a biblioteca ${importName} deste projeto?`
                    );


                if (!confirmed) {
                    return;
                }


                await api.delete(
                    `/libraries/projects/${projectId}/dependencies/${dependency.library_id}`
                );


                const treeResponse =
                    await api.get(
                        `/development/projects/${projectId}/workspace/tree`
                    );


                const tree:
                    StudioNode[] =
                        treeResponse.data
                            ?.tree || [];


                setWorkspace(
                    tree
                );


                const libraryPath =
                    `_libraries/${importName}`;


                setOpenTabs(
                    (current) =>
                        current.filter(
                            (tab) =>
                                !pathBelongsToNode(
                                    tab.id,
                                    libraryPath
                                )
                        )
                );


                setActiveFileId(
                    (current) =>
                        pathBelongsToNode(
                            current,
                            libraryPath
                        )
                            ? ""
                            : current
                );


                setSelectedFolderId(
                    (current) =>
                        current &&
                        pathBelongsToNode(
                            current,
                            libraryPath
                        )
                            ? null
                            : current
                );


                setDirtyFiles(
                    (current) => {

                        const next =
                            new Set<string>();


                        current.forEach(
                            (path) => {

                                if (
                                    !pathBelongsToNode(
                                        path,
                                        libraryPath
                                    )
                                ) {

                                    next.add(
                                        path
                                    );
                                }
                            }
                        );


                        return next;
                    }
                );


                setExpandedFolders(
                    (current) => {

                        const next =
                            new Set<string>();


                        current.forEach(
                            (path) => {

                                if (
                                    !pathBelongsToNode(
                                        path,
                                        libraryPath
                                    )
                                ) {

                                    next.add(
                                        path
                                    );
                                }
                            }
                        );


                        return next;
                    }
                );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] Biblioteca removida do projeto: ${importName}.`,
                    ]
                );

            } catch (err: any) {

                console.error(
                    "Erro ao remover biblioteca do projeto:",
                    err
                );


                if (
                    err?.response
                        ?.status === 423
                ) {

                    await carregarCheckout(
                        false
                    );
                }


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] ERRO: ${
                            getApiErrorMessage(
                                err,
                                "Não foi possível remover a biblioteca do projeto."
                            )
                        }`,
                    ]
                );
            }
        };


    return {
        showLibraryActions,
        setShowLibraryActions,

        showAddExistingLibraries,
        setShowAddExistingLibraries,

        availableLibraries,

        selectedExistingLibraries,
        selectedExistingVersions,

        loadingAvailableLibraries,
        addingExistingLibraries,
        existingLibraryError,

        showCreateLibrary,
        setShowCreateLibrary,

        libraryName,
        setLibraryName,

        libraryImportName,
        setLibraryImportName,

        libraryImportTouched,
        setLibraryImportTouched,

        libraryDescription,
        setLibraryDescription,

        libraryCreateError,
        setLibraryCreateError,

        creatingLibrary,

        suggestImportName,

        abrirGerenciamentoBibliotecas,
        abrirCriacaoBiblioteca,
        criarBibliotecaProjeto,

        abrirBibliotecasExistentes,
        alternarBibliotecaExistente,
        selecionarVersaoBibliotecaExistente,
        adicionarBibliotecasExistentes,

        removerBibliotecaDoProjeto,
    };
}
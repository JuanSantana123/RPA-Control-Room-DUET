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
import {
    getApiErrorMessage,
    getApiErrorStatus,
} from "../../utils/apiErrors";

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
import { useInteraction } from "../../context/useInteraction";


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

    const { confirm } = useInteraction();

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
    // IMPORTAR LIBRARY POR ZIP
    // ========================================================

    const [
        showImportLibrary,
        setShowImportLibrary,
    ] = useState(false);


    const [
        importingLibrary,
        setImportingLibrary,
    ] = useState(false);


    const [
        importLibraryError,
        setImportLibraryError,
    ] = useState("");


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
    // ABRIR IMPORTAÇÃO POR ZIP
    // ========================================================

    const abrirImportacaoBiblioteca =
        () => {

            if (
                !canWriteWorkspace ||
                !canCreateLibrary
            ) {
                return;
            }


            if (
                dirtyFiles.size > 0
            ) {

                setOutputLines(
                    (current) => [
                        ...current,

                        "[DUET] Salve as alterações antes de importar uma biblioteca.",
                    ]
                );

                return;
            }


            setShowLibraryActions(
                false
            );

            setImportLibraryError(
                ""
            );

            setShowImportLibrary(
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

            } catch (err: unknown) {

                console.error(
                    "Erro ao criar biblioteca no projeto:",
                    err
                );


                if (
                    getApiErrorStatus(err) === 423
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
    // IMPORTAR LIBRARY POR ZIP
    // ========================================================

    const importarBibliotecaProjeto =
        async (
            payload: {
                name: string;
                importName: string;
                description: string;
                file: File;
            }
        ) => {

            if (
                !projectId ||
                !canWriteWorkspace ||
                !canCreateLibrary ||
                importingLibrary
            ) {
                return;
            }


            try {

                setImportingLibrary(
                    true
                );

                setImportLibraryError(
                    ""
                );


                const formData =
                    new FormData();

                formData.append(
                    "name",
                    payload.name.trim()
                );

                formData.append(
                    "import_name",
                    payload.importName.trim()
                );

                formData.append(
                    "description",
                    payload.description.trim()
                );

                formData.append(
                    "file",
                    payload.file
                );


                const response =
                    await api.post(
                        `/development/projects/${projectId}/libraries/import`,
                        formData
                    );


                const tree:
                    StudioNode[] =
                        response.data?.tree ||
                        [];


                const importedLibrary =
                    response.data?.library;


                setWorkspace(
                    tree
                );


                const namespace =
                    importedLibrary?.import_name ||
                    payload.importName.trim();


                const namespacePath =
                    `_libraries/${namespace}`;


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


                setShowImportLibrary(
                    false
                );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] Biblioteca importada para o projeto: ${namespace}.`,

                        importedLibrary?.is_new
                            ? "[DUET] A biblioteca é nova e será publicada somente junto ao Release."
                            : `[DUET] Working Copy criada a partir da Library publicada${
                                importedLibrary?.version
                                    ? ` (${importedLibrary.version})`
                                    : ""
                            }.`,
                    ]
                );


                const initFile =
                    findNodeById(
                        tree,
                        `${namespacePath}/__init__.py`
                    );


                if (
                    initFile &&
                    initFile.type === "file"
                ) {

                    await openFile(
                        initFile
                    );
                }

            } catch (err: unknown) {

                console.error(
                    "Erro ao importar biblioteca para o projeto:",
                    err
                );


                if (
                    getApiErrorStatus(err) === 423
                ) {

                    await carregarCheckout(
                        false
                    );
                }


                setImportLibraryError(
                    getApiErrorMessage(
                        err,
                        "Não foi possível importar a biblioteca para o projeto."
                    )
                );

            } finally {

                setImportingLibrary(
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

            } catch (err: unknown) {

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

            } catch (err: unknown) {

                console.error(
                    "Erro ao adicionar Bibliotecas:",
                    err
                );


                if (
                    getApiErrorStatus(err) === 423
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

            // --------------------------------------------------------
            // VALIDAÇÕES BÁSICAS
            // --------------------------------------------------------
            //
            // A remoção modifica a composição do projeto e também
            // pode alterar fisicamente o Workspace.
            // --------------------------------------------------------

            if (
                !projectId ||
                !canWriteWorkspace ||
                !canUseLibrary
            ) {
                return;
            }


            // --------------------------------------------------------
            // ARQUIVOS NÃO SALVOS
            // --------------------------------------------------------
            //
            // Não permitimos remover uma Library enquanto houver
            // alterações pendentes no editor.
            //
            // Isso evita fechar abas ou apagar uma Working Copy que
            // ainda possui conteúdo não salvo no frontend.
            // --------------------------------------------------------

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


            // --------------------------------------------------------
            // IMPORT_NAME
            // --------------------------------------------------------
            //
            // O node recebido representa algo como:
            //
            //     _libraries/logging_core
            //
            // Extraímos somente:
            //
            //     logging_core
            // --------------------------------------------------------

            const importName =
                node.id
                    .replace(
                        /^_libraries\//,
                        ""
                    )
                    .split("/")[0];


            try {

                // ----------------------------------------------------
                // LISTAR LIBRARIES DO PROJETO
                // ----------------------------------------------------
                //
                // Este endpoint conhece os dois tipos:
                //
                // - Library publicada:
                //     dependency_id != null
                //
                // - Library nova:
                //     dependency_id = null
                //     draft_id != null
                //
                // Portanto o frontend não precisa mais tentar descobrir
                // ProjectLibraryDependency diretamente.
                // ----------------------------------------------------

                const librariesResponse =
                    await api.get(
                        `/development/projects/${projectId}/libraries`
                    );


                const projectLibraries =
                    Array.isArray(
                        librariesResponse.data
                            ?.libraries
                    )
                        ? librariesResponse.data
                            .libraries
                        : [];


                const library =
                    projectLibraries.find(
                        (
                            item: {
                                import_name?: string;
                                library_id?: number;
                                is_new?: boolean;
                            }
                        ) =>
                            item.import_name ===
                            importName
                    );


                if (
                    !library ||
                    typeof library.library_id !==
                        "number"
                ) {

                    setOutputLines(
                        (current) => [
                            ...current,

                            `[DUET] Não foi possível localizar a biblioteca ${importName} no projeto.`,
                        ]
                    );

                    return;
                }


                // ----------------------------------------------------
                // CONFIRMAÇÃO
                // ----------------------------------------------------
                //
                // Para Library nova, a Working Copy ainda não foi
                // publicada e será descartada.
                //
                // Para Library já publicada, somente este projeto deixa
                // de utilizá-la; o histórico global permanece intacto.
                // ----------------------------------------------------

                const confirmed =
                    await confirm({
                        title:
                            "Remover biblioteca do projeto?",

                        description:
                            library.is_new
                                ? `A biblioteca nova “${importName}” e sua Working Copy serão removidas deste projeto.`
                                : `A biblioteca “${importName}” será removida deste projeto.`,

                        detail:
                            library.is_new
                                ? "Como ela ainda não foi publicada, seu código local será descartado."
                                : "As versões publicadas da biblioteca continuarão preservadas em Produção.",

                        confirmLabel:
                            "Remover biblioteca",

                        tone:
                            "danger",
                    });


                if (
                    !confirmed
                ) {
                    return;
                }


                // ----------------------------------------------------
                // REMOÇÃO OFICIAL DO DEVELOPMENT
                // ----------------------------------------------------
                //
                // O backend decide corretamente:
                //
                // Library nova:
                //     remove Draft + Working Copy e, quando seguro,
                //     também remove a identidade global não publicada.
                //
                // Library publicada:
                //     remove somente vínculo + Working Copy do projeto.
                //
                // Não usamos mais a rota antiga de dependencies.
                // ----------------------------------------------------

                const deleteResponse =
                    await api.delete(
                        `/development/projects/${projectId}/libraries/${library.library_id}`
                    );


                // ----------------------------------------------------
                // ÁRVORE DEVOLVIDA PELO BACKEND
                // ----------------------------------------------------
                //
                // A nova rota já retorna a árvore oficial após a
                // exclusão. Portanto não precisamos fazer uma segunda
                // requisição GET para workspace/tree.
                // ----------------------------------------------------

                const tree:
                    StudioNode[] =
                        deleteResponse.data
                            ?.tree || [];


                setWorkspace(
                    tree
                );


                const libraryPath =
                    `_libraries/${importName}`;


                // ----------------------------------------------------
                // FECHAR ABAS DA LIBRARY REMOVIDA
                // ----------------------------------------------------

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


                // ----------------------------------------------------
                // LIMPAR ARQUIVO ATIVO
                // ----------------------------------------------------

                setActiveFileId(
                    (current) =>
                        pathBelongsToNode(
                            current,
                            libraryPath
                        )
                            ? ""
                            : current
                );


                // ----------------------------------------------------
                // LIMPAR PASTA SELECIONADA
                // ----------------------------------------------------

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


                // ----------------------------------------------------
                // LIMPAR DIRTY FILES DA LIBRARY
                // ----------------------------------------------------

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


                // ----------------------------------------------------
                // REMOVER EXPANSÕES DA LIBRARY
                // ----------------------------------------------------

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


                // ----------------------------------------------------
                // OUTPUT
                // ----------------------------------------------------

                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] Biblioteca removida do projeto: ${importName}.`,
                    ]
                );

            } catch (err: unknown) {

                console.error(
                    "Erro ao remover biblioteca do projeto:",
                    err
                );


                // Checkout perdido ou inválido.
                if (
                    getApiErrorStatus(err) === 423
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
        showImportLibrary,
        setShowImportLibrary,

        importingLibrary,
        importLibraryError,
        setImportLibraryError,

        suggestImportName,

        abrirGerenciamentoBibliotecas,
        abrirCriacaoBiblioteca,
        criarBibliotecaProjeto,
        abrirImportacaoBiblioteca,
        importarBibliotecaProjeto,

        abrirBibliotecasExistentes,
        alternarBibliotecaExistente,
        selecionarVersaoBibliotecaExistente,
        adicionarBibliotecasExistentes,

        removerBibliotecaDoProjeto,
    };
}

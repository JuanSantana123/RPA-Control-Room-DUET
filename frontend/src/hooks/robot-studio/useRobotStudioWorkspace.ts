// ============================================================
// DUET CORE - ROBOT STUDIO - WORKSPACE
// ============================================================
//
// Responsabilidade:
// - carregar a árvore real do AutomationProject;
// - abrir arquivos sob demanda;
// - controlar abas abertas;
// - controlar arquivo ativo;
// - controlar arquivos modificados;
// - editar e salvar arquivos;
// - criar arquivos e pastas;
// - renomear arquivos e pastas;
// - excluir arquivos e pastas;
// - controlar seleção e expansão do Explorer.
//
// Integrações:
// - API oficial do Development Workspace;
// - Checkout, para sincronizar perda de bloqueio HTTP 423;
// - Output do Studio, para manter as mensagens já existentes.
//
// IMPORTANTE:
// Este hook NÃO altera regras funcionais do RobotStudio.
// Ele apenas move para uma unidade própria a lógica que antes
// permanecia diretamente dentro da página RobotStudio.tsx.
//
// NÃO controla:
// - permissões;
// - aquisição/liberação de Checkout;
// - catálogo de Libraries;
// - componentes visuais.
// ============================================================

import {
    useEffect,
    useMemo,
    useState,
} from "react";

import api from "../../services/api";

import type {
    OpenTab,
    StudioNode,
} from "../../types/robotStudio";

import {
    addNodeToFolder,
    findNodeById,
    pathBelongsToNode,
    remapWorkspacePath,
    removeNodeById,
    renameNodePath,
    updateFileContent,
} from "../../utils/robotStudioTree";


// ============================================================
// CONTRATO DO HOOK
// ============================================================

interface UseRobotStudioWorkspaceParams {

    projectId?: string;

    permissionsLoaded: boolean;

    canViewDevelopment: boolean;

    canWriteWorkspace: boolean;

    // Função oficial do hook de Checkout.
    // É utilizada quando o backend informa HTTP 423.
    carregarCheckout: (
        registrarOutput?: boolean
    ) => Promise<void>;

    // Output continua compartilhado com as demais operações
    // do Studio para preservar a sequência atual das mensagens.
    setOutputLines: React.Dispatch<
        React.SetStateAction<string[]>
    >;
}


// ============================================================
// HELPER - ERRO DA API
// ============================================================
//
// Mantém a mesma leitura de detail/message já utilizada
// atualmente pelo RobotStudio.
// ============================================================

const getApiErrorMessage = (
    err: any,
    fallback: string
): string => {

    const detail =
        err?.response?.data?.detail;


    if (typeof detail === "string") {
        return detail;
    }


    if (
        detail &&
        typeof detail === "object" &&
        typeof detail.message === "string"
    ) {
        return detail.message;
    }


    const message =
        err?.response?.data?.message;


    if (typeof message === "string") {
        return message;
    }


    if (typeof err?.message === "string") {
        return err.message;
    }


    return fallback;
};


// ============================================================
// HOOK
// ============================================================

export function useRobotStudioWorkspace({
    projectId,
    permissionsLoaded,
    canViewDevelopment,
    canWriteWorkspace,
    carregarCheckout,
    setOutputLines,
}: UseRobotStudioWorkspaceParams) {

    // ========================================================
    // ÁRVORE DO WORKSPACE
    // ========================================================

    const [
        workspace,
        setWorkspace,
    ] = useState<StudioNode[]>([]);


    // ========================================================
    // ARQUIVO ATIVO
    // ========================================================

    const [
        activeFileId,
        setActiveFileId,
    ] = useState("");


    // ========================================================
    // ABAS ABERTAS
    // ========================================================

    const [
        openTabs,
        setOpenTabs,
    ] = useState<OpenTab[]>([]);


    // ========================================================
    // PASTAS EXPANDIDAS
    // ========================================================

    const [
        expandedFolders,
        setExpandedFolders,
    ] = useState<Set<string>>(
        new Set(["elements"])
    );


    // ========================================================
    // PASTA SELECIONADA
    // ========================================================

    const [
        selectedFolderId,
        setSelectedFolderId,
    ] =
        useState<string | null>(
            null
        );


    // ========================================================
    // ARQUIVOS MODIFICADOS
    // ========================================================

    const [
        dirtyFiles,
        setDirtyFiles,
    ] =
        useState<Set<string>>(
            new Set()
        );


    const dirty =
        dirtyFiles.size > 0;


    // ========================================================
    // ARQUIVO ATIVO COMPLETO
    // ========================================================

    const activeFile =
        useMemo(
            () => (
                activeFileId
                    ? findNodeById(
                        workspace,
                        activeFileId
                    )
                    : null
            ),
            [
                workspace,
                activeFileId,
            ]
        );


    // ========================================================
    // CARREGAR WORKSPACE REAL
    // ========================================================
    //
    // 1. consulta a árvore;
    // 2. não baixa o conteúdo de todos os arquivos;
    // 3. procura main.py;
    // 4. carrega somente main.py;
    // 5. abre main.py automaticamente.
    // ========================================================

    useEffect(() => {

        const carregarWorkspace =
            async () => {

                if (
                    !projectId ||
                    !permissionsLoaded ||
                    !canViewDevelopment
                ) {
                    return;
                }


                try {

                    // --------------------------------------------
                    // ÁRVORE
                    // --------------------------------------------

                    const treeResponse =
                        await api.get(
                            `/development/projects/${projectId}/workspace/tree`
                        );


                    const tree:
                        StudioNode[] =
                            treeResponse.data?.tree || [];


                    setWorkspace(
                        tree
                    );


                    // Limpa estados pertencentes ao projeto anterior.
                    setActiveFileId("");

                    setOpenTabs([]);

                    setSelectedFolderId(
                        null
                    );

                    setDirtyFiles(
                        new Set()
                    );


                    // Mantém elements aberta inicialmente.
                    setExpandedFolders(
                        new Set(["elements"])
                    );


                    // --------------------------------------------
                    // MAIN.PY
                    // --------------------------------------------

                    const mainFile =
                        findNodeById(
                            tree,
                            "main.py"
                        );


                    if (
                        !mainFile ||
                        mainFile.type !== "file"
                    ) {

                        setOutputLines(
                            (current) => [
                                ...current,

                                "[DUET] Workspace carregado sem main.py.",
                            ]
                        );

                        return;
                    }


                    const fileResponse =
                        await api.get(
                            `/development/projects/${projectId}/workspace/file`,
                            {
                                params: {
                                    path:
                                        mainFile.id,
                                },
                            }
                        );


                    const content =
                        fileResponse.data
                            ?.content ?? "";


                    const workspaceComMain =
                        updateFileContent(
                            tree,
                            mainFile.id,
                            content
                        );


                    setWorkspace(
                        workspaceComMain
                    );


                    setActiveFileId(
                        mainFile.id
                    );


                    setOpenTabs([
                        {
                            id:
                                mainFile.id,

                            name:
                                mainFile.name,
                        },
                    ]);


                    setOutputLines(
                        (current) => [
                            ...current,

                            "[DUET] Workspace carregado do Control Room.",
                        ]
                    );

                } catch (err: any) {

                    console.error(
                        "Erro ao carregar workspace:",
                        err
                    );


                    const mensagem =
                        err.response?.data?.detail ||
                        err.response?.data?.message ||
                        "Não foi possível carregar o workspace.";


                    setOutputLines(
                        (current) => [
                            ...current,

                            `[DUET] ERRO: ${mensagem}`,
                        ]
                    );
                }
            };


        carregarWorkspace();

    }, [
        projectId,
        permissionsLoaded,
        canViewDevelopment,
    ]);


    // ========================================================
    // ABRIR ARQUIVO
    // ========================================================

    const openFile =
        async (
            node: StudioNode
        ) => {

            if (
                node.type !== "file" ||
                !projectId ||
                !canViewDevelopment
            ) {
                return;
            }


            // Seleciona imediatamente a aba.
            setActiveFileId(
                node.id
            );


            // Abre a aba somente se ainda não existir.
            setOpenTabs(
                (current) => {

                    if (
                        current.some(
                            (tab) =>
                                tab.id ===
                                node.id
                        )
                    ) {
                        return current;
                    }


                    return [
                        ...current,

                        {
                            id:
                                node.id,

                            name:
                                node.name,
                        },
                    ];
                }
            );


            // `undefined` significa que o conteúdo ainda não
            // foi buscado. String vazia significa arquivo já
            // carregado e realmente vazio.
            if (
                node.content !== undefined
            ) {
                return;
            }


            try {

                const response =
                    await api.get(
                        `/development/projects/${projectId}/workspace/file`,
                        {
                            params: {
                                path:
                                    node.id,
                            },
                        }
                    );


                const content =
                    response.data?.content ??
                    "";


                setWorkspace(
                    (current) =>
                        updateFileContent(
                            current,
                            node.id,
                            content
                        )
                );

            } catch (err: any) {

                console.error(
                    "Erro ao abrir arquivo do workspace:",
                    err
                );


                const mensagem =
                    err.response?.data?.detail ||
                    err.response?.data?.message ||
                    "Não foi possível abrir o arquivo.";


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] ERRO: ${mensagem}`,
                    ]
                );
            }
        };


    // ========================================================
    // FECHAR ABA
    // ========================================================

    const closeTab =
        (
            tabId: string
        ) => {

            setOpenTabs(
                (current) => {

                    const currentIndex =
                        current.findIndex(
                            (tab) =>
                                tab.id ===
                                tabId
                        );


                    const filtered =
                        current.filter(
                            (tab) =>
                                tab.id !==
                                tabId
                        );


                    if (
                        activeFileId ===
                        tabId
                    ) {

                        const fallback =
                            filtered[
                                Math.max(
                                    0,
                                    currentIndex - 1
                                )
                            ] ||
                            filtered[0];


                        setActiveFileId(
                            fallback?.id || ""
                        );
                    }


                    return filtered;
                }
            );
        };


    // ========================================================
    // ALTERAÇÃO NO MONACO
    // ========================================================

    const handleEditorChange =
        (
            value?: string
        ) => {

            if (
                !canWriteWorkspace ||
                !projectId ||
                !activeFile ||
                activeFile.type !== "file"
            ) {
                return;
            }


            setWorkspace(
                (current) =>
                    updateFileContent(
                        current,
                        activeFile.id,
                        value || ""
                    )
            );


            setDirtyFiles(
                (current) => {

                    const next =
                        new Set(current);


                    next.add(
                        activeFile.id
                    );


                    return next;
                }
            );
        };


    // ========================================================
    // SALVAR ARQUIVO
    // ========================================================
    //
    // Somente o arquivo ativo é enviado.
    //
    // PUT
    // /development/projects/{project_id}/workspace/file
    // ========================================================

    const saveWorkspace =
        async () => {

            if (
                !canWriteWorkspace ||
                !projectId ||
                !activeFile ||
                activeFile.type !== "file"
            ) {
                return;
            }


            try {

                await api.put(
                    `/development/projects/${projectId}/workspace/file`,
                    {
                        path:
                            activeFile.id,

                        content:
                            activeFile.content ??
                            "",
                    }
                );


                setDirtyFiles(
                    (current) => {

                        const next =
                            new Set(current);


                        next.delete(
                            activeFile.id
                        );


                        return next;
                    }
                );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] ${activeFile.name} salvo às ${new Date().toLocaleTimeString()}.`,
                    ]
                );

            } catch (err: any) {

                console.error(
                    "Erro ao salvar arquivo:",
                    err
                );


                if (
                    err?.response?.status ===
                    423
                ) {

                    await carregarCheckout(
                        false
                    );
                }


                const mensagem =
                    getApiErrorMessage(
                        err,
                        "Não foi possível salvar o arquivo."
                    );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] ERRO AO SALVAR: ${mensagem}`,
                    ]
                );
            }
        };


    // ========================================================
    // CTRL+S / CMD+S
    // ========================================================

    useEffect(() => {

        const handleKeyDown =
            (
                event: KeyboardEvent
            ) => {

                if (
                    (
                        event.ctrlKey ||
                        event.metaKey
                    ) &&
                    event.key
                        .toLowerCase() ===
                        "s"
                ) {

                    event.preventDefault();

                    saveWorkspace();
                }
            };


        window.addEventListener(
            "keydown",
            handleKeyDown
        );


        return () => {

            window.removeEventListener(
                "keydown",
                handleKeyDown
            );
        };

    }, [
        workspace,
        activeFileId,
        projectId,
        canWriteWorkspace,
    ]);


    // ========================================================
    // CRIAR ARQUIVO EM UMA PASTA
    // ========================================================

    const createFileInFolder =
        async (
            targetFolderId:
                string | null
        ) => {

            // O contêiner técnico das Libraries não pode receber
            // arquivos diretamente.
            if (
                targetFolderId ===
                "_libraries"
            ) {

                setOutputLines(
                    (current) => [
                        ...current,

                        "[DUET] Selecione uma biblioteca para criar arquivos dentro dela.",
                    ]
                );

                return;
            }


            const name =
                window
                    .prompt(
                        "Nome do novo arquivo:"
                    )
                    ?.trim();


            if (
                !canWriteWorkspace ||
                !name ||
                !projectId
            ) {
                return;
            }


            const path =
                targetFolderId
                    ? `${targetFolderId}/${name}`
                    : name;


            try {

                await api.post(
                    `/development/projects/${projectId}/workspace/files`,
                    {
                        path,
                    }
                );


                const newNode:
                    StudioNode = {

                    id:
                        path,

                    name,

                    type:
                        "file",

                    content:
                        "",
                };


                setWorkspace(
                    (current) =>
                        addNodeToFolder(
                            current,
                            targetFolderId,
                            newNode
                        )
                );


                if (targetFolderId) {

                    setExpandedFolders(
                        (current) => {

                            const next =
                                new Set(
                                    current
                                );


                            next.add(
                                targetFolderId
                            );


                            return next;
                        }
                    );
                }


                await openFile(
                    newNode
                );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] Arquivo criado: ${path}`,
                    ]
                );

            } catch (err: any) {

                console.error(
                    "Erro ao criar arquivo:",
                    err
                );


                if (
                    err?.response?.status ===
                    423
                ) {

                    await carregarCheckout(
                        false
                    );
                }


                const mensagem =
                    getApiErrorMessage(
                        err,
                        "Não foi possível criar o arquivo."
                    );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] ERRO: ${mensagem}`,
                    ]
                );
            }
        };


    // ========================================================
    // CRIAR PASTA DENTRO DE OUTRA PASTA
    // ========================================================

    const createFolderInFolder =
        async (
            targetFolderId:
                string | null
        ) => {

            if (
                targetFolderId ===
                "_libraries"
            ) {

                setOutputLines(
                    (current) => [
                        ...current,

                        "[DUET] Use o botão 'Lib' para criar ou adicionar uma biblioteca.",
                    ]
                );

                return;
            }


            const name =
                window
                    .prompt(
                        "Nome da nova pasta:"
                    )
                    ?.trim();


            if (
                !canWriteWorkspace ||
                !name ||
                !projectId
            ) {
                return;
            }


            const path =
                targetFolderId
                    ? `${targetFolderId}/${name}`
                    : name;


            try {

                await api.post(
                    `/development/projects/${projectId}/workspace/folders`,
                    {
                        path,
                    }
                );


                const newNode:
                    StudioNode = {

                    id:
                        path,

                    name,

                    type:
                        "folder",

                    children:
                        [],
                };


                setWorkspace(
                    (current) =>
                        addNodeToFolder(
                            current,
                            targetFolderId,
                            newNode
                        )
                );


                setExpandedFolders(
                    (current) => {

                        const next =
                            new Set(
                                current
                            );


                        next.add(
                            newNode.id
                        );


                        if (
                            targetFolderId
                        ) {

                            next.add(
                                targetFolderId
                            );
                        }


                        return next;
                    }
                );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] Pasta criada: ${path}`,
                    ]
                );

            } catch (err: any) {

                console.error(
                    "Erro ao criar pasta:",
                    err
                );


                if (
                    err?.response?.status ===
                    423
                ) {

                    await carregarCheckout(
                        false
                    );
                }


                const mensagem =
                    getApiErrorMessage(
                        err,
                        "Não foi possível criar a pasta."
                    );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] ERRO: ${mensagem}`,
                    ]
                );
            }
        };


    // ========================================================
    // BOTÕES GLOBAIS DO EXPLORER
    // ========================================================

    const createFile =
        async () => {

            await createFileInFolder(
                selectedFolderId
            );
        };


    const createFolder =
        async () => {

            await createFolderInFolder(
                selectedFolderId
            );
        };


    // ========================================================
    // RENOMEAR ITEM
    // ========================================================

    const renomearItem =
        async (
            node: StudioNode
        ) => {

            if (
                !canWriteWorkspace ||
                !projectId
            ) {
                return;
            }


            // main.py continua protegido.
            if (
                node.id === "main.py"
            ) {

                setOutputLines(
                    (current) => [
                        ...current,

                        "[DUET] main.py não pode ser renomeado.",
                    ]
                );

                return;
            }


            // Protege SOMENTE:
            //
            // _libraries/<namespace>/__init__.py
            //
            // __init__.py de subpastas continua editável.
            const isLibraryRootInit =
                /^_libraries\/[^/]+\/__init__\.py$/.test(
                    node.id
                );


            if (
                isLibraryRootInit
            ) {

                setOutputLines(
                    (current) => [
                        ...current,

                        "[DUET] __init__.py da raiz de uma Biblioteca não pode ser renomeado.",
                    ]
                );

                return;
            }


            const novoNome =
                window
                    .prompt(
                        `Novo nome para "${node.name}":`,
                        node.name
                    )
                    ?.trim();


            if (!novoNome) {
                return;
            }


            if (
                novoNome ===
                node.name
            ) {
                return;
            }


            try {

                const response =
                    await api.patch(
                        `/development/projects/${projectId}/workspace/item`,
                        {
                            path:
                                node.id,

                            new_name:
                                novoNome,
                        }
                    );


                const newPath:
                    string | undefined =
                        response.data
                            ?.new_path;


                if (!newPath) {

                    throw new Error(
                        "O backend não retornou o novo caminho do item."
                    );
                }


                const oldPath =
                    node.id;


                // --------------------------------------------
                // ÁRVORE
                // --------------------------------------------

                setWorkspace(
                    (current) =>
                        renameNodePath(
                            current,
                            oldPath,
                            newPath,
                            novoNome
                        )
                );


                // --------------------------------------------
                // ABAS
                // --------------------------------------------

                setOpenTabs(
                    (current) =>
                        current.map(
                            (tab) => {

                                const nextId =
                                    remapWorkspacePath(
                                        tab.id,
                                        oldPath,
                                        newPath
                                    );


                                return {
                                    ...tab,

                                    id:
                                        nextId,

                                    name:
                                        tab.id ===
                                        oldPath
                                            ? novoNome
                                            : tab.name,
                                };
                            }
                        )
                );


                // --------------------------------------------
                // ARQUIVO ATIVO
                // --------------------------------------------

                setActiveFileId(
                    (current) =>
                        remapWorkspacePath(
                            current,
                            oldPath,
                            newPath
                        )
                );


                // --------------------------------------------
                // DIRTY FILES
                // --------------------------------------------

                setDirtyFiles(
                    (current) => {

                        const next =
                            new Set<string>();


                        current.forEach(
                            (path) => {

                                next.add(
                                    remapWorkspacePath(
                                        path,
                                        oldPath,
                                        newPath
                                    )
                                );
                            }
                        );


                        return next;
                    }
                );


                // --------------------------------------------
                // PASTA SELECIONADA
                // --------------------------------------------

                setSelectedFolderId(
                    (current) =>
                        current
                            ? remapWorkspacePath(
                                current,
                                oldPath,
                                newPath
                            )
                            : null
                );


                // --------------------------------------------
                // PASTAS EXPANDIDAS
                // --------------------------------------------

                setExpandedFolders(
                    (current) => {

                        const next =
                            new Set<string>();


                        current.forEach(
                            (path) => {

                                next.add(
                                    remapWorkspacePath(
                                        path,
                                        oldPath,
                                        newPath
                                    )
                                );
                            }
                        );


                        return next;
                    }
                );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] Renomeado: ${oldPath} → ${newPath}`,
                    ]
                );

            } catch (err: any) {

                console.error(
                    "Erro ao renomear item:",
                    err
                );


                if (
                    err?.response?.status ===
                    423
                ) {

                    await carregarCheckout(
                        false
                    );
                }


                const mensagem =
                    getApiErrorMessage(
                        err,
                        "Não foi possível renomear o item."
                    );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] ERRO AO RENOMEAR: ${mensagem}`,
                    ]
                );
            }
        };


    // ========================================================
    // EXCLUIR ITEM
    // ========================================================

    const excluirItem =
        async (
            node: StudioNode
        ) => {

            if (
                !canWriteWorkspace ||
                !projectId
            ) {
                return;
            }


            if (
                node.id === "main.py"
            ) {

                setOutputLines(
                    (current) => [
                        ...current,

                        "[DUET] main.py não pode ser excluído.",
                    ]
                );

                return;
            }


            const possuiAlteracaoNaoSalva =
                Array
                    .from(
                        dirtyFiles
                    )
                    .some(
                        (path) =>
                            pathBelongsToNode(
                                path,
                                node.id
                            )
                    );


            let mensagemConfirmacao =
                node.type === "folder"
                    ? (
                        `Excluir a pasta "${node.name}" e TODO o conteúdo dela?`
                    )
                    : (
                        `Excluir o arquivo "${node.name}"?`
                    );


            if (
                possuiAlteracaoNaoSalva
            ) {

                mensagemConfirmacao +=
                    "\n\nATENÇÃO: existem alterações não salvas nesse item.";
            }


            const confirmado =
                window.confirm(
                    mensagemConfirmacao
                );


            if (!confirmado) {
                return;
            }


            try {

                await api.delete(
                    `/development/projects/${projectId}/workspace/item`,
                    {
                        params: {
                            path:
                                node.id,

                            recursive:
                                node.type ===
                                "folder",
                        },
                    }
                );


                const deletedPath =
                    node.id;


                // --------------------------------------------
                // EXPLORER
                // --------------------------------------------

                setWorkspace(
                    (current) =>
                        removeNodeById(
                            current,
                            deletedPath
                        )
                );


                // --------------------------------------------
                // ABAS
                // --------------------------------------------

                setOpenTabs(
                    (current) =>
                        current.filter(
                            (tab) =>
                                !pathBelongsToNode(
                                    tab.id,
                                    deletedPath
                                )
                        )
                );


                // --------------------------------------------
                // ARQUIVO ATIVO
                // --------------------------------------------

                setActiveFileId(
                    (current) => {

                        if (
                            pathBelongsToNode(
                                current,
                                deletedPath
                            )
                        ) {
                            return "";
                        }


                        return current;
                    }
                );


                // --------------------------------------------
                // DIRTY FILES
                // --------------------------------------------

                setDirtyFiles(
                    (current) => {

                        const next =
                            new Set<string>();


                        current.forEach(
                            (path) => {

                                if (
                                    !pathBelongsToNode(
                                        path,
                                        deletedPath
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


                // --------------------------------------------
                // PASTA SELECIONADA
                // --------------------------------------------

                setSelectedFolderId(
                    (current) => {

                        if (
                            current &&
                            pathBelongsToNode(
                                current,
                                deletedPath
                            )
                        ) {
                            return null;
                        }


                        return current;
                    }
                );


                // --------------------------------------------
                // PASTAS EXPANDIDAS
                // --------------------------------------------

                setExpandedFolders(
                    (current) => {

                        const next =
                            new Set<string>();


                        current.forEach(
                            (path) => {

                                if (
                                    !pathBelongsToNode(
                                        path,
                                        deletedPath
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

                        `[DUET] Excluído: ${deletedPath}`,
                    ]
                );

            } catch (err: any) {

                console.error(
                    "Erro ao excluir item:",
                    err
                );


                if (
                    err?.response?.status ===
                    423
                ) {

                    await carregarCheckout(
                        false
                    );
                }


                const mensagem =
                    getApiErrorMessage(
                        err,
                        "Não foi possível excluir o item."
                    );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] ERRO AO EXCLUIR: ${mensagem}`,
                    ]
                );
            }
        };


    // ========================================================
    // EXPANDIR / RECOLHER
    // ========================================================

    const toggleFolder =
        (
            folderId: string
        ) => {

            setExpandedFolders(
                (current) => {

                    const next =
                        new Set(
                            current
                        );


                    if (
                        next.has(
                            folderId
                        )
                    ) {

                        next.delete(
                            folderId
                        );

                    } else {

                        next.add(
                            folderId
                        );
                    }


                    return next;
                }
            );
        };


    return {
        // Árvore.
        workspace,
        setWorkspace,

        // Arquivo ativo.
        activeFileId,
        setActiveFileId,
        activeFile,

        // Abas.
        openTabs,
        setOpenTabs,

        // Explorer.
        expandedFolders,
        setExpandedFolders,

        selectedFolderId,
        setSelectedFolderId,

        // Alterações.
        dirtyFiles,
        setDirtyFiles,
        dirty,

        // Operações.
        openFile,
        closeTab,
        handleEditorChange,
        saveWorkspace,

        createFile,
        createFolder,

        createFileInFolder,
        createFolderInFolder,

        renomearItem,
        excluirItem,

        toggleFolder,
    };
}
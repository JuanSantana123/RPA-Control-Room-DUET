import {
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";
import {
    BookOpen,
    ChevronDown,
    ChevronRight,
    FileCode2,
    Folder,
    FolderPlus,
    MoreVertical,
    Move,
    Pencil,
    Plus,
    RefreshCw,
    Search,
    Trash2,
    X,
} from "lucide-react";

import api from "../../services/api";
// Componente visual utilizado para selecionar a pasta de destino.
import LibraryFolderPicker from "./LibraryFolderPicker";

// Importa somente o tipo TypeScript.
// `LibraryFolderOption` não existe em runtime e, por isso,
// deve ser importado com `import type`.
import type {
    LibraryFolderOption,
} from "./LibraryFolderPicker";
import "./LibrariesPanel.css";

// ============================================================
// TIPOS - CATÁLOGO GLOBAL DE BIBLIOTECAS
// ============================================================

// Pasta organizacional do catálogo global.
//
// IMPORTANTE:
// esta estrutura organiza Libraries no Control Room. Ela NÃO representa
// as pastas Python existentes dentro de uma biblioteca.
interface LibraryFolderTreeNode {
    type: "folder";
    id: number;
    name: string;
    parent_id: number | null;
    created_by: number;
    created_at: string | null;
    updated_at: string | null;
    is_active: boolean;
    children: LibraryTreeNode[];
}

// Biblioteca reutilizável exibida no catálogo global.
interface LibraryCatalogItem {
    type: "library";
    id: number;
    name: string;
    import_name: string;
    description: string | null;
    folder_id: number | null;
    created_by: number;
    created_at: string | null;
    updated_at: string | null;
    is_active: boolean;
}

type LibraryTreeNode =
    | LibraryFolderTreeNode
    | LibraryCatalogItem;

// ============================================================
// VERSÃO PUBLICADA DA BIBLIOTECA
// ============================================================
//
// Cada LibraryVersion representa um snapshot imutável.
//
// is_production:
//     true quando esta é a versão atualmente vigente em Produção.
// ============================================================

interface LibraryVersionItem {
    id: number;
    library_id: number;
    version: string;
    source_type: string;
    source_robot_id: number | null;
    source_robot_version: number | null;
    source_path: string | null;
    file_hash: string;
    published_by: number;
    published_at: string | null;
    is_active: boolean;

    // Retornado atualmente pelo backend.
    is_production: boolean;
}



// ============================================================
// ROBOTS QUE UTILIZAM A LIBRARY
// ============================================================
//
// Representa o vínculo oficial registrado no Release:
//
//     Robot versão X
//         ↓
//     Library versão Y
//
// A consulta considera somente a versão ATUAL publicada
// de cada Robot.
// ============================================================

interface LibraryRobotUsage {
    robot_id: number;
    robot_name: string;
    robot_version: number;

    library_version_id: number;
    library_version: string;

    // true:
    //     o Robot utiliza exatamente a LibraryVersion
    //     atualmente marcada como Produção.
    //
    // false:
    //     o Robot ainda está vinculado a uma versão anterior.
    uses_production_version: boolean;
}


interface LibraryRobotsResponse {
    status: string;

    library: {
        id: number;
        name: string;
        import_name: string;
        production_version_id: number | null;
        production_version: string | null;
    };

    total_robots: number;

    robots: LibraryRobotUsage[];
}
// ============================================================
// ÁRVORE DE ARQUIVOS DO SNAPSHOT PUBLICADO
// ============================================================
//
// Esta árvore NÃO representa a Working Copy do Desenvolvimento.
//
// Ela vem diretamente do ZIP imutável da LibraryVersion.
// ============================================================

interface LibrarySnapshotNode {
    type: "folder" | "file";
    name: string;
    path: string;
    children?: LibrarySnapshotNode[];
}

type FolderEditorMode = "create" | "rename" | null;
type LibraryEditorMode = "create" | "edit" | null;

type FolderPickerMode =
    | "folder-create-location"
    | "folder-move"
    | "library-create-location"
    | "library-move"
    | null;

type ConfirmationState =
    | {
        kind: "delete-folder";
        folder: LibraryFolderTreeNode;
    }
    | {
        kind: "deactivate-library";
        library: LibraryCatalogItem;
    }
    | null;

// ============================================================
// FUNÇÕES AUXILIARES - ERROS / ÁRVORE
// ============================================================

// Extrai uma mensagem amigável de respostas do FastAPI/Axios sem
// assumir que response.data.detail sempre será uma string.
function obterMensagemErro(
    error: unknown,
    fallback: string
): string {
    const candidate = error as {
        response?: {
            data?: {
                detail?: unknown;
                message?: unknown;
            };
        };
    };

    const detail = candidate.response?.data?.detail;

    if (typeof detail === "string") {
        return detail;
    }

    if (
        detail &&
        typeof detail === "object" &&
        "message" in detail
    ) {
        const detailMessage = (
            detail as { message?: unknown }
        ).message;

        if (typeof detailMessage === "string") {
            return detailMessage;
        }
    }

    const message = candidate.response?.data?.message;

    if (typeof message === "string") {
        return message;
    }

    return fallback;
}

// Retorna somente pastas existentes em determinado nível da árvore.
function obterPastasDoNivel(
    nodes: LibraryTreeNode[]
): LibraryFolderTreeNode[] {
    return nodes.filter(
        (node): node is LibraryFolderTreeNode =>
            node.type === "folder"
    );
}

// Converte a árvore completa para o formato independente utilizado pelo
// LibraryFolderPicker. Bibliotecas são descartadas porque não são destinos.
function converterParaFolderOptions(
    nodes: LibraryTreeNode[]
): LibraryFolderOption[] {
    return obterPastasDoNivel(nodes).map((folder) => ({
        id: folder.id,
        name: folder.name,
        parent_id: folder.parent_id,
        children: converterParaFolderOptions(folder.children),
    }));
}

// Localiza uma pasta em qualquer profundidade.
function encontrarPasta(
    nodes: LibraryTreeNode[],
    folderId: number
): LibraryFolderTreeNode | null {
    for (const node of nodes) {
        if (node.type !== "folder") {
            continue;
        }

        if (node.id === folderId) {
            return node;
        }

        const encontrada = encontrarPasta(
            node.children,
            folderId
        );

        if (encontrada) {
            return encontrada;
        }
    }

    return null;
}

// Localiza uma Library pelo ID em qualquer profundidade.
function encontrarLibrary(
    nodes: LibraryTreeNode[],
    libraryId: number
): LibraryCatalogItem | null {
    for (const node of nodes) {
        if (
            node.type === "library" &&
            node.id === libraryId
        ) {
            return node;
        }

        if (node.type === "folder") {
            const encontrada = encontrarLibrary(
                node.children,
                libraryId
            );

            if (encontrada) {
                return encontrada;
            }
        }
    }

    return null;
}

// Monta o caminho organizacional de uma pasta.
// Exemplo: Corporativo / Financeiro / Cobrança.
function encontrarCaminhoPasta(
    nodes: LibraryTreeNode[],
    folderId: number,
    caminhoAtual: string[] = []
): string[] | null {
    for (const node of nodes) {
        if (node.type !== "folder") {
            continue;
        }

        const caminho = [
            ...caminhoAtual,
            node.name,
        ];

        if (node.id === folderId) {
            return caminho;
        }

        const encontrado = encontrarCaminhoPasta(
            node.children,
            folderId,
            caminho
        );

        if (encontrado) {
            return encontrado;
        }
    }

    return null;
}

// Obtém a própria pasta e todas as descendentes.
// Esses IDs ficam desabilitados ao mover uma pasta para impedir ciclos
// já no frontend. O backend continua sendo a validação definitiva.
function obterIdsDescendentes(
    folder: LibraryFolderTreeNode | null
): Set<number> {
    const ids = new Set<number>();

    const visitar = (
        atual: LibraryFolderTreeNode
    ) => {
        ids.add(atual.id);

        obterPastasDoNivel(
            atual.children
        ).forEach(visitar);
    };

    if (folder) {
        visitar(folder);
    }

    return ids;
}

// Filtra a árvore preservando ancestrais dos resultados.
function filtrarArvore(
    nodes: LibraryTreeNode[],
    searchValue: string
): LibraryTreeNode[] {
    const termo = searchValue
        .trim()
        .toLocaleLowerCase("pt-BR");

    if (!termo) {
        return nodes;
    }

    const resultado: LibraryTreeNode[] = [];

    for (const node of nodes) {
        if (node.type === "library") {
            const combina =
                node.name
                    .toLocaleLowerCase("pt-BR")
                    .includes(termo) ||
                node.import_name
                    .toLocaleLowerCase("pt-BR")
                    .includes(termo);

            if (combina) {
                resultado.push(node);
            }

            continue;
        }

        const filhosFiltrados = filtrarArvore(
            node.children,
            searchValue
        );

        const pastaCombina = node.name
            .toLocaleLowerCase("pt-BR")
            .includes(termo);

        if (
            pastaCombina ||
            filhosFiltrados.length > 0
        ) {
            resultado.push({
                ...node,
                children: pastaCombina
                    ? node.children
                    : filhosFiltrados,
            });
        }
    }

    return resultado;
}

// Formata a data ISO retornada pelo backend para leitura humana.
function formatarData(
    value: string | null
): string {
    if (!value) {
        return "-";
    }

    const date = new Date(value);

    if (Number.isNaN(date.getTime())) {
        return value;
    }

    return new Intl.DateTimeFormat(
        "pt-BR",
        {
            dateStyle: "short",
            timeStyle: "short",
        }
    ).format(date);
}

// ============================================================
// COMPONENTE PRINCIPAL
// ============================================================

function LibrariesPanel() {
    // ========================================================
    // ESTADOS - CATÁLOGO
    // ========================================================

    const [libraryTree, setLibraryTree] =
        useState<LibraryTreeNode[]>([]);

    const [libraryFolderCount, setLibraryFolderCount] =
        useState(0);

    const [libraryCount, setLibraryCount] =
        useState(0);

    const [loadingLibraries, setLoadingLibraries] =
        useState(true);

    const [libraryError, setLibraryError] =
        useState("");

    const [librarySuccess, setLibrarySuccess] =
        useState("");

    const [librarySearch, setLibrarySearch] =
        useState("");

    const [expandedFolders, setExpandedFolders] =
        useState<Set<number>>(new Set());

    // Evita reabrir automaticamente as pastas raiz após cada refresh.
    const catalogInitialized = useRef(false);

    // ========================================================
    // ESTADOS - SELEÇÃO / DETALHES
    // ========================================================

    const [selectedFolder, setSelectedFolder] =
        useState<LibraryFolderTreeNode | null>(null);

    const [selectedLibrary, setSelectedLibrary] =
        useState<LibraryCatalogItem | null>(null);

    const [versions, setVersions] =
        useState<LibraryVersionItem[]>([]);

    const [loadingVersions, setLoadingVersions] =
        useState(false);

    // ========================================================
    // ESTADOS - ROBOTS QUE UTILIZAM A LIBRARY
    // ========================================================

    // Robots cuja versão atual publicada utiliza
    // a Library atualmente selecionada.
    const [libraryRobots, setLibraryRobots] =
        useState<LibraryRobotUsage[]>([]);


    // Versão atualmente vigente em Produção para a Library.
    //
    // É usada somente como informação visual.
    // A versão efetivamente usada por cada Robot vem
    // individualmente de libraryRobots.
    const [
        libraryProductionVersion,
        setLibraryProductionVersion
    ] = useState<string | null>(null);


    // Controla somente o carregamento da consulta inversa
    // Library -> Robots.
    const [
        loadingLibraryRobots,
        setLoadingLibraryRobots
    ] = useState(false);

    // ========================================================
    // ESTADOS - SNAPSHOT DA VERSÃO PUBLICADA
    // ========================================================
    //
    // Guarda qual versão está visualmente aberta e a árvore
    // carregada diretamente do artefato imutável do backend.
    // ========================================================

    const [selectedVersionId, setSelectedVersionId] =
        useState<number | null>(null);

    const [versionTree, setVersionTree] =
        useState<LibrarySnapshotNode[]>([]);

    const [loadingVersionTree, setLoadingVersionTree] =
        useState(false);


    // Pastas expandidas dentro do snapshot publicado.
    //
    // A chave é o caminho completo no ZIP, por exemplo:
    //
    //     teste/services
    //     teste/services/api
    const [expandedVersionFolders, setExpandedVersionFolders] =
        useState<Set<string>>(
            new Set()
        );
    const [openFolderMenu, setOpenFolderMenu] =
        useState<number | null>(null);

    const [openLibraryMenu, setOpenLibraryMenu] =
        useState<number | null>(null);

    // ========================================================
    // ESTADOS - MODAL DE PASTA
    // ========================================================

    const [folderEditorMode, setFolderEditorMode] =
        useState<FolderEditorMode>(null);

    const [folderEditorItem, setFolderEditorItem] =
        useState<LibraryFolderTreeNode | null>(null);

    const [folderName, setFolderName] =
        useState("");

    const [folderDestinationId, setFolderDestinationId] =
        useState<number | null>(null);

    const [savingFolder, setSavingFolder] =
        useState(false);

    // ========================================================
    // ESTADOS - MODAL DE LIBRARY
    // ========================================================

    const [libraryEditorMode, setLibraryEditorMode] =
        useState<LibraryEditorMode>(null);

    const [libraryEditorItem, setLibraryEditorItem] =
        useState<LibraryCatalogItem | null>(null);

    const [libraryName, setLibraryName] =
        useState("");

    const [libraryImportName, setLibraryImportName] =
        useState("");

    const [libraryDescription, setLibraryDescription] =
        useState("");

    const [libraryDestinationId, setLibraryDestinationId] =
        useState<number | null>(null);

    const [savingLibrary, setSavingLibrary] =
        useState(false);

    // ========================================================
    // ESTADOS - SELETOR DE PASTA
    // ========================================================

    const [folderPickerMode, setFolderPickerMode] =
        useState<FolderPickerMode>(null);

    const [pickerSelectedFolderId, setPickerSelectedFolderId] =
        useState<number | null>(null);

    const [pickerFolderItem, setPickerFolderItem] =
        useState<LibraryFolderTreeNode | null>(null);

    const [pickerLibraryItem, setPickerLibraryItem] =
        useState<LibraryCatalogItem | null>(null);

    const [savingPicker, setSavingPicker] =
        useState(false);

    // ========================================================
    // ESTADO - CONFIRMAÇÃO DE AÇÃO DESTRUTIVA
    // ========================================================

    const [confirmation, setConfirmation] =
        useState<ConfirmationState>(null);

    const [confirmingAction, setConfirmingAction] =
        useState(false);

    // ========================================================
    // DADOS DERIVADOS
    // ========================================================

    const folderOptions = useMemo(
        () => converterParaFolderOptions(libraryTree),
        [libraryTree]
    );

    const visibleTree = useMemo(
        () => filtrarArvore(libraryTree, librarySearch),
        [libraryTree, librarySearch]
    );

    const selectedFolderPath = useMemo(() => {
        if (!selectedFolder) {
            return [];
        }

        return encontrarCaminhoPasta(
            libraryTree,
            selectedFolder.id
        ) || [selectedFolder.name];
    }, [libraryTree, selectedFolder]);

    const selectedLibraryPath = useMemo(() => {
        if (
            !selectedLibrary ||
            selectedLibrary.folder_id === null
        ) {
            return [];
        }

        return encontrarCaminhoPasta(
            libraryTree,
            selectedLibrary.folder_id
        ) || [];
    }, [libraryTree, selectedLibrary]);

    const blockedPickerFolderIds = useMemo(() => {
        if (folderPickerMode !== "folder-move") {
            return new Set<number>();
        }

        return obterIdsDescendentes(pickerFolderItem);
    }, [folderPickerMode, pickerFolderItem]);

    // ========================================================
    // CARREGAMENTO DO CATÁLOGO
    // ========================================================

    const carregarBibliotecas = async () => {
        try {
            setLoadingLibraries(true);
            setLibraryError("");

            const response = await api.get(
                "/libraries/tree"
            );

            const tree: LibraryTreeNode[] =
                response.data?.tree || [];

            setLibraryTree(tree);
            setLibraryFolderCount(
                response.data?.total_folders || 0
            );
            setLibraryCount(
                response.data?.total_libraries || 0
            );

            // Na primeira abertura, deixa as pastas raiz expandidas para
            // o usuário enxergar imediatamente a organização do catálogo.
            if (!catalogInitialized.current) {
                setExpandedFolders(
                    new Set(
                        obterPastasDoNivel(tree).map(
                            (folder) => folder.id
                        )
                    )
                );

                catalogInitialized.current = true;
            }

            // Atualiza referências selecionadas depois de qualquer mutação.
            setSelectedFolder((atual) => {
                if (!atual) {
                    return null;
                }

                return encontrarPasta(tree, atual.id);
            });

            setSelectedLibrary((atual) => {
                if (!atual) {
                    return null;
                }

                return encontrarLibrary(tree, atual.id);
            });

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
            setLoadingLibraries(false);
        }
    };

    // Carrega as versões publicadas da Library selecionada.
    const carregarVersoes = async (
        library: LibraryCatalogItem
    ) => {
        try {
            setLoadingVersions(true);
            setLibraryError("");

            const response = await api.get(
                `/libraries/${library.id}/versions`,
                {
                    params: {
                        include_inactive: true,
                    },
                }
            );

            setVersions(
                response.data?.versions || []
            );

        } catch (error) {
            console.error(
                "Erro ao carregar versões da biblioteca:",
                error
            );

            setVersions([]);

            setLibraryError(
                obterMensagemErro(
                    error,
                    "Não foi possível carregar as versões desta biblioteca."
                )
            );

        } finally {
            setLoadingVersions(false);
        }
    };




// ========================================================
// CARREGAR ROBOTS QUE UTILIZAM A LIBRARY
// ========================================================
//
// Consulta o relacionamento inverso:
//
//     Library
//         ↓
//     Robots que dependem dela
//
// O backend considera somente a versão ATUAL
// publicada de cada Robot.
// ========================================================

const carregarRobosDaLibrary = async (
    library: LibraryCatalogItem
) => {

    try {

        setLoadingLibraryRobots(true);

        const response =
            await api.get<LibraryRobotsResponse>(
                `/libraries/${library.id}/robots`
            );


        // Guarda somente os Robots retornados para
        // a Library atualmente selecionada.
        setLibraryRobots(
            response.data?.robots || []
        );


        // Guarda também qual é a versão oficial de
        // Produção desta Library.
        setLibraryProductionVersion(
            response.data?.library?.production_version ||
            null
        );


    } catch (error) {

        console.error(
            "Erro ao carregar Robots da biblioteca:",
            error
        );


        // Evita manter na tela Robots pertencentes
        // à Library anteriormente selecionada.
        setLibraryRobots([]);

        setLibraryProductionVersion(null);


        setLibraryError(
            obterMensagemErro(
                error,
                "Não foi possível carregar os Robots que utilizam esta biblioteca."
            )
        );


    } finally {

        setLoadingLibraryRobots(false);
    }
};


    // ========================================================
    // CARREGAR SNAPSHOT DE UMA VERSÃO PUBLICADA
    // ========================================================

    const carregarArvoreVersao = async (
        library: LibraryCatalogItem,
        version: LibraryVersionItem
    ) => {

        // ----------------------------------------------------
        // CLICOU NOVAMENTE NA MESMA VERSÃO
        // ----------------------------------------------------
        //
        // Funciona como expandir/recolher.
        // ----------------------------------------------------

        if (
            selectedVersionId === version.id
        ) {
            setSelectedVersionId(null);
            setVersionTree([]);
            setExpandedVersionFolders(
                new Set()
            );

            return;
        }


        try {

            setLoadingVersionTree(true);
            setLibraryError("");

            // A versão passa a aparecer imediatamente como selecionada.
            setSelectedVersionId(
                version.id
            );

            setVersionTree([]);

            setExpandedVersionFolders(
                new Set()
            );


            // ------------------------------------------------
            // SNAPSHOT IMUTÁVEL
            // ------------------------------------------------
            //
            // Este endpoint lê o ZIP publicado.
            //
            // NÃO consulta o workspace de Desenvolvimento.
            // ------------------------------------------------

            const response =
                await api.get(
                    `/libraries/${library.id}/versions/${version.id}/tree`
                );


            let tree: LibrarySnapshotNode[] =
                response.data?.tree || [];


            // ------------------------------------------------
            // REMOVE O NAMESPACE DUPLICADO DA VISUALIZAÇÃO
            // ------------------------------------------------
            //
            // O ZIP correto possui:
            //
            // teste/
            //     __init__.py
            //     services/
            //
            // Como a tela já está dentro da Library "teste",
            // não precisamos mostrar novamente:
            //
            // 1.0.0
            //   └── teste
            //
            // Mostramos diretamente:
            //
            // 1.0.0
            //   └── Código
            //       ├── __init__.py
            //       └── services
            // ------------------------------------------------

            if (
                tree.length === 1 &&
                tree[0].type === "folder" &&
                tree[0].name === library.import_name
            ) {
                tree =
                    tree[0].children || [];
            }


            setVersionTree(
                tree
            );


            // ------------------------------------------------
            // ABRE AS PASTAS DO PRIMEIRO NÍVEL
            // ------------------------------------------------
            //
            // Facilita a leitura inicial sem expandir toda a
            // árvore recursivamente.
            // ------------------------------------------------

            setExpandedVersionFolders(
                new Set(
                    tree
                        .filter(
                            (node) =>
                                node.type === "folder"
                        )
                        .map(
                            (node) =>
                                node.path
                        )
                )
            );


        } catch (error) {

            console.error(
                "Erro ao carregar snapshot da versão:",
                error
            );

            setVersionTree([]);

            setLibraryError(
                obterMensagemErro(
                    error,
                    "Não foi possível carregar os arquivos desta versão."
                )
            );

        } finally {

            setLoadingVersionTree(
                false
            );
        }
    };


    // ========================================================
    // EXPANDIR / RECOLHER PASTA DO SNAPSHOT
    // ========================================================

    const alternarPastaVersao = (
        path: string
    ) => {

        setExpandedVersionFolders(
            (atual) => {

                const novo =
                    new Set(
                        atual
                    );

                if (
                    novo.has(path)
                ) {
                    novo.delete(
                        path
                    );

                } else {

                    novo.add(
                        path
                    );
                }

                return novo;
            }
        );
    };

    useEffect(() => {
        void carregarBibliotecas();
    }, []);

    // ========================================================
    // SELEÇÃO / EXPANSÃO
    // ========================================================

    const alternarPasta = (
        folderId: number
    ) => {
        setExpandedFolders((atual) => {
            const novo = new Set(atual);

            if (novo.has(folderId)) {
                novo.delete(folderId);
            } else {
                novo.add(folderId);
            }

            return novo;
        });
    };

    const selecionarPasta = (
        folder: LibraryFolderTreeNode
    ) => {

        setSelectedFolder(folder);

        // Nenhuma Library permanece selecionada.
        setSelectedLibrary(null);

        // Limpa informações pertencentes à Library anterior.
        setVersions([]);
        setLibraryRobots([]);
        setLibraryProductionVersion(null);

        setOpenFolderMenu(null);
        setOpenLibraryMenu(null);
    };





    const selecionarLibrary = async (
        library: LibraryCatalogItem
    ) => {

        setSelectedLibrary(
            library
        );

        setSelectedFolder(
            null
        );

        setOpenFolderMenu(
            null
        );

        setOpenLibraryMenu(
            null
        );


        // ----------------------------------------------------
        // LIMPA SNAPSHOT DA LIBRARY ANTERIOR
        // ----------------------------------------------------
        //
        // Uma árvore pertencente à biblioteca anterior nunca
        // deve permanecer aberta quando outra Library é escolhida.
        // ----------------------------------------------------

        setSelectedVersionId(
            null
        );

        setVersionTree(
            []
        );

        setExpandedVersionFolders(
            new Set()
        );


        // Limpa os dados da Library anterior antes das novas consultas.
        setLibraryRobots([]);
        setLibraryProductionVersion(null);


        // Versões publicadas e Robots consumidores são informações
        // independentes, portanto podem ser carregadas em paralelo.
        await Promise.all([
            carregarVersoes(
                library
            ),

            carregarRobosDaLibrary(
                library
            ),
        ]);
    };
    // ========================================================
    // MODAL - PASTA
    // ========================================================

    const fecharFolderEditor = () => {
        setFolderEditorMode(null);
        setFolderEditorItem(null);
        setFolderName("");
        setFolderDestinationId(null);
        setSavingFolder(false);
    };

    const abrirCriacaoPasta = (
        parentId: number | null
    ) => {
        setLibraryError("");
        setLibrarySuccess("");
        setOpenFolderMenu(null);

        setFolderEditorMode("create");
        setFolderEditorItem(null);
        setFolderName("");
        setFolderDestinationId(parentId);
    };

    const abrirRenomearPasta = (
        folder: LibraryFolderTreeNode
    ) => {
        setLibraryError("");
        setLibrarySuccess("");
        setOpenFolderMenu(null);

        setFolderEditorMode("rename");
        setFolderEditorItem(folder);
        setFolderName(folder.name);
        setFolderDestinationId(folder.parent_id);
    };

    const salvarPasta = async () => {
        const nome = folderName.trim();

        if (!folderEditorMode) {
            return;
        }

        if (!nome) {
            setLibraryError(
                "Informe um nome para a pasta."
            );
            return;
        }

        if (
            folderEditorMode === "rename" &&
            !folderEditorItem
        ) {
            setLibraryError(
                "Não foi possível identificar a pasta selecionada."
            );
            return;
        }

        try {
            setSavingFolder(true);
            setLibraryError("");
            setLibrarySuccess("");

            if (folderEditorMode === "create") {
                await api.post(
                    "/libraries/folders",
                    {
                        name: nome,
                        parent_id: folderDestinationId,
                    }
                );

                if (folderDestinationId !== null) {
                    setExpandedFolders((atual) => {
                        const novo = new Set(atual);
                        novo.add(folderDestinationId);
                        return novo;
                    });
                }

                setLibrarySuccess(
                    "Pasta criada com sucesso."
                );

            } else {
                await api.patch(
                    `/libraries/folders/${folderEditorItem!.id}`,
                    {
                        name: nome,
                    }
                );

                setLibrarySuccess(
                    "Pasta renomeada com sucesso."
                );
            }

            fecharFolderEditor();
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
            setSavingFolder(false);
        }
    };

    // ========================================================
    // MODAL - LIBRARY
    // ========================================================

    const fecharLibraryEditor = () => {
        setLibraryEditorMode(null);
        setLibraryEditorItem(null);
        setLibraryName("");
        setLibraryImportName("");
        setLibraryDescription("");
        setLibraryDestinationId(null);
        setSavingLibrary(false);
    };

    const abrirCriacaoLibrary = (
        folderId: number | null
    ) => {
        setLibraryError("");
        setLibrarySuccess("");
        setOpenFolderMenu(null);
        setOpenLibraryMenu(null);

        setLibraryEditorMode("create");
        setLibraryEditorItem(null);
        setLibraryName("");
        setLibraryImportName("");
        setLibraryDescription("");
        setLibraryDestinationId(folderId);
    };

    const abrirEdicaoLibrary = (
        library: LibraryCatalogItem
    ) => {
        setLibraryError("");
        setLibrarySuccess("");
        setOpenLibraryMenu(null);

        setLibraryEditorMode("edit");
        setLibraryEditorItem(library);
        setLibraryName(library.name);
        setLibraryImportName(library.import_name);
        setLibraryDescription(
            library.description || ""
        );
        setLibraryDestinationId(library.folder_id);
    };

    const salvarLibrary = async () => {
        if (!libraryEditorMode) {
            return;
        }

        const nome = libraryName.trim();
        const importName = libraryImportName.trim();

        if (!nome) {
            setLibraryError(
                "Informe o nome da biblioteca."
            );
            return;
        }

        if (
            libraryEditorMode === "create" &&
            !importName
        ) {
            setLibraryError(
                "Informe o import_name da biblioteca."
            );
            return;
        }

        try {
            setSavingLibrary(true);
            setLibraryError("");
            setLibrarySuccess("");

            if (libraryEditorMode === "create") {
                const response = await api.post(
                    "/libraries",
                    {
                        name: nome,
                        import_name: importName,
                        description:
                            libraryDescription.trim() || null,
                        folder_id: libraryDestinationId,
                    }
                );

                const criada = response.data?.library;

                if (criada) {
                    setSelectedLibrary({
                        ...criada,
                        type: "library",
                    });
                    setSelectedFolder(null);
                }

                if (libraryDestinationId !== null) {
                    setExpandedFolders((atual) => {
                        const novo = new Set(atual);
                        novo.add(libraryDestinationId);
                        return novo;
                    });
                }

                setLibrarySuccess(
                    "Biblioteca criada com sucesso."
                );

            } else {
                await api.patch(
                    `/libraries/${libraryEditorItem!.id}`,
                    {
                        name: nome,
                        description:
                            libraryDescription.trim() || null,
                    }
                );

                setLibrarySuccess(
                    "Biblioteca atualizada com sucesso."
                );
            }

            // O refresh abaixo atualiza a seleção usando a árvore
            // retornada pelo backend. Não reutilizamos a árvore antiga
            // para evitar mostrar metadados desatualizados.
            fecharLibraryEditor();
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
            setSavingLibrary(false);
        }
    };

    // ========================================================
    // SELETOR DE PASTA
    // ========================================================

    const abrirPickerCriacaoPasta = () => {
        setPickerSelectedFolderId(
            folderDestinationId
        );
        setPickerFolderItem(null);
        setPickerLibraryItem(null);
        setFolderPickerMode(
            "folder-create-location"
        );
    };

    const abrirPickerMoverPasta = (
        folder: LibraryFolderTreeNode
    ) => {
        setOpenFolderMenu(null);
        setPickerFolderItem(folder);
        setPickerLibraryItem(null);
        setPickerSelectedFolderId(
            folder.parent_id
        );
        setFolderPickerMode("folder-move");
    };

    const abrirPickerCriacaoLibrary = () => {
        setPickerSelectedFolderId(
            libraryDestinationId
        );
        setPickerFolderItem(null);
        setPickerLibraryItem(null);
        setFolderPickerMode(
            "library-create-location"
        );
    };

    const abrirPickerMoverLibrary = (
        library: LibraryCatalogItem
    ) => {
        setOpenLibraryMenu(null);
        setPickerFolderItem(null);
        setPickerLibraryItem(library);
        setPickerSelectedFolderId(
            library.folder_id
        );
        setFolderPickerMode("library-move");
    };

    const fecharPicker = () => {
        if (savingPicker) {
            return;
        }

        setFolderPickerMode(null);
        setPickerFolderItem(null);
        setPickerLibraryItem(null);
        setPickerSelectedFolderId(null);
    };

    const confirmarPicker = async () => {
        if (!folderPickerMode) {
            return;
        }

        // Nos formulários de criação o picker apenas devolve o local.
        // A persistência acontece quando o usuário salva o formulário.
        if (
            folderPickerMode === "folder-create-location"
        ) {
            setFolderDestinationId(
                pickerSelectedFolderId
            );
            fecharPicker();
            return;
        }

        if (
            folderPickerMode === "library-create-location"
        ) {
            setLibraryDestinationId(
                pickerSelectedFolderId
            );
            fecharPicker();
            return;
        }

        try {
            setSavingPicker(true);
            setLibraryError("");
            setLibrarySuccess("");

            if (
                folderPickerMode === "folder-move"
            ) {
                if (!pickerFolderItem) {
                    throw new Error(
                        "Pasta não identificada."
                    );
                }

                await api.patch(
                    `/libraries/folders/${pickerFolderItem.id}`,
                    {
                        parent_id: pickerSelectedFolderId,
                    }
                );

                if (pickerSelectedFolderId !== null) {
                    setExpandedFolders((atual) => {
                        const novo = new Set(atual);
                        novo.add(pickerSelectedFolderId);
                        return novo;
                    });
                }

                setLibrarySuccess(
                    "Pasta movida com sucesso."
                );

            } else {
                if (!pickerLibraryItem) {
                    throw new Error(
                        "Biblioteca não identificada."
                    );
                }

                await api.patch(
                    `/libraries/${pickerLibraryItem.id}/folder`,
                    {
                        folder_id: pickerSelectedFolderId,
                    }
                );

                if (pickerSelectedFolderId !== null) {
                    setExpandedFolders((atual) => {
                        const novo = new Set(atual);
                        novo.add(pickerSelectedFolderId);
                        return novo;
                    });
                }

                setLibrarySuccess(
                    "Biblioteca movida com sucesso."
                );
            }

            setFolderPickerMode(null);
            setPickerFolderItem(null);
            setPickerLibraryItem(null);
            setPickerSelectedFolderId(null);

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
            setSavingPicker(false);
        }
    };

    // ========================================================
    // AÇÕES DESTRUTIVAS
    // ========================================================

    const confirmarAcaoDestrutiva = async () => {
        if (!confirmation) {
            return;
        }

        try {
            setConfirmingAction(true);
            setLibraryError("");
            setLibrarySuccess("");

            if (confirmation.kind === "delete-folder") {
                await api.delete(
                    `/libraries/folders/${confirmation.folder.id}`
                );

                if (
                    selectedFolder?.id ===
                    confirmation.folder.id
                ) {
                    setSelectedFolder(null);
                }

                setLibrarySuccess(
                    "Pasta excluída com sucesso."
                );

            } else {
                await api.delete(
                    `/libraries/${confirmation.library.id}`
                );

                if (
                    selectedLibrary?.id ===
                    confirmation.library.id
                ) {
                    setSelectedLibrary(null);
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
            setConfirmingAction(false);
        }
    };





    // ========================================================
    // RENDERIZAÇÃO - SNAPSHOT DE LIBRARYVERSION
    // ========================================================
    //
    // Esta árvore é somente leitura.
    //
    // Não existem aqui:
    // - editar;
    // - excluir;
    // - renomear;
    // - criar arquivo;
    // - criar pasta.
    //
    // Afinal, uma versão publicada é imutável.
    // ========================================================

    const renderizarNoSnapshot = (
        node: LibrarySnapshotNode,
        level: number = 0
    ): React.ReactNode => {

        const paddingLeft =
            12 + level * 18;


        // ----------------------------------------------------
        // PASTA
        // ----------------------------------------------------

        if (
            node.type === "folder"
        ) {

            const expanded =
                expandedVersionFolders.has(
                    node.path
                );

            return (
                <div
                    key={node.path}
                >
                    <button
                        type="button"

                        onClick={() =>
                            alternarPastaVersao(
                                node.path
                            )
                        }

                        style={{
                            width: "100%",
                            border: 0,
                            background: "transparent",
                            color: "inherit",
                            display: "flex",
                            alignItems: "center",
                            gap: "7px",
                            padding: `6px 8px 6px ${paddingLeft}px`,
                            cursor: "pointer",
                            textAlign: "left",
                        }}
                    >
                        {expanded ? (
                            <ChevronDown
                                size={14}
                            />
                        ) : (
                            <ChevronRight
                                size={14}
                            />
                        )}

                        <Folder
                            size={15}
                            strokeWidth={1.7}
                        />

                        <span>
                            {node.name}
                        </span>
                    </button>


                    {expanded &&
                        node.children?.map(
                            (child) =>
                                renderizarNoSnapshot(
                                    child,
                                    level + 1
                                )
                        )}
                </div>
            );
        }


        // ----------------------------------------------------
        // ARQUIVO
        // ----------------------------------------------------

        return (
            <div
                key={node.path}

                style={{
                    display: "flex",
                    alignItems: "center",
                    gap: "7px",
                    padding:
                        `6px 8px 6px ${paddingLeft + 21}px`,
                }}
            >
                <FileCode2
                    size={14}
                    strokeWidth={1.7}
                />

                <span>
                    {node.name}
                </span>
            </div>
        );
    };
    // ========================================================
    // RENDERIZAÇÃO RECURSIVA DA ÁRVORE
    // ========================================================

    const renderizarNo = (
        node: LibraryTreeNode,
        level: number = 0
    ): React.ReactNode => {
        if (node.type === "library") {
            const selected =
                selectedLibrary?.id === node.id;

            return (
                <div
                    key={`library-${node.id}`}
                    className="library-catalog-node"
                >
                    <div
                        className={`library-catalog-row library-catalog-library-row ${
                            selected
                                ? "library-catalog-row-selected"
                                : ""
                        }`}
                        style={{
                            paddingLeft: `${12 + level * 22}px`,
                        }}
                    >
                        <span className="library-catalog-spacer" />

                        <button
                            type="button"
                            className="library-catalog-main-button"
                            onClick={(event) => {
                                event.stopPropagation();
                                void selecionarLibrary(node);
                            }}
                        >
                            <FileCode2
                                className="library-catalog-library-icon"
                                size={16}
                                strokeWidth={1.8}
                            />

                            <span className="library-catalog-text">
                                <strong className="library-catalog-name">
                                    {node.name}
                                </strong>

                                <small className="library-catalog-import">
                                    {node.import_name}
                                </small>
                            </span>
                        </button>

                        <div className="library-catalog-actions">
                            <button
                                type="button"
                                className="library-catalog-menu-button"
                                aria-label={`Ações de ${node.name}`}
                                title="Ações da biblioteca"
                                onClick={(event) => {
                                    event.stopPropagation();
                                    setOpenFolderMenu(null);
                                    setOpenLibraryMenu(
                                        openLibraryMenu === node.id
                                            ? null
                                            : node.id
                                    );
                                }}
                            >
                                <MoreVertical
                                    size={16}
                                    strokeWidth={1.8}
                                />
                            </button>

                            {openLibraryMenu === node.id && (
                                <div
                                    className="library-catalog-context-menu"
                                    onClick={(event) =>
                                        event.stopPropagation()
                                    }
                                >
                                    <button
                                        type="button"
                                        onClick={() => {
                                            setOpenLibraryMenu(null);
                                            void selecionarLibrary(node);
                                        }}
                                    >
                                        <FileCode2 size={15} />
                                        <span>Ver detalhes</span>
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() =>
                                            abrirEdicaoLibrary(node)
                                        }
                                    >
                                        <Pencil size={15} />
                                        <span>Editar metadados</span>
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() =>
                                            abrirPickerMoverLibrary(node)
                                        }
                                    >
                                        <Move size={15} />
                                        <span>Mover para pasta</span>
                                    </button>

                                    <button
                                        type="button"
                                        className="library-context-danger"
                                        onClick={() => {
                                            setOpenLibraryMenu(null);
                                            setConfirmation({
                                                kind: "deactivate-library",
                                                library: node,
                                            });
                                        }}
                                    >
                                        <Trash2 size={15} />
                                        <span>Desativar</span>
                                    </button>
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            );
        }

        const hasChildren = node.children.length > 0;
        const forceExpanded = Boolean(librarySearch.trim());
        const expanded =
            forceExpanded ||
            expandedFolders.has(node.id);
        const selected =
            selectedFolder?.id === node.id;

        return (
            <div
                key={`folder-${node.id}`}
                className="library-catalog-node"
            >
                <div
                    className={`library-catalog-row ${
                        selected
                            ? "library-catalog-row-selected"
                            : ""
                    }`}
                    style={{
                        paddingLeft: `${12 + level * 22}px`,
                    }}
                >
                    {hasChildren ? (
                        <button
                            type="button"
                            className="library-catalog-expand"
                            onClick={(event) => {
                                event.stopPropagation();
                                alternarPasta(node.id);
                            }}
                            aria-label={
                                expanded
                                    ? `Recolher ${node.name}`
                                    : `Expandir ${node.name}`
                            }
                        >
                            {expanded ? (
                                <ChevronDown size={15} />
                            ) : (
                                <ChevronRight size={15} />
                            )}
                        </button>
                    ) : (
                        <span className="library-catalog-spacer" />
                    )}

                    <button
                        type="button"
                        className="library-catalog-main-button"
                        onClick={(event) => {
                            event.stopPropagation();
                            selecionarPasta(node);
                        }}
                    >
                        <Folder
                            className="library-catalog-folder-icon"
                            size={16}
                            strokeWidth={1.8}
                        />

                        <span className="library-catalog-text">
                            <strong className="library-catalog-name">
                                {node.name}
                            </strong>

                            <small className="library-catalog-child-count">
                                {node.children.length} itens
                            </small>
                        </span>
                    </button>

                    <div className="library-catalog-actions">
                        <button
                            type="button"
                            className="library-catalog-menu-button"
                            aria-label={`Ações da pasta ${node.name}`}
                            title="Ações da pasta"
                            onClick={(event) => {
                                event.stopPropagation();
                                setOpenLibraryMenu(null);
                                setOpenFolderMenu(
                                    openFolderMenu === node.id
                                        ? null
                                        : node.id
                                );
                            }}
                        >
                            <MoreVertical
                                size={16}
                                strokeWidth={1.8}
                            />
                        </button>

                        {openFolderMenu === node.id && (
                            <div
                                className="library-catalog-context-menu"
                                onClick={(event) =>
                                    event.stopPropagation()
                                }
                            >
                                <button
                                    type="button"
                                    onClick={() =>
                                        abrirCriacaoPasta(node.id)
                                    }
                                >
                                    <FolderPlus size={15} />
                                    <span>Criar subpasta</span>
                                </button>

                                <button
                                    type="button"
                                    onClick={() =>
                                        abrirCriacaoLibrary(node.id)
                                    }
                                >
                                    <Plus size={15} />
                                    <span>Nova biblioteca aqui</span>
                                </button>

                                <button
                                    type="button"
                                    onClick={() =>
                                        abrirRenomearPasta(node)
                                    }
                                >
                                    <Pencil size={15} />
                                    <span>Renomear</span>
                                </button>

                                <button
                                    type="button"
                                    onClick={() =>
                                        abrirPickerMoverPasta(node)
                                    }
                                >
                                    <Move size={15} />
                                    <span>Mover pasta</span>
                                </button>

                                <button
                                    type="button"
                                    className="library-context-danger"
                                    onClick={() => {
                                        setOpenFolderMenu(null);
                                        setConfirmation({
                                            kind: "delete-folder",
                                            folder: node,
                                        });
                                    }}
                                >
                                    <Trash2 size={15} />
                                    <span>Excluir pasta</span>
                                </button>
                            </div>
                        )}
                    </div>
                </div>

                {expanded && hasChildren && (
                    <div className="library-catalog-children">
                        {node.children.map((child) =>
                            renderizarNo(child, level + 1)
                        )}
                    </div>
                )}
            </div>
        );
    };

    // ========================================================
    // CONFIGURAÇÃO DO SELETOR DE PASTAS
    // ========================================================

    const pickerTitle = (() => {
        switch (folderPickerMode) {
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
    })();

    const pickerDescription = (() => {
        switch (folderPickerMode) {
            case "folder-create-location":
                return "Selecione a pasta pai. A raiz também é um destino válido.";
            case "folder-move":
                return pickerFolderItem
                    ? `Escolha o novo local de “${pickerFolderItem.name}”.`
                    : "Escolha o novo local da pasta.";
            case "library-create-location":
                return "Este local organiza a biblioteca no catálogo e não altera o namespace Python.";
            case "library-move":
                return pickerLibraryItem
                    ? `Escolha o novo local de “${pickerLibraryItem.name}”.`
                    : "Escolha o novo local da biblioteca.";
            default:
                return undefined;
        }
    })();

    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div
            className="libraries-module"
            onClick={() => {
                setOpenFolderMenu(null);
                setOpenLibraryMenu(null);
            }}
        >
            <section className="content-panel libraries-catalog-panel">
                <div className="libraries-catalog-header">
                    <div className="libraries-catalog-title-group">
                        <div className="libraries-catalog-title-icon">
                            <BookOpen
                                size={20}
                                strokeWidth={1.8}
                            />
                        </div>

                        <div>
                            <div className="libraries-catalog-eyebrow">
                                REUSABLE COMPONENTS
                            </div>

                            <h2>Bibliotecas</h2>

                            <p>
                                Organize componentes reutilizáveis em pastas e
                                controle exatamente quais versões estão publicadas.
                            </p>
                        </div>
                    </div>

                    <div className="libraries-catalog-header-actions">
                        <button
                            type="button"
                            className="library-toolbar-button"
                            title="Atualizar catálogo"
                            aria-label="Atualizar catálogo"
                            disabled={loadingLibraries}
                            onClick={(event) => {
                                event.stopPropagation();
                                void carregarBibliotecas();
                            }}
                        >
                            <RefreshCw
                                size={15}
                                strokeWidth={1.9}
                            />
                        </button>

                        <button
                            type="button"
                            className="library-button library-button-secondary"
                            onClick={(event) => {
                                event.stopPropagation();
                                abrirCriacaoPasta(null);
                            }}
                        >
                            <FolderPlus
                                size={15}
                                strokeWidth={1.9}
                            />
                            Nova pasta
                        </button>

                        <button
                            type="button"
                            className="library-button library-button-primary"
                            onClick={(event) => {
                                event.stopPropagation();
                                abrirCriacaoLibrary(null);
                            }}
                        >
                            <Plus
                                size={15}
                                strokeWidth={2}
                            />
                            Nova biblioteca
                        </button>
                    </div>
                </div>

                {(libraryError || librarySuccess) && (
                    <div className="libraries-catalog-message-area">
                        {libraryError && (
                            <div className="library-inline-alert library-inline-alert-error">
                                <span>{libraryError}</span>

                                <button
                                    type="button"
                                    onClick={() => setLibraryError("")}
                                    aria-label="Fechar mensagem de erro"
                                >
                                    <X size={15} />
                                </button>
                            </div>
                        )}

                        {librarySuccess && (
                            <div className="library-inline-alert library-inline-alert-success">
                                <span>{librarySuccess}</span>

                                <button
                                    type="button"
                                    onClick={() => setLibrarySuccess("")}
                                    aria-label="Fechar mensagem de sucesso"
                                >
                                    <X size={15} />
                                </button>
                            </div>
                        )}
                    </div>
                )}

                <div className="libraries-workspace">
                    <aside className="libraries-explorer">
                        <div className="libraries-explorer-toolbar">
                            <div className="libraries-search">
                                <Search
                                    size={15}
                                    strokeWidth={1.8}
                                />

                                <input
                                    type="search"
                                    value={librarySearch}
                                    placeholder="Buscar biblioteca..."
                                    onChange={(event) =>
                                        setLibrarySearch(event.target.value)
                                    }
                                    aria-label="Buscar no catálogo de Bibliotecas"
                                />

                                {librarySearch && (
                                    <button
                                        type="button"
                                        onClick={() => setLibrarySearch("")}
                                        aria-label="Limpar busca"
                                    >
                                        <X size={14} />
                                    </button>
                                )}
                            </div>

                            <div className="libraries-explorer-stats">
                                <span>
                                    {libraryFolderCount} pastas
                                </span>

                                <span className="libraries-explorer-stat-separator" />

                                <span>
                                    {libraryCount} bibliotecas
                                </span>
                            </div>
                        </div>

                        <div className="libraries-tree-root">
                            <div className="libraries-tree-root-label">
                                <BookOpen
                                    size={16}
                                    strokeWidth={1.8}
                                />
                                <span>Bibliotecas</span>
                            </div>

                            <div className="libraries-tree-content">
                                {loadingLibraries ? (
                                    <div className="libraries-tree-state">
                                        Carregando catálogo...
                                    </div>
                                ) : visibleTree.length === 0 ? (
                                    <div className="libraries-tree-empty">
                                        <div className="libraries-tree-empty-icon">
                                            <BookOpen
                                                size={20}
                                                strokeWidth={1.6}
                                            />
                                        </div>

                                        <strong>
                                            {librarySearch
                                                ? "Nenhum resultado"
                                                : "Catálogo vazio"}
                                        </strong>

                                        <span>
                                            {librarySearch
                                                ? "Tente outro termo de busca."
                                                : "Crie uma pasta ou a primeira biblioteca."}
                                        </span>
                                    </div>
                                ) : (
                                    visibleTree.map((node) =>
                                        renderizarNo(node)
                                    )
                                )}
                            </div>
                        </div>
                    </aside>

                    <div className="libraries-details">
                        {selectedLibrary ? (
                            <>
                                <div className="libraries-details-header">
                                    <div className="libraries-details-heading">
                                        <div className="libraries-details-icon library-details-code-icon">
                                            <FileCode2
                                                size={20}
                                                strokeWidth={1.8}
                                            />
                                        </div>

                                        <div>
                                            <div className="library-breadcrumb">
                                                <span>Bibliotecas</span>

                                                {selectedLibraryPath.map(
                                                    (part, index) => (
                                                        <span
                                                            key={`${part}-${index}`}
                                                            className="library-breadcrumb-part"
                                                        >
                                                            / {part}
                                                        </span>
                                                    )
                                                )}
                                            </div>

                                            <h3>
                                                {selectedLibrary.name}
                                            </h3>

                                            <code>
                                                {selectedLibrary.import_name}
                                            </code>
                                        </div>
                                    </div>

                                    <div className="libraries-details-actions">
                                        <button
                                            type="button"
                                            className="library-button library-button-secondary"
                                            onClick={() =>
                                                abrirPickerMoverLibrary(
                                                    selectedLibrary
                                                )
                                            }
                                        >
                                            <Move size={15} />
                                            Mover
                                        </button>

                                        <button
                                            type="button"
                                            className="library-button library-button-primary"
                                            onClick={() =>
                                                abrirEdicaoLibrary(
                                                    selectedLibrary
                                                )
                                            }
                                        >
                                            <Pencil size={15} />
                                            Editar
                                        </button>
                                    </div>
                                </div>

                                <div className="library-detail-summary">
                                    <div className="library-detail-description">
                                        <span className="library-detail-label">
                                            Descrição
                                        </span>

                                        <p>
                                            {selectedLibrary.description ||
                                                "Nenhuma descrição cadastrada."}
                                        </p>
                                    </div>

                                    <div className="library-detail-location">
                                        <span className="library-detail-label">
                                            Local no catálogo
                                        </span>

                                        <strong>
                                            {[
                                                "Bibliotecas",
                                                ...selectedLibraryPath,
                                            ].join(" / ")}
                                        </strong>
                                    </div>
                                </div>



                                {/* ============================================================
                                    ROBOTS QUE UTILIZAM ESTA LIBRARY
                                ============================================================ */}

                                <div className="library-usage-section">

                                    <div className="library-usage-header">

                                        <div>
                                            <h4>
                                                Utilizada por
                                            </h4>

                                            <p>
                                                Robots cuja versão atual publicada depende desta biblioteca.
                                            </p>
                                        </div>


                                        <div className="library-usage-header-meta">

                                            {libraryProductionVersion && (
                                                <span className="library-production-version">
                                                    Produção {libraryProductionVersion}
                                                </span>
                                            )}


                                            <span className="library-versions-count">
                                                {libraryRobots.length}
                                            </span>

                                        </div>

                                    </div>


                                    {loadingLibraryRobots ? (

                                        <div className="library-usage-state">
                                            Carregando Robots...
                                        </div>

                                    ) : libraryRobots.length === 0 ? (

                                        <div className="library-usage-empty">

                                            <strong>
                                                Nenhum Robot utiliza esta biblioteca
                                            </strong>

                                            <span>
                                                Nenhuma versão atual publicada possui vínculo com esta Library.
                                            </span>

                                        </div>

                                    ) : (

                                        <div className="library-usage-list">

                                            {libraryRobots.map(
                                                (robot) => (

                                                    <div
                                                        key={robot.robot_id}
                                                        className="library-usage-row"
                                                    >

                                                        {/* Identificação do Robot. */}
                                                        <div className="library-usage-robot">

                                                            <strong>
                                                                {robot.robot_name}
                                                            </strong>

                                                            <span>
                                                                Robot v{robot.robot_version}
                                                            </span>

                                                        </div>


                                                        {/* Versão exata da Library utilizada por ele. */}
                                                        <div className="library-usage-version">

                                                            <span>
                                                                Biblioteca
                                                            </span>

                                                            <strong>
                                                                {robot.library_version}
                                                            </strong>

                                                        </div>


                                                        {/* Situação em relação à versão de Produção atual. */}
                                                        <span
                                                            className={
                                                                robot.uses_production_version
                                                                    ? "library-usage-status-current"
                                                                    : "library-usage-status-previous"
                                                            }
                                                        >
                                                            {robot.uses_production_version
                                                                ? "Produção atual"
                                                                : "Versão anterior"}
                                                        </span>

                                                    </div>
                                                )
                                            )}

                                        </div>
                                    )}

                                </div>

                                <div className="library-versions-section">
                                    <div className="library-versions-header">
                                        <div>
                                            <h4>Versões publicadas</h4>
                                            <p>
                                                Cada versão é um snapshot imutável da biblioteca.
                                            </p>
                                        </div>

                                        <span className="library-versions-count">
                                            {versions.length}
                                        </span>
                                    </div>

                                    {loadingVersions ? (
                                        <div className="library-versions-state">
                                            Carregando versões...
                                        </div>
                                    ) : versions.length === 0 ? (
                                        <div className="library-versions-empty">
                                            <FileCode2 size={20} />
                                            <div>
                                                <strong>
                                                    Nenhuma versão publicada
                                                </strong>
                                                <span>
                                                    A identidade da biblioteca já existe, mas ainda não possui release.
                                                </span>
                                            </div>
                                        </div>
                                    ) : (
                                        <div className="library-versions-list">
                                            {versions.map((version) => {

                                                const versionOpened =
                                                    selectedVersionId ===
                                                    version.id;

                                                return (
                                                    <div
                                                        key={version.id}
                                                    >
                                                        {/* ============================================
                                                            CABEÇALHO DA VERSÃO
                                                        ============================================ */}

                                                        <div
                                                            className="library-version-row"

                                                            role="button"
                                                            tabIndex={0}

                                                            onClick={() =>
                                                                selectedLibrary &&
                                                                carregarArvoreVersao(
                                                                    selectedLibrary,
                                                                    version
                                                                )
                                                            }

                                                            onKeyDown={(event) => {

                                                                if (
                                                                    event.key === "Enter" ||
                                                                    event.key === " "
                                                                ) {
                                                                    event.preventDefault();

                                                                    if (
                                                                        selectedLibrary
                                                                    ) {
                                                                        void carregarArvoreVersao(
                                                                            selectedLibrary,
                                                                            version
                                                                        );
                                                                    }
                                                                }
                                                            }}

                                                            style={{
                                                                cursor: "pointer",
                                                            }}
                                                        >
                                                            <div className="library-version-main">

                                                                {/* Expande/recolhe o snapshot. */}
                                                                <span>
                                                                    {versionOpened ? (
                                                                        <ChevronDown
                                                                            size={15}
                                                                        />
                                                                    ) : (
                                                                        <ChevronRight
                                                                            size={15}
                                                                        />
                                                                    )}
                                                                </span>


                                                                <span className="library-version-badge">
                                                                    {version.version}
                                                                </span>


                                                                <div>
                                                                    <strong>
                                                                        {version.source_type}
                                                                    </strong>

                                                                    <small>
                                                                        Publicada em{" "}
                                                                        {formatarData(
                                                                            version.published_at
                                                                        )}
                                                                    </small>
                                                                </div>
                                                            </div>


                                                            {/* ========================================
                                                                STATUS REAL DA VERSÃO
                                                            ======================================== */}

                                                            <span
                                                                className={`library-version-status ${
                                                                    version.is_active
                                                                        ? "library-version-status-active"
                                                                        : "library-version-status-inactive"
                                                                }`}
                                                            >
                                                                {version.is_production
                                                                    ? "Produção"
                                                                    : version.is_active
                                                                        ? "Disponível"
                                                                        : "Inativa"}
                                                            </span>
                                                        </div>


                                                        {/* ============================================
                                                            CONTEÚDO IMUTÁVEL DA VERSÃO
                                                        ============================================ */}

                                                        {versionOpened && (

                                                            <div
                                                                style={{
                                                                    margin:
                                                                        "0 8px 10px 8px",

                                                                    border:
                                                                        "1px solid rgba(148, 163, 184, 0.18)",

                                                                    borderRadius:
                                                                        "8px",

                                                                    overflow:
                                                                        "hidden",
                                                                }}
                                                            >
                                                                {/* Cabeçalho conceitual da árvore. */}
                                                                <div
                                                                    style={{
                                                                        padding:
                                                                            "8px 12px",

                                                                        display:
                                                                            "flex",

                                                                        alignItems:
                                                                            "center",

                                                                        gap:
                                                                            "7px",

                                                                        fontSize:
                                                                            "12px",

                                                                        fontWeight:
                                                                            600,

                                                                        opacity:
                                                                            0.8,

                                                                        borderBottom:
                                                                            "1px solid rgba(148, 163, 184, 0.14)",
                                                                    }}
                                                                >
                                                                    <FileCode2
                                                                        size={14}
                                                                    />

                                                                    Código
                                                                </div>


                                                                {loadingVersionTree ? (

                                                                    <div
                                                                        style={{
                                                                            padding:
                                                                                "12px",

                                                                            fontSize:
                                                                                "12px",

                                                                            opacity:
                                                                                0.7,
                                                                        }}
                                                                    >
                                                                        Carregando snapshot...
                                                                    </div>

                                                                ) : versionTree.length === 0 ? (

                                                                    <div
                                                                        style={{
                                                                            padding:
                                                                                "12px",

                                                                            fontSize:
                                                                                "12px",

                                                                            opacity:
                                                                                0.7,
                                                                        }}
                                                                    >
                                                                        Nenhum arquivo encontrado nesta versão.
                                                                    </div>

                                                                ) : (

                                                                    <div
                                                                        style={{
                                                                            padding:
                                                                                "4px 0",
                                                                        }}
                                                                    >
                                                                        {versionTree.map(
                                                                            (node) =>
                                                                                renderizarNoSnapshot(
                                                                                    node
                                                                                )
                                                                        )}
                                                                    </div>
                                                                )}
                                                            </div>
                                                        )}
                                                    </div>
                                                );
                                            })}
                                        </div>
                                    )}
                                </div>
                            </>
                        ) : selectedFolder ? (
                            <>
                                <div className="libraries-details-header">
                                    <div className="libraries-details-heading">
                                        <div className="libraries-details-icon">
                                            <Folder
                                                size={20}
                                                strokeWidth={1.8}
                                            />
                                        </div>

                                        <div>
                                            <div className="library-breadcrumb">
                                                <span>Bibliotecas</span>

                                                {selectedFolderPath
                                                    .slice(0, -1)
                                                    .map((part, index) => (
                                                        <span
                                                            key={`${part}-${index}`}
                                                            className="library-breadcrumb-part"
                                                        >
                                                            / {part}
                                                        </span>
                                                    ))}
                                            </div>

                                            <h3>{selectedFolder.name}</h3>
                                            <p>Pasta organizacional</p>
                                        </div>
                                    </div>

                                    <div className="libraries-details-actions">
                                        <button
                                            type="button"
                                            className="library-button library-button-secondary"
                                            onClick={() =>
                                                abrirCriacaoPasta(
                                                    selectedFolder.id
                                                )
                                            }
                                        >
                                            <FolderPlus size={15} />
                                            Subpasta
                                        </button>

                                        <button
                                            type="button"
                                            className="library-button library-button-primary"
                                            onClick={() =>
                                                abrirCriacaoLibrary(
                                                    selectedFolder.id
                                                )
                                            }
                                        >
                                            <Plus size={15} />
                                            Nova biblioteca
                                        </button>
                                    </div>
                                </div>

                                <div className="library-folder-overview">
                                    <div className="library-folder-overview-card">
                                        <span>Local</span>
                                        <strong>
                                            {[
                                                "Bibliotecas",
                                                ...selectedFolderPath,
                                            ].join(" / ")}
                                        </strong>
                                    </div>

                                    <div className="library-folder-overview-card">
                                        <span>Itens diretos</span>
                                        <strong>
                                            {selectedFolder.children.length}
                                        </strong>
                                    </div>
                                </div>
                            </>
                        ) : (
                            <div className="libraries-details-empty">
                                <div className="libraries-details-empty-icon">
                                    <BookOpen
                                        size={25}
                                        strokeWidth={1.6}
                                    />
                                </div>

                                <h3>Catálogo de Bibliotecas</h3>

                                <p>
                                    Selecione uma pasta ou biblioteca no explorador
                                    para visualizar detalhes e ações.
                                </p>

                                <div className="libraries-details-empty-actions">
                                    <button
                                        type="button"
                                        className="library-button library-button-secondary"
                                        onClick={() => abrirCriacaoPasta(null)}
                                    >
                                        <FolderPlus size={15} />
                                        Criar pasta
                                    </button>

                                    <button
                                        type="button"
                                        className="library-button library-button-primary"
                                        onClick={() => abrirCriacaoLibrary(null)}
                                    >
                                        <Plus size={15} />
                                        Nova biblioteca
                                    </button>
                                </div>
                            </div>
                        )}
                    </div>
                </div>
            </section>

            {/* ==================================================
                MODAL - CRIAR / RENOMEAR PASTA
               ================================================== */}
            {folderEditorMode && (
                <div
                    className="library-modal-backdrop"
                    role="presentation"
                    onMouseDown={(event) => {
                        if (
                            !savingFolder &&
                            event.target === event.currentTarget
                        ) {
                            fecharFolderEditor();
                        }
                    }}
                >
                    <div
                        className="library-modal"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="library-folder-editor-title"
                        onClick={(event) => event.stopPropagation()}
                    >
                        <div className="library-modal-header">
                            <div>
                                <div className="library-modal-eyebrow">
                                    CATÁLOGO GLOBAL
                                </div>

                                <h3 id="library-folder-editor-title">
                                    {folderEditorMode === "create"
                                        ? "Nova pasta"
                                        : "Renomear pasta"}
                                </h3>

                                <p>
                                    {folderEditorMode === "create"
                                        ? "Crie uma pasta organizacional em qualquer nível do catálogo."
                                        : "Altere somente o nome desta pasta."}
                                </p>
                            </div>

                            <button
                                type="button"
                                className="library-modal-close"
                                disabled={savingFolder}
                                onClick={fecharFolderEditor}
                                aria-label="Fechar"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <div className="library-modal-body">
                            <div className="library-modal-field">
                                <label htmlFor="library-folder-name">
                                    Nome da pasta
                                </label>

                                <input
                                    id="library-folder-name"
                                    type="text"
                                    autoFocus
                                    value={folderName}
                                    placeholder="Ex.: Financeiro"
                                    disabled={savingFolder}
                                    onChange={(event) =>
                                        setFolderName(event.target.value)
                                    }
                                    onKeyDown={(event) => {
                                        if (event.key === "Enter") {
                                            void salvarPasta();
                                        }
                                    }}
                                />
                            </div>

                            {folderEditorMode === "create" && (
                                <div className="library-modal-location-card">
                                    <div>
                                        <span>Local</span>
                                        <strong>
                                            {folderDestinationId === null
                                                ? "Bibliotecas"
                                                : [
                                                    "Bibliotecas",
                                                    ...(encontrarCaminhoPasta(
                                                        libraryTree,
                                                        folderDestinationId
                                                    ) || []),
                                                ].join(" / ")}
                                        </strong>
                                    </div>

                                    <button
                                        type="button"
                                        className="library-button library-button-secondary"
                                        disabled={savingFolder}
                                        onClick={abrirPickerCriacaoPasta}
                                    >
                                        <Move size={15} />
                                        Alterar local
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="library-modal-footer">
                            <button
                                type="button"
                                className="library-button library-button-secondary"
                                disabled={savingFolder}
                                onClick={fecharFolderEditor}
                            >
                                Cancelar
                            </button>

                            <button
                                type="button"
                                className="library-button library-button-primary"
                                disabled={
                                    savingFolder ||
                                    !folderName.trim()
                                }
                                onClick={() => void salvarPasta()}
                            >
                                {savingFolder
                                    ? "Salvando..."
                                    : folderEditorMode === "create"
                                        ? "Criar pasta"
                                        : "Salvar nome"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ==================================================
                MODAL - CRIAR / EDITAR LIBRARY
               ================================================== */}
            {libraryEditorMode && (
                <div
                    className="library-modal-backdrop"
                    role="presentation"
                    onMouseDown={(event) => {
                        if (
                            !savingLibrary &&
                            event.target === event.currentTarget
                        ) {
                            fecharLibraryEditor();
                        }
                    }}
                >
                    <div
                        className="library-modal library-modal-large"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="library-editor-title"
                        onClick={(event) => event.stopPropagation()}
                    >
                        <div className="library-modal-header">
                            <div>
                                <div className="library-modal-eyebrow">
                                    BIBLIOTECA REUTILIZÁVEL
                                </div>

                                <h3 id="library-editor-title">
                                    {libraryEditorMode === "create"
                                        ? "Nova biblioteca"
                                        : "Editar biblioteca"}
                                </h3>

                                <p>
                                    {libraryEditorMode === "create"
                                        ? "Cadastre a identidade da biblioteca. As versões serão publicadas separadamente."
                                        : "Altere os metadados amigáveis. O import_name permanece imutável."}
                                </p>
                            </div>

                            <button
                                type="button"
                                className="library-modal-close"
                                disabled={savingLibrary}
                                onClick={fecharLibraryEditor}
                                aria-label="Fechar"
                            >
                                <X size={18} />
                            </button>
                        </div>

                        <div className="library-modal-body">
                            <div className="library-modal-grid">
                                <div className="library-modal-field">
                                    <label htmlFor="library-name">
                                        Nome
                                    </label>

                                    <input
                                        id="library-name"
                                        type="text"
                                        value={libraryName}
                                        placeholder="Ex.: Financeiro Core"
                                        disabled={savingLibrary}
                                        onChange={(event) =>
                                            setLibraryName(event.target.value)
                                        }
                                    />
                                </div>

                                <div className="library-modal-field">
                                    <label htmlFor="library-import-name">
                                        import_name
                                    </label>

                                    <input
                                        id="library-import-name"
                                        type="text"
                                        value={libraryImportName}
                                        placeholder="Ex.: financeiro_core"
                                        disabled={
                                            savingLibrary ||
                                            libraryEditorMode === "edit"
                                        }
                                        onChange={(event) =>
                                            setLibraryImportName(
                                                event.target.value
                                            )
                                        }
                                    />

                                    <small>
                                        Namespace utilizado nos imports Python.
                                    </small>
                                </div>
                            </div>

                            <div className="library-modal-field">
                                <label htmlFor="library-description">
                                    Descrição
                                </label>

                                <textarea
                                    id="library-description"
                                    rows={4}
                                    value={libraryDescription}
                                    placeholder="Explique a finalidade desta biblioteca..."
                                    disabled={savingLibrary}
                                    onChange={(event) =>
                                        setLibraryDescription(
                                            event.target.value
                                        )
                                    }
                                />
                            </div>

                            {libraryEditorMode === "create" && (
                                <div className="library-modal-location-card">
                                    <div>
                                        <span>Local</span>
                                        <strong>
                                            {libraryDestinationId === null
                                                ? "Bibliotecas"
                                                : [
                                                    "Bibliotecas",
                                                    ...(encontrarCaminhoPasta(
                                                        libraryTree,
                                                        libraryDestinationId
                                                    ) || []),
                                                ].join(" / ")}
                                        </strong>
                                        <small>
                                            A organização do catálogo é independente da estrutura Python interna.
                                        </small>
                                    </div>

                                    <button
                                        type="button"
                                        className="library-button library-button-secondary"
                                        disabled={savingLibrary}
                                        onClick={abrirPickerCriacaoLibrary}
                                    >
                                        <Move size={15} />
                                        Alterar pasta
                                    </button>
                                </div>
                            )}
                        </div>

                        <div className="library-modal-footer">
                            <button
                                type="button"
                                className="library-button library-button-secondary"
                                disabled={savingLibrary}
                                onClick={fecharLibraryEditor}
                            >
                                Cancelar
                            </button>

                            <button
                                type="button"
                                className="library-button library-button-primary"
                                disabled={
                                    savingLibrary ||
                                    !libraryName.trim() ||
                                    (
                                        libraryEditorMode === "create" &&
                                        !libraryImportName.trim()
                                    )
                                }
                                onClick={() => void salvarLibrary()}
                            >
                                {savingLibrary
                                    ? "Salvando..."
                                    : libraryEditorMode === "create"
                                        ? "Criar biblioteca"
                                        : "Salvar alterações"}
                            </button>
                        </div>
                    </div>
                </div>
            )}

            {/* ==================================================
                SELETOR REUTILIZÁVEL DE PASTAS
               ================================================== */}
            <LibraryFolderPicker
                open={folderPickerMode !== null}
                title={pickerTitle}
                description={pickerDescription}
                folders={folderOptions}
                selectedFolderId={pickerSelectedFolderId}
                disabledFolderIds={blockedPickerFolderIds}
                busy={savingPicker}
                confirmLabel={
                    folderPickerMode === "folder-move"
                        ? "Mover pasta"
                        : folderPickerMode === "library-move"
                            ? "Mover biblioteca"
                            : "Selecionar"
                }
                onChange={setPickerSelectedFolderId}
                onCancel={fecharPicker}
                onConfirm={() => void confirmarPicker()}
            />

            {/* ==================================================
                CONFIRMAÇÃO PROFISSIONAL DE AÇÃO DESTRUTIVA
               ================================================== */}
            {confirmation && (
                <div
                    className="library-modal-backdrop library-confirm-backdrop"
                    role="presentation"
                    onMouseDown={(event) => {
                        if (
                            !confirmingAction &&
                            event.target === event.currentTarget
                        ) {
                            setConfirmation(null);
                        }
                    }}
                >
                    <div
                        className="library-confirm-modal"
                        role="dialog"
                        aria-modal="true"
                        aria-labelledby="library-confirm-title"
                        onClick={(event) => event.stopPropagation()}
                    >
                        <div className="library-confirm-icon">
                            <Trash2
                                size={20}
                                strokeWidth={1.8}
                            />
                        </div>

                        <div className="library-confirm-content">
                            <div className="library-modal-eyebrow">
                                CONFIRMAÇÃO
                            </div>

                            <h3 id="library-confirm-title">
                                {confirmation.kind === "delete-folder"
                                    ? "Excluir pasta?"
                                    : "Desativar biblioteca?"}
                            </h3>

                            <p>
                                {confirmation.kind === "delete-folder"
                                    ? `A pasta “${confirmation.folder.name}” só poderá ser excluída se estiver vazia.`
                                    : `A biblioteca “${confirmation.library.name}” deixará de aparecer para novos vínculos. O histórico publicado não será apagado.`}
                            </p>
                        </div>

                        <div className="library-confirm-actions">
                            <button
                                type="button"
                                className="library-button library-button-secondary"
                                disabled={confirmingAction}
                                onClick={() => setConfirmation(null)}
                            >
                                Cancelar
                            </button>

                            <button
                                type="button"
                                className="library-button library-button-danger"
                                disabled={confirmingAction}
                                onClick={() =>
                                    void confirmarAcaoDestrutiva()
                                }
                            >
                                {confirmingAction
                                    ? "Processando..."
                                    : confirmation.kind === "delete-folder"
                                        ? "Excluir pasta"
                                        : "Desativar biblioteca"}
                            </button>
                        </div>
                    </div>
                </div>
            )}
        </div>
    );
}

export default LibrariesPanel;

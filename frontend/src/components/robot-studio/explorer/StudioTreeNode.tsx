// ============================================================
// DUET CORE - ROBOT STUDIO - STUDIO TREE NODE
// ============================================================
//
// Responsabilidade:
// - renderizar recursivamente um arquivo ou pasta da árvore
//   do Explorer do Robot Studio;
// - manter a apresentação e as ações visuais atualmente
//   existentes no renderNode de RobotStudio.tsx;
// - delegar todas as operações reais para callbacks recebidos
//   pelo componente.
//
// IMPORTANTE:
// Este componente faz parte de uma refatoração estrutural.
// Nenhuma regra funcional, permissão ou comportamento do
// Explorer deve ser alterado durante esta extração.
//
// Este componente NÃO deve:
// - executar chamadas HTTP;
// - alterar diretamente o workspace;
// - possuir regras de Checkout;
// - implementar regras de Library no backend;
// - controlar o Monaco Editor.
//
// As operações de criar, renomear, excluir, abrir arquivo e
// remover Library continuam pertencendo ao Robot Studio e são
// recebidas explicitamente através das propriedades.
//
// Dependências:
// - StudioNode;
// - estilos atualmente existentes em RobotStudio.tsx;
// - ícones Lucide utilizados pelo Explorer.
// ============================================================

import type {
    CSSProperties,
    ReactNode,
} from "react";

import {
    ChevronDown,
    ChevronRight,
    FileCode2,
    FileJson,
    FilePlus2,
    Folder,
    FolderOpen,
    FolderPlus,
    Pencil,
    Trash2,
    Unlink,
} from "lucide-react";

import type {
    StudioNode,
} from "../../../types/robotStudio";


// ============================================================
// CONTRATO DOS ESTILOS UTILIZADOS
// ============================================================
//
// Não estamos movendo o objeto styles nesta etapa.
// O componente recebe somente os estilos de que precisa,
// preservando os mesmos objetos utilizados atualmente pela
// página RobotStudio.tsx.
// ============================================================

interface StudioTreeNodeStyles {
    treeItemRow: CSSProperties;
    treeRowMain: CSSProperties;
    treeChevron: CSSProperties;
    treeLabel: CSSProperties;
    treeItemActions: CSSProperties;
    treeActionButton: CSSProperties;
    fileIcon: CSSProperties;
}


// ============================================================
// PROPRIEDADES
// ============================================================

interface StudioTreeNodeProps {

    // Nó atual que será renderizado.
    node: StudioNode;

    // Nível atual da recursão.
    level?: number;

    // Pastas atualmente expandidas no Explorer.
    expandedFolders: Set<string>;

    // Pasta selecionada como destino de criação.
    selectedFolderId: string | null;

    // Arquivo atualmente ativo no editor.
    activeFileId: string;

    // Permissões/estado derivados do Studio.
    canWriteWorkspace: boolean;
    canUseLibrary: boolean;

    // Estilos originais do RobotStudio.tsx.
    styles: StudioTreeNodeStyles;

    // Ações delegadas para o componente proprietário.
    onSelectFolder: (folderId: string) => void;
    onToggleFolder: (folderId: string) => void;
    onOpenFile: (node: StudioNode) => void;

    onCreateFileInFolder: (
        targetFolderId: string | null
    ) => void;

    onCreateFolderInFolder: (
        targetFolderId: string | null
    ) => void;

    onRenameItem: (
        node: StudioNode
    ) => void;

    onDeleteItem: (
        node: StudioNode
    ) => void;

    onRemoveLibrary: (
        node: StudioNode
    ) => void;
}


// ============================================================
// HELPER VISUAL - ÍCONE DO ARQUIVO
// ============================================================
//
// Mantém exatamente a regra atualmente utilizada pelo
// fileIcon do RobotStudio.tsx:
//
// - JSON -> FileJson;
// - qualquer outro arquivo -> FileCode2.
// ============================================================

const fileIcon = (
    filename: string,
    size = 15
): ReactNode => {

    if (
        filename
            .toLowerCase()
            .endsWith(".json")
    ) {
        return (
            <FileJson
                size={size}
                strokeWidth={1.7}
            />
        );
    }

    return (
        <FileCode2
            size={size}
            strokeWidth={1.7}
        />
    );
};


// ============================================================
// COMPONENTE
// ============================================================

function StudioTreeNode({
    node,
    level = 0,
    expandedFolders,
    selectedFolderId,
    activeFileId,
    canWriteWorkspace,
    canUseLibrary,
    styles,
    onSelectFolder,
    onToggleFolder,
    onOpenFile,
    onCreateFileInFolder,
    onCreateFolderInFolder,
    onRenameItem,
    onDeleteItem,
    onRemoveLibrary,
}: StudioTreeNodeProps) {

    const paddingLeft =
        10 + level * 14;


    // ========================================================
    // PASTA
    // ========================================================

    if (node.type === "folder") {

        const expanded =
            expandedFolders.has(
                node.id
            );

        const selected =
            selectedFolderId ===
            node.id;


        // O contêiner técnico e o namespace principal possuem
        // responsabilidades diferentes:
        //
        // - _libraries: apenas agrupa Bibliotecas;
        // - _libraries/<namespace>: raiz de uma Biblioteca;
        // - níveis abaixo do namespace: pastas normais editáveis.
        const isLibraryContainer =
            node.id === "_libraries";

        const isLibraryNamespaceRoot =
            /^_libraries\/[^/]+$/.test(
                node.id
            );

        const isInsideLibrary =
            node.id.startsWith(
                "_libraries/"
            );

        const displayName =
            node.id === "_libraries"
                ? "Bibliotecas"
                : node.name;


        return (
            <div>

                <div
                    style={{
                        ...styles.treeItemRow,

                        background:
                            selected
                                ? "#252526"
                                : "transparent",
                    }}
                >

                    {/* =========================================
                        ÁREA PRINCIPAL DA PASTA
                    ========================================= */}

                    <button
                        type="button"
                        onClick={() => {

                            onSelectFolder(
                                node.id
                            );

                            onToggleFolder(
                                node.id
                            );
                        }}
                        style={{
                            ...styles.treeRowMain,
                            paddingLeft,
                        }}
                    >

                        <span style={styles.treeChevron}>
                            {expanded ? (
                                <ChevronDown size={14} />
                            ) : (
                                <ChevronRight size={14} />
                            )}
                        </span>


                        {expanded ? (
                            <FolderOpen
                                size={15}
                                strokeWidth={1.7}
                            />
                        ) : (
                            <Folder
                                size={15}
                                strokeWidth={1.7}
                            />
                        )}


                        <span style={styles.treeLabel}>
                            {displayName}
                        </span>

                    </button>


                    {/* =========================================
                        AÇÕES DA PASTA
                    ========================================= */}

                    {!isLibraryContainer && (
                        <div style={styles.treeItemActions}>

                            {/* ---------------------------------
                                BIBLIOTECAS: NOVO ARQUIVO
                               ---------------------------------

                               A raiz do namespace e qualquer
                               subpasta interna podem receber
                               novos arquivos.
                            */}
                            {isInsideLibrary && (
                                <button
                                    type="button"
                                    onClick={() =>
                                        onCreateFileInFolder(
                                            node.id
                                        )
                                    }
                                    disabled={!canWriteWorkspace}
                                    style={{
                                        ...styles.treeActionButton,

                                        opacity:
                                            canWriteWorkspace
                                                ? 1
                                                : 0.35,

                                        cursor:
                                            canWriteWorkspace
                                                ? "pointer"
                                                : "not-allowed",
                                    }}
                                    title="Novo arquivo nesta pasta"
                                    aria-label={`Novo arquivo em ${node.name}`}
                                >
                                    <FilePlus2
                                        size={13}
                                        strokeWidth={1.8}
                                    />
                                </button>
                            )}


                            {/* ---------------------------------
                                BIBLIOTECAS: NOVA SUBPASTA
                               ---------------------------------

                               Funciona tanto na raiz da
                               Biblioteca quanto em qualquer
                               subpasta abaixo dela.
                            */}
                            {isInsideLibrary && (
                                <button
                                    type="button"
                                    onClick={() =>
                                        onCreateFolderInFolder(
                                            node.id
                                        )
                                    }
                                    disabled={!canWriteWorkspace}
                                    style={{
                                        ...styles.treeActionButton,

                                        opacity:
                                            canWriteWorkspace
                                                ? 1
                                                : 0.35,

                                        cursor:
                                            canWriteWorkspace
                                                ? "pointer"
                                                : "not-allowed",
                                    }}
                                    title="Nova pasta dentro desta pasta"
                                    aria-label={`Nova pasta em ${node.name}`}
                                >
                                    <FolderPlus
                                        size={13}
                                        strokeWidth={1.8}
                                    />
                                </button>
                            )}


                            {/* ---------------------------------
                                REMOVER LIBRARY DO PROJETO
                               ---------------------------------

                               Diferente da lixeira comum:

                               - não apaga uma pasta arbitrária;
                               - não exclui a Library global;
                               - remove oficialmente a dependência
                                 deste AutomationProject.
                            */}
                            {isLibraryNamespaceRoot && (
                                <button
                                    type="button"
                                    onClick={() =>
                                        onRemoveLibrary(
                                            node
                                        )
                                    }
                                    disabled={
                                        !canWriteWorkspace ||
                                        !canUseLibrary
                                    }
                                    style={{
                                        ...styles.treeActionButton,

                                        opacity:
                                            canWriteWorkspace &&
                                            canUseLibrary
                                                ? 1
                                                : 0.35,

                                        cursor:
                                            canWriteWorkspace &&
                                            canUseLibrary
                                                ? "pointer"
                                                : "not-allowed",
                                    }}
                                    title="Remover biblioteca do projeto"
                                    aria-label={`Remover ${node.name} do projeto`}
                                >
                                    <Unlink
                                        size={13}
                                        strokeWidth={1.8}
                                    />
                                </button>
                            )}


                            {/* A raiz da Biblioteca não pode ser
                                renomeada ou excluída diretamente
                                pelo Explorer. Isso continua sendo
                                responsabilidade da gestão da Library.

                                Subpastas internas seguem editáveis. */}
                            {!isLibraryNamespaceRoot && (
                                <>
                                    <button
                                        type="button"
                                        onClick={() =>
                                            onRenameItem(
                                                node
                                            )
                                        }
                                        disabled={!canWriteWorkspace}
                                        style={{
                                            ...styles.treeActionButton,

                                            opacity:
                                                canWriteWorkspace
                                                    ? 1
                                                    : 0.35,

                                            cursor:
                                                canWriteWorkspace
                                                    ? "pointer"
                                                    : "not-allowed",
                                        }}
                                        title="Renomear pasta"
                                        aria-label={`Renomear ${node.name}`}
                                    >
                                        <Pencil
                                            size={13}
                                            strokeWidth={1.8}
                                        />
                                    </button>

                                    <button
                                        type="button"
                                        onClick={() =>
                                            onDeleteItem(
                                                node
                                            )
                                        }
                                        disabled={!canWriteWorkspace}
                                        style={{
                                            ...styles.treeActionButton,

                                            opacity:
                                                canWriteWorkspace
                                                    ? 1
                                                    : 0.35,

                                            cursor:
                                                canWriteWorkspace
                                                    ? "pointer"
                                                    : "not-allowed",
                                        }}
                                        title="Excluir pasta"
                                        aria-label={`Excluir ${node.name}`}
                                    >
                                        <Trash2
                                            size={13}
                                            strokeWidth={1.8}
                                        />
                                    </button>
                                </>
                            )}

                        </div>
                    )}

                </div>


                {/* =============================================
                    FILHOS
                ============================================= */}

                {expanded &&
                    node.children?.map(
                        (child) => (
                            <StudioTreeNode
                                key={child.id}
                                node={child}
                                level={level + 1}
                                expandedFolders={expandedFolders}
                                selectedFolderId={selectedFolderId}
                                activeFileId={activeFileId}
                                canWriteWorkspace={canWriteWorkspace}
                                canUseLibrary={canUseLibrary}
                                styles={styles}
                                onSelectFolder={onSelectFolder}
                                onToggleFolder={onToggleFolder}
                                onOpenFile={onOpenFile}
                                onCreateFileInFolder={onCreateFileInFolder}
                                onCreateFolderInFolder={onCreateFolderInFolder}
                                onRenameItem={onRenameItem}
                                onDeleteItem={onDeleteItem}
                                onRemoveLibrary={onRemoveLibrary}
                            />
                        )
                    )}

            </div>
        );
    }


    // ========================================================
    // ARQUIVO
    // ========================================================

    const active =
        activeFileId ===
        node.id;


    return (
        <div
            style={{
                ...styles.treeItemRow,

                background:
                    active
                        ? "#37373d"
                        : "transparent",
            }}
        >

            {/* =============================================
                ÁREA PRINCIPAL DO ARQUIVO
            ============================================= */}

            <button
                type="button"
                onClick={() =>
                    onOpenFile(
                        node
                    )
                }
                style={{
                    ...styles.treeRowMain,

                    paddingLeft:
                        paddingLeft + 20,
                }}
            >

                <span style={styles.fileIcon}>
                    {fileIcon(
                        node.name
                    )}
                </span>


                <span style={styles.treeLabel}>
                    {node.name}
                </span>

            </button>


            {/* =============================================
                AÇÕES DO ARQUIVO
            ============================================= */}

            {node.id !== "main.py" && (

                <div style={styles.treeItemActions}>

                    <button
                        type="button"
                        onClick={() =>
                            onRenameItem(
                                node
                            )
                        }
                        disabled={!canWriteWorkspace}
                        style={{
                            ...styles.treeActionButton,

                            opacity:
                                canWriteWorkspace
                                    ? 1
                                    : 0.35,

                            cursor:
                                canWriteWorkspace
                                    ? "pointer"
                                    : "not-allowed",
                        }}
                        title="Renomear arquivo"
                        aria-label={`Renomear ${node.name}`}
                    >
                        <Pencil
                            size={13}
                            strokeWidth={1.8}
                        />
                    </button>


                    <button
                        type="button"
                        onClick={() =>
                            onDeleteItem(
                                node
                            )
                        }
                        disabled={!canWriteWorkspace}
                        style={{
                            ...styles.treeActionButton,

                            opacity:
                                canWriteWorkspace
                                    ? 1
                                    : 0.35,

                            cursor:
                                canWriteWorkspace
                                    ? "pointer"
                                    : "not-allowed",
                        }}
                        title="Excluir arquivo"
                        aria-label={`Excluir ${node.name}`}
                    >
                        <Trash2
                            size={13}
                            strokeWidth={1.8}
                        />
                    </button>

                </div>
            )}

        </div>
    );
}


export default StudioTreeNode;
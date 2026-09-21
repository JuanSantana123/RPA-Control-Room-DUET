// ============================================================
// DUET CORE - ROBOT STUDIO - EXPLORER
// ============================================================
//
// Responsabilidade:
// - renderizar a barra lateral EXPLORER do Robot Studio;
// - exibir a raiz do AutomationProject;
// - exibir a árvore recursiva do workspace;
// - exibir as ações atuais de Library, novo arquivo e pasta;
// - exibir o destino atualmente selecionado para criação.
//
// IMPORTANTE:
// Este componente faz parte de uma refatoração estrutural.
// O objetivo é reproduzir a interface já existente no
// RobotStudio.tsx sem alterar comportamento, permissões,
// regras de Library ou layout.
//
// Este componente NÃO deve:
// - executar chamadas HTTP;
// - possuir regras de Checkout;
// - alterar diretamente o workspace;
// - implementar criação/exclusão/rename;
// - decidir regras de persistência.
//
// Todas as operações continuam sendo recebidas por callbacks.
//
// Dependências:
// - StudioTreeNode para renderização recursiva;
// - findNodeById para apresentar o nome do destino atual;
// - estilos originais do RobotStudio.tsx.
// ============================================================

import type {
    CSSProperties,
} from "react";

import {
    ChevronDown,
    FilePlus2,
    FolderOpen,
    FolderPlus,
    Plus,
} from "lucide-react";

import type {
    StudioNode,
} from "../../types/robotStudio";

import {
    findNodeById,
} from "../../utils/robotStudioTree";

import StudioTreeNode
    from "./explorer/StudioTreeNode";


// ============================================================
// CONTRATO DOS ESTILOS
// ============================================================
//
// O objeto styles permanece no RobotStudio.tsx nesta etapa.
// Este contrato contém apenas as propriedades utilizadas pelo
// Explorer e pelo StudioTreeNode.
// ============================================================

interface RobotStudioExplorerStyles {
    sidebar: CSSProperties;
    sidebarHeader: CSSProperties;
    sidebarActions: CSSProperties;
    libraryCreateButton: CSSProperties;
    smallIconButton: CSSProperties;
    projectRoot: CSSProperties;
    tree: CSSProperties;
    sidebarFooter: CSSProperties;

    // Estilos utilizados pelos nós recursivos.
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

interface RobotStudioExplorerProps {

    // Nome exibido na raiz do Explorer.
    projectName: string;

    // Árvore atual do workspace.
    workspace: StudioNode[];

    // Estado visual atual.
    expandedFolders: Set<string>;
    selectedFolderId: string | null;
    activeFileId: string;

    // Permissões e Checkout já calculados pelo Robot Studio.
    canWriteWorkspace: boolean;
    canCreateLibrary: boolean;
    canViewLibraries: boolean;
    canUseLibrary: boolean;

    // Mensagem atual apresentada quando o workspace
    // está em modo somente leitura.
    workspaceReadOnlyMessage: string;

    // Estilos originais.
    styles: RobotStudioExplorerStyles;

    // Atualiza a pasta atualmente selecionada.
    onSelectFolder: (
        folderId: string | null
    ) => void;

    // Expande/recolhe uma pasta.
    onToggleFolder: (
        folderId: string
    ) => void;

    // Abre arquivo no Monaco.
    onOpenFile: (
        node: StudioNode
    ) => void;

    // Ações globais do cabeçalho do Explorer.
    onManageLibraries: () => void;
    onCreateFile: () => void;
    onCreateFolder: () => void;

    // Ações específicas de uma pasta.
    onCreateFileInFolder: (
        targetFolderId: string | null
    ) => void;

    onCreateFolderInFolder: (
        targetFolderId: string | null
    ) => void;

    // Ações dos itens da árvore.
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
// COMPONENTE
// ============================================================

function RobotStudioExplorer({
    projectName,
    workspace,
    expandedFolders,
    selectedFolderId,
    activeFileId,
    canWriteWorkspace,
    canCreateLibrary,
    canViewLibraries,
    canUseLibrary,
    workspaceReadOnlyMessage,
    styles,
    onSelectFolder,
    onToggleFolder,
    onOpenFile,
    onManageLibraries,
    onCreateFile,
    onCreateFolder,
    onCreateFileInFolder,
    onCreateFolderInFolder,
    onRenameItem,
    onDeleteItem,
    onRemoveLibrary,
}: RobotStudioExplorerProps) {

    return (
        <aside style={styles.sidebar}>

            {/* =================================================
                CABEÇALHO DO EXPLORER
            ================================================= */}

            <div style={styles.sidebarHeader}>
                <span>EXPLORER</span>

                <div style={styles.sidebarActions}>

                    {/* =========================================
                        GERENCIAMENTO DE BIBLIOTECAS
                    ========================================= */}

                    <button
                        type="button"
                        onClick={onManageLibraries}
                        disabled={
                            !canWriteWorkspace ||
                            (
                                !canCreateLibrary &&
                                !(
                                    canViewLibraries &&
                                    canUseLibrary
                                )
                            )
                        }
                        style={{
                            ...styles.libraryCreateButton,

                            opacity:
                                canWriteWorkspace &&
                                (
                                    canCreateLibrary ||
                                    (
                                        canViewLibraries &&
                                        canUseLibrary
                                    )
                                )
                                    ? 1
                                    : 0.4,

                            cursor:
                                canWriteWorkspace &&
                                (
                                    canCreateLibrary ||
                                    (
                                        canViewLibraries &&
                                        canUseLibrary
                                    )
                                )
                                    ? "pointer"
                                    : "not-allowed",
                        }}
                        title={
                            canWriteWorkspace
                                ? "Gerenciar bibliotecas do projeto"
                                : workspaceReadOnlyMessage
                        }
                        aria-label="Gerenciar bibliotecas"
                    >
                        <Plus size={13} />
                        <span>Lib</span>
                    </button>


                    {/* =========================================
                        NOVO ARQUIVO
                    ========================================= */}

                    <button
                        type="button"
                        onClick={onCreateFile}

                        // Sem Checkout, não permite criar.
                        disabled={!canWriteWorkspace}

                        style={{
                            ...styles.smallIconButton,

                            opacity:
                                canWriteWorkspace
                                    ? 1
                                    : 0.4,

                            cursor:
                                canWriteWorkspace
                                    ? "pointer"
                                    : "not-allowed",
                        }}

                        title={
                            canWriteWorkspace
                                ? "Novo arquivo"
                                : workspaceReadOnlyMessage
                        }

                        aria-label="Novo arquivo"
                    >
                        <FilePlus2 size={15} />
                    </button>


                    {/* =========================================
                        NOVA PASTA
                    ========================================= */}

                    <button
                        type="button"
                        onClick={onCreateFolder}

                        // Sem Checkout, não permite criar.
                        disabled={!canWriteWorkspace}

                        style={{
                            ...styles.smallIconButton,

                            opacity:
                                canWriteWorkspace
                                    ? 1
                                    : 0.4,

                            cursor:
                                canWriteWorkspace
                                    ? "pointer"
                                    : "not-allowed",
                        }}

                        title={
                            canWriteWorkspace
                                ? "Nova pasta"
                                : workspaceReadOnlyMessage
                        }

                        aria-label="Nova pasta"
                    >
                        <FolderPlus size={15} />
                    </button>

                </div>
            </div>


            {/* =================================================
                RAIZ DO PROJETO
            ================================================= */}

            <button
                type="button"
                onClick={() =>
                    onSelectFolder(
                        null
                    )
                }
                style={{
                    ...styles.projectRoot,

                    background:
                        selectedFolderId === null
                            ? "#252526"
                            : "transparent",
                }}
            >
                <ChevronDown size={14} />
                <FolderOpen size={16} />
                <strong>{projectName}</strong>
            </button>


            {/* =================================================
                ÁRVORE DO WORKSPACE
            ================================================= */}

            <div style={styles.tree}>
                {workspace.map((node) => (
                    <StudioTreeNode
                        key={node.id}
                        node={node}
                        expandedFolders={expandedFolders}
                        selectedFolderId={selectedFolderId}
                        activeFileId={activeFileId}
                        canWriteWorkspace={canWriteWorkspace}
                        canUseLibrary={canUseLibrary}
                        styles={styles}
                        onSelectFolder={(folderId) =>
                            onSelectFolder(
                                folderId
                            )
                        }
                        onToggleFolder={onToggleFolder}
                        onOpenFile={onOpenFile}
                        onCreateFileInFolder={onCreateFileInFolder}
                        onCreateFolderInFolder={onCreateFolderInFolder}
                        onRenameItem={onRenameItem}
                        onDeleteItem={onDeleteItem}
                        onRemoveLibrary={onRemoveLibrary}
                    />
                ))}
            </div>


            {/* =================================================
                DESTINO DE CRIAÇÃO
            ================================================= */}

            <div style={styles.sidebarFooter}>
                <span>Destino de criação:</span>

                <strong>
                    {selectedFolderId
                        ? findNodeById(
                            workspace,
                            selectedFolderId
                        )?.name || "Pasta"
                        : "Raiz"}
                </strong>
            </div>

        </aside>
    );
}


export default RobotStudioExplorer;
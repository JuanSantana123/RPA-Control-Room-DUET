/**
 * ÁRVORE VISUAL DO CATÁLOGO DE BIBLIOTECAS
 * ==========================================
 *
 * Responsável somente pela renderização recursiva da árvore:
 *
 * - pastas;
 * - libraries;
 * - expansão/recolhimento;
 * - menus contextuais;
 * - callbacks de ações.
 *
 * IMPORTANTE
 * ----------
 * Este componente NÃO realiza chamadas HTTP e NÃO mantém regra
 * de negócio. Todas as ações são devolvidas ao componente pai.
 */

import {
    ChevronDown,
    ChevronRight,
    FileCode2,
    Folder,
    FolderPlus,
    MoreVertical,
    Move,
    Pencil,
    Plus,
    RotateCcw,
    Trash2,
} from "lucide-react";

import type {
    LibraryCatalogItem,
    LibraryFolderTreeNode,
    LibraryTreeNode,
} from "../types/libraries";


interface LibraryCatalogTreeProps {
    nodes: LibraryTreeNode[];

    searchValue: string;

    expandedFolders: Set<number>;

    selectedFolderId: number | null;

    selectedLibraryId: number | null;

    openFolderMenu: number | null;

    openLibraryMenu: number | null;

    onToggleFolder: (
        folderId: number
    ) => void;

    onSelectFolder: (
        folder: LibraryFolderTreeNode
    ) => void;

    onSelectLibrary: (
        library: LibraryCatalogItem
    ) => void | Promise<void>;

    onOpenFolderMenu: (
        folderId: number | null
    ) => void;

    onOpenLibraryMenu: (
        libraryId: number | null
    ) => void;

    onCreateFolder: (
        parentId: number | null
    ) => void;

    onCreateLibrary: (
        folderId: number | null
    ) => void;

    onRenameFolder: (
        folder: LibraryFolderTreeNode
    ) => void;

    onMoveFolder: (
        folder: LibraryFolderTreeNode
    ) => void;

    onEditLibrary: (
        library: LibraryCatalogItem
    ) => void;

    onMoveLibrary: (
        library: LibraryCatalogItem
    ) => void;

    onDeleteFolder: (
        folder: LibraryFolderTreeNode
    ) => void;

    onDeactivateLibrary: (
        library: LibraryCatalogItem
    ) => void;

    onReactivateLibrary: (
        library: LibraryCatalogItem
    ) => void | Promise<void>;
}


function LibraryCatalogTree({
    nodes,
    searchValue,
    expandedFolders,
    selectedFolderId,
    selectedLibraryId,
    openFolderMenu,
    openLibraryMenu,
    onToggleFolder,
    onSelectFolder,
    onSelectLibrary,
    onOpenFolderMenu,
    onOpenLibraryMenu,
    onCreateFolder,
    onCreateLibrary,
    onRenameFolder,
    onMoveFolder,
    onEditLibrary,
    onMoveLibrary,
    onDeleteFolder,
    onDeactivateLibrary,
    onReactivateLibrary,
}: LibraryCatalogTreeProps) {

    const renderNode = (
        node: LibraryTreeNode,
        level: number = 0
    ): React.ReactNode => {
        // ----------------------------------------------------
        // LIBRARY
        // ----------------------------------------------------

        if (node.type === "library") {
            const selected =
                selectedLibraryId === node.id;

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
                                void onSelectLibrary(node);
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
                                    onOpenFolderMenu(null);
                                    onOpenLibraryMenu(
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
                                            onOpenLibraryMenu(null);

                                            void onSelectLibrary(
                                                node
                                            );
                                        }}
                                    >
                                        <FileCode2 size={15} />
                                        <span>
                                            Ver detalhes
                                        </span>
                                    </button>

                                    {node.is_active ? (
                                        <>
                                            <button
                                                type="button"
                                                onClick={() => {
                                                    onOpenLibraryMenu(
                                                        null
                                                    );

                                                    onEditLibrary(
                                                        node
                                                    );
                                                }}
                                            >
                                                <Pencil size={15} />
                                                <span>
                                                    Editar metadados
                                                </span>
                                            </button>

                                            <button
                                                type="button"
                                                onClick={() => {
                                                    onOpenLibraryMenu(
                                                        null
                                                    );

                                                    onMoveLibrary(
                                                        node
                                                    );
                                                }}
                                            >
                                                <Move size={15} />
                                                <span>
                                                    Mover para pasta
                                                </span>
                                            </button>

                                            <button
                                                type="button"
                                                className="library-context-danger"
                                                onClick={() => {
                                                    onOpenLibraryMenu(
                                                        null
                                                    );

                                                    onDeactivateLibrary(
                                                        node
                                                    );
                                                }}
                                            >
                                                <Trash2 size={15} />
                                                <span>
                                                    Desativar
                                                </span>
                                            </button>
                                        </>
                                    ) : (
                                        <button
                                            type="button"
                                            onClick={() => {
                                                onOpenLibraryMenu(
                                                    null
                                                );

                                                void onReactivateLibrary(
                                                    node
                                                );
                                            }}
                                        >
                                            <RotateCcw size={15} />
                                            <span>
                                                Reativar
                                            </span>
                                        </button>
                                    )}
                                </div>
                            )}
                        </div>
                    </div>
                </div>
            );
        }


        // ----------------------------------------------------
        // PASTA
        // ----------------------------------------------------

        const hasChildren =
            node.children.length > 0;

        const forceExpanded =
            Boolean(searchValue.trim());

        const expanded =
            forceExpanded ||
            expandedFolders.has(node.id);

        const selected =
            selectedFolderId === node.id;

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
                                onToggleFolder(node.id);
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
                            onSelectFolder(node);
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
                                onOpenLibraryMenu(null);
                                onOpenFolderMenu(
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
                                        onCreateFolder(node.id)
                                    }
                                >
                                    <FolderPlus size={15} />
                                    <span>Criar subpasta</span>
                                </button>

                                <button
                                    type="button"
                                    onClick={() =>
                                        onCreateLibrary(node.id)
                                    }
                                >
                                    <Plus size={15} />
                                    <span>Nova biblioteca aqui</span>
                                </button>

                                <button
                                    type="button"
                                    onClick={() =>
                                        onRenameFolder(node)
                                    }
                                >
                                    <Pencil size={15} />
                                    <span>Renomear</span>
                                </button>

                                <button
                                    type="button"
                                    onClick={() =>
                                        onMoveFolder(node)
                                    }
                                >
                                    <Move size={15} />
                                    <span>Mover pasta</span>
                                </button>

                                <button
                                    type="button"
                                    className="library-context-danger"
                                    onClick={() =>
                                        onDeleteFolder(node)
                                    }
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
                            renderNode(
                                child,
                                level + 1
                            )
                        )}
                    </div>
                )}
            </div>
        );
    };


    return (
        <>
            {nodes.map((node) =>
                renderNode(node)
            )}
        </>
    );
}


export default LibraryCatalogTree;

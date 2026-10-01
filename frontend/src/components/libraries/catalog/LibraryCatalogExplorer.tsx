/**
 * EXPLORADOR DO CATÁLOGO DE BIBLIOTECAS
 * ======================================
 *
 * Responsável por:
 * - busca visual;
 * - totais do catálogo;
 * - estados de loading/vazio;
 * - composição da árvore recursiva.
 *
 * Nenhuma chamada HTTP é feita aqui.
 */

import {
    BookOpen,
    Search,
    X,
} from "lucide-react";

import LibraryCatalogTree from "./LibraryCatalogTree";

import type {
    LibraryCatalogItem,
    LibraryFolderTreeNode,
    LibraryTreeNode,
} from "../types/libraries";


interface LibraryCatalogExplorerProps {
    searchValue: string;

    folderCount: number;

    libraryCount: number;

    loading: boolean;

    nodes: LibraryTreeNode[];

    expandedFolders: Set<number>;

    selectedFolderId: number | null;

    selectedLibraryId: number | null;

    openFolderMenu: number | null;

    openLibraryMenu: number | null;

    onSearchChange: (
        value: string
    ) => void;

    onToggleFolder: (
        folderId: number
    ) => void;

    onSelectFolder: (
        folder: LibraryFolderTreeNode
    ) => void;

    onSelectLibrary: (
        library: LibraryCatalogItem
    ) => void | Promise<void>;

    onReactivateLibrary: (
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
}


function LibraryCatalogExplorer({
    searchValue,
    folderCount,
    libraryCount,
    loading,
    nodes,
    expandedFolders,
    selectedFolderId,
    selectedLibraryId,
    openFolderMenu,
    openLibraryMenu,
    onSearchChange,
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
}: LibraryCatalogExplorerProps) {
    return (
        <aside className="libraries-explorer">
            <div className="libraries-explorer-toolbar">
                <div className="libraries-search">
                    <Search
                        size={15}
                        strokeWidth={1.8}
                    />

                    <input
                        type="search"
                        value={searchValue}
                        placeholder="Buscar biblioteca..."
                        onChange={(event) =>
                            onSearchChange(
                                event.target.value
                            )
                        }
                        aria-label="Buscar no catálogo de Bibliotecas"
                    />

                    {searchValue && (
                        <button
                            type="button"
                            onClick={() =>
                                onSearchChange("")
                            }
                            aria-label="Limpar busca"
                        >
                            <X size={14} />
                        </button>
                    )}
                </div>

                <div className="libraries-explorer-stats">
                    <span>
                        {folderCount} pastas
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
                    {loading ? (
                        <div className="libraries-tree-state">
                            Carregando catálogo...
                        </div>
                    ) : nodes.length === 0 ? (
                        <div className="libraries-tree-empty">
                            <div className="libraries-tree-empty-icon">
                                <BookOpen
                                    size={20}
                                    strokeWidth={1.6}
                                />
                            </div>

                            <strong>
                                {searchValue
                                    ? "Nenhum resultado"
                                    : "Catálogo vazio"}
                            </strong>

                            <span>
                                {searchValue
                                    ? "Tente outro termo de busca."
                                    : "Crie uma pasta ou a primeira biblioteca."}
                            </span>
                        </div>
                    ) : (
                        <LibraryCatalogTree
                            nodes={nodes}
                            searchValue={searchValue}
                            expandedFolders={expandedFolders}
                            selectedFolderId={selectedFolderId}
                            selectedLibraryId={selectedLibraryId}
                            openFolderMenu={openFolderMenu}
                            openLibraryMenu={openLibraryMenu}
                            onToggleFolder={onToggleFolder}
                            onSelectFolder={onSelectFolder}
                            onSelectLibrary={onSelectLibrary}
                            onOpenFolderMenu={onOpenFolderMenu}
                            onOpenLibraryMenu={onOpenLibraryMenu}
                            onCreateFolder={onCreateFolder}
                            onCreateLibrary={onCreateLibrary}
                            onRenameFolder={onRenameFolder}
                            onMoveFolder={onMoveFolder}
                            onEditLibrary={onEditLibrary}
                            onMoveLibrary={onMoveLibrary}
                            onDeleteFolder={
                                onDeleteFolder
                            }
                            onDeactivateLibrary={
                                onDeactivateLibrary
                            }
                            onReactivateLibrary={
                                onReactivateLibrary
                            }
                        />
                    )}
                </div>
            </div>
        </aside>
    );
}


export default LibraryCatalogExplorer;

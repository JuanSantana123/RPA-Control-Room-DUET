/**
 * DETALHES DO CATÁLOGO DE BIBLIOTECAS
 * ====================================
 *
 * Renderiza somente a área direita do catálogo.
 *
 * Estados possíveis:
 * - Library selecionada;
 * - pasta selecionada;
 * - nenhuma seleção.
 *
 * Nenhuma chamada HTTP é realizada neste componente.
 */

import {
    BookOpen,
    FileCode2,
    Folder,
    FolderPlus,
    Move,
    Pencil,
    Plus,
    Upload,
} from "lucide-react";

import {
    formatarData,
} from "../utils/libraryFormatters";

import type {
    LibraryCatalogItem,
    LibraryFolderTreeNode,
    LibraryVersionItem,
} from "../types/libraries";


interface LibraryDetailsPanelProps {
    selectedLibrary:
        LibraryCatalogItem | null;

    selectedFolder:
        LibraryFolderTreeNode | null;

    selectedLibraryPath:
        string[];

    selectedFolderPath:
        string[];

    versions:
        LibraryVersionItem[];

    loadingVersions:
        boolean;

    onMoveLibrary: (
        library: LibraryCatalogItem
    ) => void;

    onEditLibrary: (
        library: LibraryCatalogItem
    ) => void;

    onCreateFolder: (
        parentId: number | null
    ) => void;

    onImportLibrary: (
        folderId: number | null
    ) => void;

    onCreateLibrary: (
        folderId: number | null
    ) => void;
}


function LibraryDetailsPanel({
    selectedLibrary,
    selectedFolder,
    selectedLibraryPath,
    selectedFolderPath,
    versions,
    loadingVersions,
    onMoveLibrary,
    onEditLibrary,
    onCreateFolder,
    onImportLibrary,
    onCreateLibrary,
}: LibraryDetailsPanelProps) {
    return (
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
                                        (
                                            part,
                                            index
                                        ) => (
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

                        {selectedLibrary.is_active && (
                            <div className="libraries-details-actions">
                                <button
                                    type="button"
                                    className="library-button library-button-secondary"
                                    onClick={() =>
                                        onMoveLibrary(
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
                                        onEditLibrary(
                                            selectedLibrary
                                        )
                                    }
                                >
                                    <Pencil size={15} />
                                    Editar
                                </button>
                            </div>
                        )}
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

                    <div className="library-versions-section">
                        <div className="library-versions-header">
                            <div>
                                <h4>
                                    Versões publicadas
                                </h4>

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
                                {versions.map(
                                    (
                                        version
                                    ) => (
                                        <div
                                            key={version.id}
                                            className="library-version-row"
                                        >
                                            <div className="library-version-main">
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

                                            <span
                                                className={`library-version-status ${
                                                    version.is_active
                                                        ? "library-version-status-active"
                                                        : "library-version-status-inactive"
                                                }`}
                                            >
                                                {version.is_active
                                                    ? "Ativa"
                                                    : "Inativa"}
                                            </span>
                                        </div>
                                    )
                                )}
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
                                        .map(
                                            (
                                                part,
                                                index
                                            ) => (
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
                                    {selectedFolder.name}
                                </h3>

                                <p>
                                    Pasta organizacional
                                </p>
                            </div>
                        </div>

                        <div className="libraries-details-actions">
                            <button
                                type="button"
                                className="library-button library-button-secondary"
                                onClick={() =>
                                    onCreateFolder(
                                        selectedFolder.id
                                    )
                                }
                            >
                                <FolderPlus size={15} />
                                Subpasta
                            </button>

                            <button
                                type="button"
                                className="library-button library-button-secondary"
                                onClick={() =>
                                    onImportLibrary(
                                        selectedFolder.id
                                    )
                                }
                            >
                                <Upload size={15} />
                                Importar aqui
                            </button>

                            <button
                                type="button"
                                className="library-button library-button-primary"
                                onClick={() =>
                                    onCreateLibrary(
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
                            <span>
                                Itens diretos
                            </span>

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

                    <h3>
                        Catálogo de Bibliotecas
                    </h3>

                    <p>
                        Selecione uma pasta ou biblioteca no explorador
                        para visualizar detalhes e ações.
                    </p>

                    <div className="libraries-details-empty-actions">
                        <button
                            type="button"
                            className="library-button library-button-secondary"
                            onClick={() =>
                                onCreateFolder(null)
                            }
                        >
                            <FolderPlus size={15} />
                            Criar pasta
                        </button>

                        <button
                            type="button"
                            className="library-button library-button-primary"
                            onClick={() =>
                                onCreateLibrary(null)
                            }
                        >
                            <Plus size={15} />
                            Nova biblioteca
                        </button>
                    </div>
                </div>
            )}
        </div>
    );
}


export default LibraryDetailsPanel;

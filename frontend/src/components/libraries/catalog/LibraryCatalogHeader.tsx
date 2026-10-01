/**
 * CABEÇALHO DO CATÁLOGO DE BIBLIOTECAS
 * =====================================
 *
 * Responsável somente por:
 * - título do módulo;
 * - ações principais;
 * - feedback de erro/sucesso.
 *
 * Não possui chamadas HTTP nem estado de negócio.
 */

import {
    Archive,
    BookOpen,
    FolderPlus,
    LibraryBig,
    Plus,
    RefreshCw,
    Upload,
    X,
} from "lucide-react";

import type {
    LibraryCatalogView,
} from "../types/libraries";

interface LibraryCatalogHeaderProps {
    loading: boolean;

    error: string;

    success: string;

    catalogView:
        LibraryCatalogView;

    onCatalogViewChange:
        (
            view: LibraryCatalogView
        ) => void;

    onRefresh: () => void | Promise<void>;

    onCreateFolder: () => void;

    onImportLibrary: () => void;

    onCreateLibrary: () => void;

    onClearError: () => void;

    onClearSuccess: () => void;
}

function LibraryCatalogHeader({
    loading,
    error,
    success,

    catalogView,
    onCatalogViewChange,

    onRefresh,
    onCreateFolder,
    onImportLibrary,
    onCreateLibrary,
    onClearError,
    onClearSuccess,
}: LibraryCatalogHeaderProps) {
    return (
        <>
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
                        className={`library-button ${
                            catalogView === "active"
                                ? "library-button-primary"
                                : "library-button-secondary"
                        }`}
                        onClick={(event) => {
                            event.stopPropagation();

                            onCatalogViewChange(
                                "active"
                            );
                        }}
                    >
                        <LibraryBig
                            size={15}
                            strokeWidth={1.9}
                        />

                        Ativas
                    </button>

                    <button
                        type="button"
                        className={`library-button ${
                            catalogView === "archived"
                                ? "library-button-primary"
                                : "library-button-secondary"
                        }`}
                        onClick={(event) => {
                            event.stopPropagation();

                            onCatalogViewChange(
                                "archived"
                            );
                        }}
                    >
                        <Archive
                            size={15}
                            strokeWidth={1.9}
                        />

                        Arquivadas
                    </button>

                    <button
                        type="button"
                        className="library-toolbar-button"
                        title="Atualizar catálogo"
                        aria-label="Atualizar catálogo"
                        disabled={loading}
                        onClick={(event) => {
                            event.stopPropagation();
                            void onRefresh();
                        }}
                    >
                        <RefreshCw
                            size={15}
                            strokeWidth={1.9}
                        />
                    </button>

                    {catalogView === "active" && (
                        <>
                            <button
                                type="button"
                                className="library-button library-button-secondary"
                                onClick={(event) => {
                                    event.stopPropagation();
                                    onCreateFolder();
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
                                className="library-button library-button-secondary"
                                onClick={(event) => {
                                    event.stopPropagation();
                                    onImportLibrary();
                                }}
                            >
                                <Upload
                                    size={15}
                                    strokeWidth={1.9}
                                />
                                Importar biblioteca
                            </button>

                            <button
                                type="button"
                                className="library-button library-button-primary"
                                onClick={(event) => {
                                    event.stopPropagation();
                                    onCreateLibrary();
                                }}
                            >
                                <Plus
                                    size={15}
                                    strokeWidth={2}
                                />
                                Nova biblioteca
                            </button>
                        </>
                    )}
                </div>
            </div>

            {(error || success) && (
                <div className="libraries-catalog-message-area">
                    {error && (
                        <div className="library-inline-alert library-inline-alert-error">
                            <span>{error}</span>

                            <button
                                type="button"
                                onClick={onClearError}
                                aria-label="Fechar mensagem de erro"
                            >
                                <X size={15} />
                            </button>
                        </div>
                    )}

                    {success && (
                        <div className="library-inline-alert library-inline-alert-success">
                            <span>{success}</span>

                            <button
                                type="button"
                                onClick={onClearSuccess}
                                aria-label="Fechar mensagem de sucesso"
                            >
                                <X size={15} />
                            </button>
                        </div>
                    )}
                </div>
            )}
        </>
    );
}


export default LibraryCatalogHeader;

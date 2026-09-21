// ============================================================
// DUET CORE - ROBOT STUDIO - LIBRARY ACTIONS MODAL
// ============================================================
//
// Responsabilidade:
// - renderizar o modal inicial de gerenciamento de Libraries;
// - apresentar as duas ações já existentes no Robot Studio:
//   criar uma nova Working Copy ou adicionar uma Library
//   publicada;
// - respeitar as permissões já calculadas pelo Studio.
//
// IMPORTANTE:
// Este componente faz parte de uma refatoração estrutural.
// Nenhuma regra funcional ou visual está sendo alterada.
//
// Este componente NÃO deve:
// - executar chamadas HTTP;
// - criar Libraries;
// - carregar Libraries;
// - modificar o workspace;
// - calcular permissões.
//
// Todas as operações continuam sendo delegadas por callbacks.
// ============================================================

import type {
    CSSProperties,
    MouseEvent,
} from "react";

import {
    FolderOpen,
    Plus,
    X,
} from "lucide-react";


interface LibraryActionsModalStyles {
    modalBackdrop: CSSProperties;
    modalCard: CSSProperties;
    modalHeader: CSSProperties;
    modalEyebrow: CSSProperties;
    modalTitle: CSSProperties;
    modalSubtitle: CSSProperties;
    modalClose: CSSProperties;
    libraryChoiceGrid: CSSProperties;
    libraryChoiceButton: CSSProperties;
    libraryChoiceIcon: CSSProperties;
}


interface LibraryActionsModalProps {
    open: boolean;

    canCreateLibrary: boolean;
    canViewLibraries: boolean;
    canUseLibrary: boolean;

    styles: LibraryActionsModalStyles;

    onClose: () => void;
    onCreateLibrary: () => void;
    onAddExistingLibraries: () => void;
}


function LibraryActionsModal({
    open,
    canCreateLibrary,
    canViewLibraries,
    canUseLibrary,
    styles,
    onClose,
    onCreateLibrary,
    onAddExistingLibraries,
}: LibraryActionsModalProps) {

    if (!open) {
        return null;
    }


    const handleBackdropMouseDown = (
        event: MouseEvent<HTMLDivElement>
    ) => {

        if (
            event.target ===
            event.currentTarget
        ) {
            onClose();
        }
    };


    return (
        <div
            style={styles.modalBackdrop}
            onMouseDown={handleBackdropMouseDown}
        >
            <div style={styles.modalCard}>

                <div style={styles.modalHeader}>

                    <div>
                        <div style={styles.modalEyebrow}>
                            PROJECT LIBRARIES
                        </div>

                        <h2 style={styles.modalTitle}>
                            Bibliotecas
                        </h2>

                        <p style={styles.modalSubtitle}>
                            Crie uma nova Working Copy ou utilize
                            bibliotecas que já estão publicadas.
                        </p>
                    </div>


                    <button
                        type="button"
                        onClick={onClose}
                        style={styles.modalClose}
                        aria-label="Fechar"
                    >
                        <X size={16} />
                    </button>

                </div>


                <div style={styles.libraryChoiceGrid}>

                    {/* =========================================
                        CRIAR NOVA
                    ========================================= */}

                    <button
                        type="button"
                        onClick={onCreateLibrary}
                        disabled={!canCreateLibrary}
                        style={{
                            ...styles.libraryChoiceButton,

                            opacity:
                                canCreateLibrary
                                    ? 1
                                    : 0.45,

                            cursor:
                                canCreateLibrary
                                    ? "pointer"
                                    : "not-allowed",
                        }}
                    >
                        <div style={styles.libraryChoiceIcon}>
                            <Plus size={20} />
                        </div>

                        <div>
                            <strong>
                                Criar nova biblioteca
                            </strong>

                            <span>
                                Cria uma Working Copy nova e isolada
                                neste projeto.
                            </span>

                            {!canCreateLibrary && (
                                <small>
                                    Requer Libraries:create
                                </small>
                            )}
                        </div>
                    </button>


                    {/* =========================================
                        USAR EXISTENTE
                    ========================================= */}

                    <button
                        type="button"
                        onClick={onAddExistingLibraries}
                        disabled={
                            !canViewLibraries ||
                            !canUseLibrary
                        }
                        style={{
                            ...styles.libraryChoiceButton,

                            opacity:
                                canViewLibraries &&
                                canUseLibrary
                                    ? 1
                                    : 0.45,

                            cursor:
                                canViewLibraries &&
                                canUseLibrary
                                    ? "pointer"
                                    : "not-allowed",
                        }}
                    >
                        <div style={styles.libraryChoiceIcon}>
                            <FolderOpen size={20} />
                        </div>

                        <div>
                            <strong>
                                Adicionar existentes
                            </strong>

                            <span>
                                Selecione uma ou várias bibliotecas
                                já publicadas em Produção.
                            </span>

                            {(
                                !canViewLibraries ||
                                !canUseLibrary
                            ) && (
                                <small>
                                    Requer Libraries:view e Libraries:use
                                </small>
                            )}
                        </div>
                    </button>

                </div>
            </div>
        </div>
    );
}


export default LibraryActionsModal;
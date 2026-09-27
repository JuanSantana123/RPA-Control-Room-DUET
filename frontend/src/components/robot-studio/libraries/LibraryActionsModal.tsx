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
import { createPortal } from "react-dom";

import {
    FolderOpen,
    Plus,
    X,
} from "lucide-react";
import { useDialogFocus } from "../../../hooks/ui/useDialogFocus";
import { Button, IconButton } from "../../ui/Button";


export interface LibraryActionsModalStyles {
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
    const dialogRef = useDialogFocus<HTMLDivElement>({
        open,
        onClose,
    });

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


    return createPortal(
        <div
            className="ui-modal-backdrop"
            style={styles.modalBackdrop}
            onMouseDown={handleBackdropMouseDown}
        >
            <div
                ref={dialogRef}
                className="ui-modal-surface"
                style={styles.modalCard}
                role="dialog"
                aria-modal="true"
                aria-labelledby="studio-library-actions-title"
                tabIndex={-1}
            >

                <div className="ui-modal-header" style={styles.modalHeader}>

                    <div>
                        <div style={styles.modalEyebrow}>
                            PROJECT LIBRARIES
                        </div>

                        <h2 id="studio-library-actions-title" style={styles.modalTitle}>
                            Bibliotecas
                        </h2>

                        <p style={styles.modalSubtitle}>
                            Crie uma nova Working Copy ou utilize
                            bibliotecas que já estão publicadas.
                        </p>
                    </div>


                    <IconButton
                        label="Fechar"
                        icon={<X size={16} aria-hidden="true" />}
                        onClick={onClose}
                        style={styles.modalClose}
                    />

                </div>


                <div style={styles.libraryChoiceGrid}>

                    {/* =========================================
                        CRIAR NOVA
                    ========================================= */}

                    <Button
                        variant="secondary"
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
                    </Button>


                    {/* =========================================
                        USAR EXISTENTE
                    ========================================= */}

                    <Button
                        variant="secondary"
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
                    </Button>

                </div>
            </div>
        </div>,
        document.body,
    );
}


export default LibraryActionsModal;

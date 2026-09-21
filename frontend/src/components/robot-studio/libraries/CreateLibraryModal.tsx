// ============================================================
// DUET CORE - ROBOT STUDIO - CREATE LIBRARY MODAL
// ============================================================
//
// Responsabilidade:
// - renderizar o formulário atual de criação de uma Library;
// - editar visualmente nome, import_name e descrição;
// - apresentar estado de criação e mensagens de erro.
//
// IMPORTANTE:
// Este componente faz parte exclusivamente da modularização
// do RobotStudio.tsx.
//
// Nenhuma regra de criação, validação, nomenclatura ou
// persistência deve ser modificada neste componente.
//
// Este componente NÃO deve:
// - executar chamadas HTTP;
// - criar Library no backend;
// - modificar o workspace;
// - decidir regras de versionamento;
// - implementar suggestImportName.
//
// A função de sugestão e todas as operações reais continuam
// sendo fornecidas pelo Robot Studio.
// ============================================================

import type {
    CSSProperties,
    MouseEvent,
} from "react";

import {
    X,
} from "lucide-react";


interface CreateLibraryModalStyles {
    modalBackdrop: CSSProperties;
    modalCard: CSSProperties;
    modalHeader: CSSProperties;
    modalEyebrow: CSSProperties;
    modalTitle: CSSProperties;
    modalSubtitle: CSSProperties;
    modalClose: CSSProperties;
    modalBody: CSSProperties;
    modalField: CSSProperties;
    modalInput: CSSProperties;
    modalHint: CSSProperties;
    modalTextarea: CSSProperties;
    modalError: CSSProperties;
    modalFooter: CSSProperties;
    modalSecondaryButton: CSSProperties;
    modalPrimaryButton: CSSProperties;
}


interface CreateLibraryModalProps {
    open: boolean;

    libraryName: string;
    libraryImportName: string;
    libraryImportTouched: boolean;
    libraryDescription: string;

    libraryCreateError: string;
    creatingLibrary: boolean;

    styles: CreateLibraryModalStyles;

    onClose: () => void;

    onLibraryNameChange: (
        value: string
    ) => void;

    onLibraryImportNameChange: (
        value: string
    ) => void;

    onLibraryImportTouchedChange: (
        touched: boolean
    ) => void;

    onLibraryDescriptionChange: (
        value: string
    ) => void;

    onClearError: () => void;

    onSuggestImportName: (
        value: string
    ) => string;

    onCreateLibrary: () => void;
}


function CreateLibraryModal({
    open,
    libraryName,
    libraryImportName,
    libraryImportTouched,
    libraryDescription,
    libraryCreateError,
    creatingLibrary,
    styles,
    onClose,
    onLibraryNameChange,
    onLibraryImportNameChange,
    onLibraryImportTouchedChange,
    onLibraryDescriptionChange,
    onClearError,
    onSuggestImportName,
    onCreateLibrary,
}: CreateLibraryModalProps) {

    if (!open) {
        return null;
    }


    const handleBackdropMouseDown = (
        event: MouseEvent<HTMLDivElement>
    ) => {

        if (
            event.target ===
                event.currentTarget &&
            !creatingLibrary
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
                            REUSABLE LIBRARY
                        </div>

                        <h2 style={styles.modalTitle}>
                            Nova biblioteca
                        </h2>

                        <p style={styles.modalSubtitle}>
                            Crie uma Working Copy isolada neste projeto.
                            Ela só aparecerá em Produção após o Release.
                        </p>
                    </div>


                    <button
                        type="button"
                        onClick={() =>
                            !creatingLibrary &&
                            onClose()
                        }
                        style={styles.modalClose}
                        disabled={creatingLibrary}
                        aria-label="Fechar"
                    >
                        <X size={16} />
                    </button>

                </div>


                <div style={styles.modalBody}>

                    {/* =========================================
                        NOME
                    ========================================= */}

                    <label style={styles.modalField}>
                        <span>Nome</span>

                        <input
                            type="text"
                            autoFocus
                            value={libraryName}
                            placeholder="Ex.: Financeiro Core"
                            onChange={(event) => {

                                const value =
                                    event.target.value;

                                onLibraryNameChange(
                                    value
                                );

                                onClearError();

                                if (
                                    !libraryImportTouched
                                ) {
                                    onLibraryImportNameChange(
                                        onSuggestImportName(
                                            value
                                        )
                                    );
                                }
                            }}
                            style={styles.modalInput}
                        />
                    </label>


                    {/* =========================================
                        IMPORT NAME
                    ========================================= */}

                    <label style={styles.modalField}>
                        <span>import_name</span>

                        <input
                            type="text"
                            value={libraryImportName}
                            placeholder="financeiro_core"
                            onChange={(event) => {

                                onLibraryImportTouchedChange(
                                    true
                                );

                                onLibraryImportNameChange(
                                    event.target.value
                                );

                                onClearError();
                            }}
                            style={styles.modalInput}
                        />

                        <small style={styles.modalHint}>
                            Namespace Python usado em imports, por exemplo:
                            from financeiro_core import ...
                        </small>
                    </label>


                    {/* =========================================
                        DESCRIÇÃO
                    ========================================= */}

                    <label style={styles.modalField}>
                        <span>
                            Descrição <em>opcional</em>
                        </span>

                        <textarea
                            value={libraryDescription}
                            placeholder="Responsabilidade desta biblioteca..."
                            onChange={(event) =>
                                onLibraryDescriptionChange(
                                    event.target.value
                                )
                            }
                            style={styles.modalTextarea}
                        />
                    </label>


                    {libraryCreateError && (
                        <div style={styles.modalError}>
                            {libraryCreateError}
                        </div>
                    )}

                </div>


                <div style={styles.modalFooter}>

                    <button
                        type="button"
                        onClick={onClose}
                        disabled={creatingLibrary}
                        style={styles.modalSecondaryButton}
                    >
                        Cancelar
                    </button>


                    <button
                        type="button"
                        onClick={onCreateLibrary}
                        disabled={
                            creatingLibrary ||
                            !libraryName.trim() ||
                            !libraryImportName.trim()
                        }
                        style={{
                            ...styles.modalPrimaryButton,

                            opacity:
                                creatingLibrary ||
                                !libraryName.trim() ||
                                !libraryImportName.trim()
                                    ? 0.55
                                    : 1,
                        }}
                    >
                        {creatingLibrary
                            ? "Criando..."
                            : "Criar biblioteca"}
                    </button>

                </div>

            </div>
        </div>
    );
}


export default CreateLibraryModal;
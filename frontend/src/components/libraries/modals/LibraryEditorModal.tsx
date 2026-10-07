/**
 * MODAL - CRIAR / EDITAR LIBRARY
 * ===============================
 *
 * Componente exclusivamente visual.
 *
 * As regras de criação/edição e persistência permanecem
 * no fluxo de orquestração da feature.
 */

import {
    Move,
    X,
} from "lucide-react";

import type {
    LibraryEditorMode,
} from "../types/libraries";


interface LibraryEditorModalProps {
    mode: Exclude<
        LibraryEditorMode,
        null
    > | null;

    name: string;

    importName: string;

    description: string;

    destinationLabel: string;

    busy: boolean;

    onNameChange: (
        value: string
    ) => void;

    onImportNameChange: (
        value: string
    ) => void;

    onDescriptionChange: (
        value: string
    ) => void;

    onChangeLocation: () => void;

    onCancel: () => void;

    onSave: () => void | Promise<void>;
}


function LibraryEditorModal({
    mode,
    name,
    importName,
    description,
    destinationLabel,
    busy,
    onNameChange,
    onImportNameChange,
    onDescriptionChange,
    onChangeLocation,
    onCancel,
    onSave,
}: LibraryEditorModalProps) {
    if (!mode) {
        return null;
    }

    const creating =
        mode === "create";

    return (
        <div
            className="library-modal-backdrop"
            role="presentation"
            onMouseDown={(event) => {
                if (
                    !busy &&
                    event.target ===
                        event.currentTarget
                ) {
                    onCancel();
                }
            }}
        >
            <div
                className="library-modal library-modal-large"
                role="dialog"
                aria-modal="true"
                aria-labelledby="library-editor-title"
                onClick={(event) =>
                    event.stopPropagation()
                }
            >
                <div className="library-modal-header">
                    <div>
                        <div className="library-modal-eyebrow">
                            BIBLIOTECA REUTILIZÁVEL
                        </div>

                        <h3 id="library-editor-title">
                            {creating
                                ? "Nova biblioteca"
                                : "Editar biblioteca"}
                        </h3>

                        <p>
                            {creating
                                ? "Cadastre a identidade da biblioteca. As versões serão publicadas separadamente."
                                : "Altere os metadados amigáveis. O import_name permanece imutável."}
                        </p>
                    </div>

                    <button
                        type="button"
                        className="library-modal-close"
                        disabled={busy}
                        onClick={onCancel}
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
                                value={name}
                                placeholder="Ex.: Financeiro Core"
                                disabled={busy}
                                onChange={(event) =>
                                    onNameChange(
                                        event.target.value
                                    )
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
                                value={importName}
                                placeholder="Ex.: financeiro_core"
                                disabled={
                                    busy ||
                                    !creating
                                }
                                onChange={(event) =>
                                    onImportNameChange(
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
                            value={description}
                            placeholder="Explique a finalidade desta biblioteca..."
                            disabled={busy}
                            onChange={(event) =>
                                onDescriptionChange(
                                    event.target.value
                                )
                            }
                        />
                    </div>

                    {creating && (
                        <div className="library-modal-location-card">
                            <div>
                                <span>
                                    Local
                                </span>

                                <strong>
                                    {destinationLabel}
                                </strong>

                                <small>
                                    A organização do catálogo é independente da estrutura Python interna.
                                </small>
                            </div>

                            <button
                                type="button"
                                className="library-button library-button-secondary"
                                disabled={busy}
                                onClick={
                                    onChangeLocation
                                }
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
                        disabled={busy}
                        onClick={onCancel}
                    >
                        Cancelar
                    </button>

                    <button
                        type="button"
                        className="library-button library-button-primary"
                        disabled={
                            busy ||
                            !name.trim() ||
                            (
                                creating &&
                                !importName.trim()
                            )
                        }
                        onClick={() =>
                            void onSave()
                        }
                    >
                        {busy
                            ? "Salvando..."
                            : creating
                                ? "Criar biblioteca"
                                : "Salvar alterações"}
                    </button>
                </div>
            </div>
        </div>
    );
}


export default LibraryEditorModal;

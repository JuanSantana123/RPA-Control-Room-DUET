/**
 * MODAL - CRIAR / RENOMEAR PASTA
 * ===============================
 *
 * Componente exclusivamente visual.
 *
 * Regras de persistência continuam fora dele.
 */

import {
    Move,
    X,
} from "lucide-react";

import type {
    FolderEditorMode,
} from "../types/libraries";


interface LibraryFolderEditorModalProps {
    mode: Exclude<
        FolderEditorMode,
        null
    > | null;

    name: string;

    destinationLabel: string;

    busy: boolean;

    onNameChange: (
        value: string
    ) => void;

    onChangeLocation: () => void;

    onCancel: () => void;

    onSave: () => void | Promise<void>;
}


function LibraryFolderEditorModal({
    mode,
    name,
    destinationLabel,
    busy,
    onNameChange,
    onChangeLocation,
    onCancel,
    onSave,
}: LibraryFolderEditorModalProps) {
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
                className="library-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="library-folder-editor-title"
                onClick={(event) =>
                    event.stopPropagation()
                }
            >
                <div className="library-modal-header">
                    <div>
                        <div className="library-modal-eyebrow">
                            CATÁLOGO GLOBAL
                        </div>

                        <h3 id="library-folder-editor-title">
                            {creating
                                ? "Nova pasta"
                                : "Renomear pasta"}
                        </h3>

                        <p>
                            {creating
                                ? "Crie uma pasta organizacional em qualquer nível do catálogo."
                                : "Altere somente o nome desta pasta."}
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
                    <div className="library-modal-field">
                        <label htmlFor="library-folder-name">
                            Nome da pasta
                        </label>

                        <input
                            id="library-folder-name"
                            type="text"
                            autoFocus
                            value={name}
                            placeholder="Ex.: Financeiro"
                            disabled={busy}
                            onChange={(event) =>
                                onNameChange(
                                    event.target.value
                                )
                            }
                            onKeyDown={(event) => {
                                if (
                                    event.key ===
                                    "Enter"
                                ) {
                                    void onSave();
                                }
                            }}
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
                                Alterar local
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
                            !name.trim()
                        }
                        onClick={() =>
                            void onSave()
                        }
                    >
                        {busy
                            ? "Salvando..."
                            : creating
                                ? "Criar pasta"
                                : "Salvar nome"}
                    </button>
                </div>
            </div>
        </div>
    );
}


export default LibraryFolderEditorModal;

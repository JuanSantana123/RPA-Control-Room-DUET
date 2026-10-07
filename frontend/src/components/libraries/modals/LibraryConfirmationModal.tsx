/**
 * MODAL - CONFIRMAÇÃO DE AÇÃO DESTRUTIVA
 * =======================================
 *
 * Componente visual reutilizável para:
 * - excluir pasta;
 * - desativar Library.
 *
 * A execução da ação permanece no componente/orquestrador.
 */

import {
    Trash2,
} from "lucide-react";

import type {
    LibraryConfirmationState,
} from "../types/libraries";


interface LibraryConfirmationModalProps {
    confirmation:
        LibraryConfirmationState;

    busy: boolean;

    onCancel: () => void;

    onConfirm: () => void | Promise<void>;
}


function LibraryConfirmationModal({
    confirmation,
    busy,
    onCancel,
    onConfirm,
}: LibraryConfirmationModalProps) {
    if (!confirmation) {
        return null;
    }

    const deletingFolder =
        confirmation.kind ===
        "delete-folder";

    return (
        <div
            className="library-modal-backdrop library-confirm-backdrop"
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
                className="library-confirm-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="library-confirm-title"
                onClick={(event) =>
                    event.stopPropagation()
                }
            >
                <div className="library-confirm-icon">
                    <Trash2
                        size={20}
                        strokeWidth={1.8}
                    />
                </div>

                <div className="library-confirm-content">
                    <div className="library-modal-eyebrow">
                        CONFIRMAÇÃO
                    </div>

                    <h3 id="library-confirm-title">
                        {deletingFolder
                            ? "Excluir pasta?"
                            : "Desativar biblioteca?"}
                    </h3>

                    <p>
                        {deletingFolder
                            ? `A pasta “${confirmation.folder.name}” só poderá ser excluída se estiver vazia.`
                            : `A biblioteca “${confirmation.library.name}” deixará de aparecer para novos vínculos. O histórico publicado não será apagado.`}
                    </p>
                </div>

                <div className="library-confirm-actions">
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
                        className="library-button library-button-danger"
                        disabled={busy}
                        onClick={() =>
                            void onConfirm()
                        }
                    >
                        {busy
                            ? "Processando..."
                            : deletingFolder
                                ? "Excluir pasta"
                                : "Desativar biblioteca"}
                    </button>
                </div>
            </div>
        </div>
    );
}


export default LibraryConfirmationModal;

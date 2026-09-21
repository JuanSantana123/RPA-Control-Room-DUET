// ============================================================
// DUET CORE - ROBOT STUDIO
// ADD EXISTING LIBRARIES MODAL
// ============================================================
//
// Responsabilidade:
// - renderizar o catálogo de Libraries publicadas disponíveis
//   para associação ao AutomationProject;
// - apresentar seleção múltipla;
// - apresentar seleção explícita da versão;
// - informar quando a versão selecionada é anterior à versão
//   vigente em Produção.
//
// IMPORTANTE:
// Este componente preserva a interface e as condições atuais
// existentes no RobotStudio.tsx.
//
// Este componente NÃO deve:
// - buscar Libraries na API;
// - adicionar dependências;
// - decidir qual versão deve ser utilizada;
// - modificar o workspace;
// - implementar regras de versionamento.
//
// Toda operação é recebida por callbacks.
// ============================================================

import type {
    CSSProperties,
    MouseEvent,
} from "react";

import {
    X,
} from "lucide-react";

import type {
    AvailableProjectLibrary,
} from "../../../types/robotStudio";


interface AddExistingLibrariesModalStyles {
    modalBackdrop: CSSProperties;
    modalCardWide: CSSProperties;
    modalHeader: CSSProperties;
    modalEyebrow: CSSProperties;
    modalTitle: CSSProperties;
    modalSubtitle: CSSProperties;
    modalClose: CSSProperties;

    existingLibrariesBody: CSSProperties;
    libraryEmptyState: CSSProperties;
    existingLibrariesList: CSSProperties;
    existingLibraryRow: CSSProperties;
    existingLibraryMain: CSSProperties;
    libraryCheckbox: CSSProperties;
    existingLibraryInfo: CSSProperties;
    existingLibraryNameRow: CSSProperties;
    libraryAlreadyBadge: CSSProperties;
    existingLibraryDescription: CSSProperties;
    existingLibraryVersionArea: CSSProperties;
    libraryVersionSelect: CSSProperties;
    productionVersionInfo: CSSProperties;
    oldVersionWarning: CSSProperties;

    modalError: CSSProperties;
    modalFooter: CSSProperties;
    librarySelectionCount: CSSProperties;
    modalSecondaryButton: CSSProperties;
    modalPrimaryButton: CSSProperties;
}


interface AddExistingLibrariesModalProps {
    open: boolean;

    availableLibraries: AvailableProjectLibrary[];

    selectedExistingLibraries: Set<number>;

    selectedExistingVersions:
        Record<number, number>;

    loadingAvailableLibraries: boolean;
    addingExistingLibraries: boolean;

    existingLibraryError: string;

    styles: AddExistingLibrariesModalStyles;

    onClose: () => void;

    onToggleLibrary: (
        libraryId: number
    ) => void;

    onSelectVersion: (
        libraryId: number,
        versionId: number
    ) => void;

    onAddLibraries: () => void;
}


function AddExistingLibrariesModal({
    open,
    availableLibraries,
    selectedExistingLibraries,
    selectedExistingVersions,
    loadingAvailableLibraries,
    addingExistingLibraries,
    existingLibraryError,
    styles,
    onClose,
    onToggleLibrary,
    onSelectVersion,
    onAddLibraries,
}: AddExistingLibrariesModalProps) {

    if (!open) {
        return null;
    }


    const handleBackdropMouseDown = (
        event: MouseEvent<HTMLDivElement>
    ) => {

        if (
            event.target ===
                event.currentTarget &&
            !addingExistingLibraries
        ) {
            onClose();
        }
    };


    return (
        <div
            style={styles.modalBackdrop}
            onMouseDown={handleBackdropMouseDown}
        >
            <div style={styles.modalCardWide}>

                {/* =============================================
                    CABEÇALHO
                ============================================= */}

                <div style={styles.modalHeader}>

                    <div>
                        <div style={styles.modalEyebrow}>
                            PUBLISHED LIBRARIES
                        </div>

                        <h2 style={styles.modalTitle}>
                            Adicionar bibliotecas
                        </h2>

                        <p style={styles.modalSubtitle}>
                            Selecione uma ou várias bibliotecas.
                            A versão vigente em Produção é utilizada
                            por padrão.
                        </p>
                    </div>


                    <button
                        type="button"
                        onClick={() =>
                            !addingExistingLibraries &&
                            onClose()
                        }
                        style={styles.modalClose}
                        disabled={addingExistingLibraries}
                        aria-label="Fechar"
                    >
                        <X size={16} />
                    </button>

                </div>


                {/* =============================================
                    CONTEÚDO
                ============================================= */}

                <div style={styles.existingLibrariesBody}>

                    {loadingAvailableLibraries ? (

                        <div style={styles.libraryEmptyState}>
                            Carregando bibliotecas publicadas...
                        </div>

                    ) : availableLibraries.length === 0 ? (

                        <div style={styles.libraryEmptyState}>
                            Nenhuma biblioteca publicada está disponível.
                        </div>

                    ) : (

                        <div style={styles.existingLibrariesList}>

                            {availableLibraries.map(
                                (item) => {

                                    const library =
                                        item.library;

                                    const selected =
                                        selectedExistingLibraries.has(
                                            library.id
                                        );

                                    const selectedVersionId =
                                        selectedExistingVersions[
                                            library.id
                                        ];

                                    const selectedVersion =
                                        item.versions.find(
                                            (version) =>
                                                version.id ===
                                                selectedVersionId
                                        );

                                    const usingOldVersion =
                                        selected &&
                                        selectedVersionId !==
                                            item.production_version.id;


                                    return (
                                        <div
                                            key={library.id}
                                            style={{
                                                ...styles.existingLibraryRow,

                                                borderColor:
                                                    selected
                                                        ? "#416ea8"
                                                        : "#353940",

                                                background:
                                                    selected
                                                        ? "#202a37"
                                                        : "#1b1c1f",

                                                opacity:
                                                    item.already_added
                                                        ? 0.58
                                                        : 1,
                                            }}
                                        >

                                            <div
                                                style={
                                                    styles.existingLibraryMain
                                                }
                                            >

                                                <input
                                                    type="checkbox"
                                                    checked={
                                                        selected ||
                                                        item.already_added
                                                    }
                                                    disabled={
                                                        item.already_added ||
                                                        addingExistingLibraries
                                                    }
                                                    onChange={() =>
                                                        onToggleLibrary(
                                                            library.id
                                                        )
                                                    }
                                                    style={
                                                        styles.libraryCheckbox
                                                    }
                                                />


                                                <div
                                                    style={
                                                        styles.existingLibraryInfo
                                                    }
                                                >

                                                    <div
                                                        style={
                                                            styles.existingLibraryNameRow
                                                        }
                                                    >
                                                        <strong>
                                                            {library.name}
                                                        </strong>

                                                        <code>
                                                            {library.import_name}
                                                        </code>

                                                        {item.already_added && (
                                                            <span
                                                                style={
                                                                    styles.libraryAlreadyBadge
                                                                }
                                                            >
                                                                JÁ NO PROJETO
                                                            </span>
                                                        )}
                                                    </div>


                                                    {library.description && (
                                                        <span
                                                            style={
                                                                styles.existingLibraryDescription
                                                            }
                                                        >
                                                            {library.description}
                                                        </span>
                                                    )}

                                                </div>
                                            </div>


                                            <div
                                                style={
                                                    styles.existingLibraryVersionArea
                                                }
                                            >
                                                <label>
                                                    Versão
                                                </label>

                                                <select
                                                    value={
                                                        selectedVersionId || ""
                                                    }
                                                    disabled={
                                                        !selected ||
                                                        item.already_added ||
                                                        addingExistingLibraries
                                                    }
                                                    onChange={(event) =>
                                                        onSelectVersion(
                                                            library.id,
                                                            Number(
                                                                event.target.value
                                                            )
                                                        )
                                                    }
                                                    style={
                                                        styles.libraryVersionSelect
                                                    }
                                                >
                                                    {item.versions.map(
                                                        (version) => (
                                                            <option
                                                                key={version.id}
                                                                value={version.id}
                                                            >
                                                                {version.version}
                                                                {version.is_production
                                                                    ? " • PRODUÇÃO"
                                                                    : " • anterior"}
                                                            </option>
                                                        )
                                                    )}
                                                </select>
                                            </div>


                                            {selected &&
                                                !usingOldVersion && (

                                                <div
                                                    style={
                                                        styles.productionVersionInfo
                                                    }
                                                >
                                                    Produção atual:{" "}

                                                    <strong>
                                                        {
                                                            item.production_version
                                                                .version
                                                        }
                                                    </strong>
                                                </div>
                                            )}


                                            {usingOldVersion && (

                                                <div
                                                    style={
                                                        styles.oldVersionWarning
                                                    }
                                                >
                                                    <strong>
                                                        Atenção:
                                                    </strong>{" "}

                                                    você selecionou uma versão
                                                    anterior.

                                                    <span>
                                                        Produção atual:{" "}
                                                        {
                                                            item.production_version
                                                                .version
                                                        }
                                                        {" · "}
                                                        Selecionada:{" "}
                                                        {
                                                            selectedVersion?.version
                                                        }
                                                    </span>
                                                </div>
                                            )}

                                        </div>
                                    );
                                }
                            )}

                        </div>
                    )}


                    {existingLibraryError && (
                        <div style={styles.modalError}>
                            {existingLibraryError}
                        </div>
                    )}

                </div>


                {/* =============================================
                    RODAPÉ
                ============================================= */}

                <div style={styles.modalFooter}>

                    <div style={styles.librarySelectionCount}>
                        {
                            selectedExistingLibraries.size
                        }{" "}
                        selecionada(s)
                    </div>


                    <button
                        type="button"
                        onClick={onClose}
                        disabled={addingExistingLibraries}
                        style={styles.modalSecondaryButton}
                    >
                        Cancelar
                    </button>


                    <button
                        type="button"
                        onClick={onAddLibraries}
                        disabled={
                            addingExistingLibraries ||
                            selectedExistingLibraries.size === 0
                        }
                        style={{
                            ...styles.modalPrimaryButton,

                            opacity:
                                addingExistingLibraries ||
                                selectedExistingLibraries.size === 0
                                    ? 0.55
                                    : 1,
                        }}
                    >
                        {addingExistingLibraries
                            ? "Adicionando..."
                            : selectedExistingLibraries.size === 1
                                ? "Adicionar biblioteca"
                                : `Adicionar ${selectedExistingLibraries.size} bibliotecas`}
                    </button>

                </div>

            </div>
        </div>
    );
}


export default AddExistingLibrariesModal;
// ============================================================
// TEMPLATE LIBRARIES SELECTOR
// ============================================================
//
// Responsabilidade:
//     Permitir selecionar uma ou várias Libraries e fixar uma
//     LibraryVersion exata para uma AutomationTemplateVersion.
//
// Regras visuais/funcionais:
//     - a versão vigente em Produção é usada por padrão ao marcar
//       uma Library pela primeira vez;
//     - versões anteriores continuam disponíveis como escolha
//       explícita, com indicação visual;
//     - Libraries arquivadas aparecem somente quando já fazem parte
//       da composição recebida, permitindo remover o vínculo;
//     - versões são carregadas sob demanda e mantidas em cache.
// ============================================================

import {
    useEffect,
    useMemo,
    useState,
} from "react";

import {
    AlertTriangle,
    BookOpen,
    LoaderCircle,
    Search,
} from "lucide-react";

import {
    useTemplateLibraryCatalog,
} from "../../hooks/templates/useTemplateLibraryCatalog";

import type {
    TemplateLibrarySelection,
} from "../../types/development";

import type {
    LibraryCatalogItem,
    LibraryVersionItem,
} from "../libraries/types/libraries";


// ============================================================
// PROPS
// ============================================================

interface TemplateLibrariesSelectorProps {
    value: TemplateLibrarySelection[];

    onChange: (
        next: TemplateLibrarySelection[],
    ) => void;

    disabled?: boolean;

    onValidationChange?: (
        isValid: boolean,
    ) => void;

    title?: string;
    description?: string;
}


// ============================================================
// AUXILIARES
// ============================================================

function findSelection(
    value: TemplateLibrarySelection[],
    libraryId: number,
): TemplateLibrarySelection | undefined {
    return value.find(
        (item) => item.library_id === libraryId
    );
}


function findSelectedVersion(
    versions: LibraryVersionItem[],
    selection: TemplateLibrarySelection | undefined,
): LibraryVersionItem | undefined {
    if (!selection) {
        return undefined;
    }

    return versions.find(
        (version) =>
            version.id === selection.library_version_id
    );
}


// ============================================================
// COMPONENTE
// ============================================================

export function TemplateLibrariesSelector({
    value,
    onChange,
    disabled = false,
    onValidationChange,
    title = "Libraries do Template",
    description = "Selecione dependências reutilizáveis e fixe a versão que fará parte deste snapshot.",
}: TemplateLibrariesSelectorProps) {

    const {
        libraries,
        loadingCatalog,
        catalogError,
        versionsByLibraryId,
        isLoadingVersions,
        loadVersions,
    } = useTemplateLibraryCatalog();

    const [search, setSearch] =
        useState("");

    const [selectionError, setSelectionError] =
        useState("");


    // ========================================================
    // GARANTE DADOS DAS LIBRARIES JÁ SELECIONADAS
    // ========================================================

    useEffect(() => {
        for (const selection of value) {
            if (!versionsByLibraryId[selection.library_id]) {
                void loadVersions(
                    selection.library_id
                ).catch(() => {
                    // O erro de carregamento é mostrado na própria linha
                    // quando o usuário interagir. O vínculo exato recebido
                    // continua preservado no estado do formulário.
                });
            }
        }
    }, [
        loadVersions,
        value,
        versionsByLibraryId,
    ]);


    // ========================================================
    // FILTRO
    // ========================================================

    const visibleLibraries = useMemo(() => {
        const normalizedSearch =
            search.trim().toLocaleLowerCase("pt-BR");

        const selectedLibraryIds =
            new Set(
                value.map(
                    (item) => item.library_id
                )
            );

        return libraries.filter((library) => {
            // Library arquivada só aparece quando já está selecionada.
            if (
                !library.is_active &&
                !selectedLibraryIds.has(library.id)
            ) {
                return false;
            }

            if (!normalizedSearch) {
                return true;
            }

            return (
                library.name
                    .toLocaleLowerCase("pt-BR")
                    .includes(normalizedSearch) ||
                library.import_name
                    .toLocaleLowerCase("pt-BR")
                    .includes(normalizedSearch)
            );
        });
    }, [
        libraries,
        search,
        value,
    ]);


    // ========================================================
    // VALIDAÇÃO DA COMPOSIÇÃO
    // ========================================================

    const selectionIsValid = useMemo(() => {
        if (value.length === 0) {
            return true;
        }

        if (loadingCatalog || catalogError) {
            return false;
        }

        for (const selection of value) {
            const library = libraries.find(
                (item) => item.id === selection.library_id
            );

            if (!library || !library.is_active) {
                return false;
            }

            const versions =
                versionsByLibraryId[selection.library_id];

            if (!versions) {
                return false;
            }

            const selectedVersion =
                versions.find(
                    (version) =>
                        version.id === selection.library_version_id
                );

            if (!selectedVersion || !selectedVersion.is_active) {
                return false;
            }
        }

        return true;
    }, [
        catalogError,
        libraries,
        loadingCatalog,
        value,
        versionsByLibraryId,
    ]);


    useEffect(() => {
        onValidationChange?.(
            selectionIsValid
        );
    }, [
        onValidationChange,
        selectionIsValid,
    ]);


    // ========================================================
    // SELEÇÃO / REMOÇÃO
    // ========================================================

    const toggleLibrary = async (
        library: LibraryCatalogItem,
    ) => {
        if (disabled) {
            return;
        }

        setSelectionError("");

        const current =
            findSelection(
                value,
                library.id,
            );

        if (current) {
            onChange(
                value.filter(
                    (item) =>
                        item.library_id !== library.id
                )
            );
            return;
        }

        if (!library.is_active) {
            setSelectionError(
                `A Library "${library.name}" está arquivada e não pode ser adicionada a uma nova versão.`
            );
            return;
        }

        try {
            const versions =
                await loadVersions(library.id);

            const productionVersion =
                versions.find(
                    (version) =>
                        version.is_active &&
                        version.is_production
                );

            if (!productionVersion) {
                setSelectionError(
                    `A Library "${library.name}" não possui uma versão ativa marcada como Produção.`
                );
                return;
            }

            onChange([
                ...value,
                {
                    library_id:
                        library.id,
                    library_version_id:
                        productionVersion.id,
                },
            ]);

        } catch {
            setSelectionError(
                `Não foi possível carregar as versões de "${library.name}".`
            );
        }
    };


    // ========================================================
    // TROCA EXPLÍCITA DE VERSÃO
    // ========================================================

    const changeVersion = (
        libraryId: number,
        versionId: number,
    ) => {
        if (disabled) {
            return;
        }

        setSelectionError("");

        onChange(
            value.map((item) =>
                item.library_id === libraryId
                    ? {
                          ...item,
                          library_version_id:
                              versionId,
                      }
                    : item
            )
        );
    };


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <section className="template-libraries-selector">
            <div className="template-libraries-selector__header">
                <div>
                    <div className="template-libraries-selector__title-row">
                        <BookOpen size={16} aria-hidden="true" />
                        <strong>{title}</strong>
                    </div>

                    <p>{description}</p>
                </div>

                <span className="template-libraries-selector__count">
                    {value.length} selecionada(s)
                </span>
            </div>

            <label className="template-libraries-search">
                <Search size={15} aria-hidden="true" />
                <input
                    type="search"
                    value={search}
                    disabled={disabled || loadingCatalog}
                    placeholder="Buscar por nome ou import..."
                    onChange={(event) =>
                        setSearch(event.target.value)
                    }
                />
            </label>

            {(
                catalogError ||
                selectionError ||
                (!selectionIsValid && value.length > 0 && !loadingCatalog)
            ) && (
                <div
                    className="template-libraries-selector__warning"
                    role="alert"
                >
                    <AlertTriangle size={15} aria-hidden="true" />
                    <span>
                        {
                            selectionError ||
                            catalogError ||
                            "A composição possui uma Library ou versão indisponível. Remova o vínculo ou selecione uma versão ativa antes de publicar."
                        }
                    </span>
                </div>
            )}

            <div className="template-libraries-selector__list">
                {loadingCatalog ? (
                    <div className="template-libraries-selector__state">
                        <LoaderCircle
                            className="template-libraries-spinner"
                            size={17}
                            aria-hidden="true"
                        />
                        Carregando catálogo de Libraries...
                    </div>
                ) : visibleLibraries.length === 0 ? (
                    <div className="template-libraries-selector__state">
                        Nenhuma Library encontrada.
                    </div>
                ) : (
                    visibleLibraries.map((library) => {
                        const selection =
                            findSelection(
                                value,
                                library.id,
                            );

                        const selected =
                            Boolean(selection);

                        const versions =
                            versionsByLibraryId[
                                library.id
                            ] || [];

                        const selectedVersion =
                            findSelectedVersion(
                                versions,
                                selection,
                            );

                        const loadingVersions =
                            isLoadingVersions(
                                library.id
                            );

                        return (
                            <div
                                className={`template-library-row${
                                    selected
                                        ? " template-library-row--selected"
                                        : ""
                                }`}
                                key={library.id}
                            >
                                <label className="template-library-row__identity">
                                    <input
                                        type="checkbox"
                                        checked={selected}
                                        disabled={
                                            disabled ||
                                            loadingVersions ||
                                            (!library.is_active && !selected)
                                        }
                                        onChange={() =>
                                            void toggleLibrary(
                                                library
                                            )
                                        }
                                    />

                                    <span>
                                        <strong>
                                            {library.name}
                                        </strong>
                                        <code>
                                            {library.import_name}
                                        </code>
                                    </span>
                                </label>

                                {selected && (
                                    <div className="template-library-row__version">
                                        {loadingVersions && versions.length === 0 ? (
                                            <span className="template-library-row__loading">
                                                <LoaderCircle
                                                    className="template-libraries-spinner"
                                                    size={14}
                                                    aria-hidden="true"
                                                />
                                                Carregando versões
                                            </span>
                                        ) : (
                                            <>
                                                <select
                                                    value={
                                                        selection?.library_version_id ?? ""
                                                    }
                                                    disabled={
                                                        disabled ||
                                                        loadingVersions
                                                    }
                                                    aria-label={`Versão da Library ${library.name}`}
                                                    onChange={(event) =>
                                                        changeVersion(
                                                            library.id,
                                                            Number(event.target.value),
                                                        )
                                                    }
                                                >
                                                    {versions.map((version) => (
                                                        <option
                                                            key={version.id}
                                                            value={version.id}
                                                            disabled={!version.is_active}
                                                        >
                                                            {version.version}
                                                            {version.is_production
                                                                ? " · Produção"
                                                                : version.is_active
                                                                    ? " · Versão anterior"
                                                                    : " · Inativa"}
                                                        </option>
                                                    ))}

                                                    {selection && !selectedVersion && (
                                                        <option
                                                            value={selection.library_version_id}
                                                        >
                                                            Versão #{selection.library_version_id}
                                                        </option>
                                                    )}
                                                </select>

                                                {selectedVersion?.is_production ? (
                                                    <span className="template-library-version-status template-library-version-status--production">
                                                        Produção
                                                    </span>
                                                ) : selectedVersion?.is_active ? (
                                                    <span className="template-library-version-status template-library-version-status--previous">
                                                        Versão anterior
                                                    </span>
                                                ) : selectedVersion ? (
                                                    <span className="template-library-version-status template-library-version-status--inactive">
                                                        Inativa
                                                    </span>
                                                ) : null}
                                            </>
                                        )}
                                    </div>
                                )}
                            </div>
                        );
                    })
                )}
            </div>
        </section>
    );
}

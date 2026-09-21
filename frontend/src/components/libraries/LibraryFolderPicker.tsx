import { useEffect, useMemo, useState } from "react";
import {
    BookOpen,
    Check,
    ChevronDown,
    ChevronRight,
    Folder,
    Search,
    X,
} from "lucide-react";

// ============================================================
// TIPO - PASTA UTILIZADA PELO SELETOR
// ============================================================

// Este tipo é propositalmente simples e independente do backend.
// O componente pai transforma a árvore de Bibliotecas neste formato.
export interface LibraryFolderOption {
    id: number;
    name: string;
    parent_id: number | null;
    children: LibraryFolderOption[];
}

// ============================================================
// PROPRIEDADES DO SELETOR
// ============================================================

interface LibraryFolderPickerProps {
    open: boolean;
    title: string;
    description?: string;
    folders: LibraryFolderOption[];
    selectedFolderId: number | null;
    disabledFolderIds?: Set<number>;
    confirmLabel?: string;
    busy?: boolean;
    onChange: (folderId: number | null) => void;
    onCancel: () => void;
    onConfirm: () => void;
}

// ============================================================
// FUNÇÕES AUXILIARES
// ============================================================

// Filtra a árvore sem perder os ancestrais do resultado.
// Dessa forma, uma pasta profunda continua aparecendo no contexto certo.
function filtrarPastas(
    folders: LibraryFolderOption[],
    searchValue: string
): LibraryFolderOption[] {
    const termo = searchValue.trim().toLocaleLowerCase("pt-BR");

    if (!termo) {
        return folders;
    }

    const resultado: LibraryFolderOption[] = [];

    for (const folder of folders) {
        const children = filtrarPastas(folder.children, searchValue);
        const combina = folder.name
            .toLocaleLowerCase("pt-BR")
            .includes(termo);

        if (combina || children.length > 0) {
            resultado.push({
                ...folder,
                // Quando a própria pasta combina com a busca, mantém a
                // subárvore completa. Caso contrário, mostra só matches.
                children: combina ? folder.children : children,
            });
        }
    }

    return resultado;
}

// Localiza o caminho visual de uma pasta.
// Exemplo: Bibliotecas / Corporativo / Financeiro.
function encontrarCaminho(
    folders: LibraryFolderOption[],
    folderId: number,
    caminhoAtual: string[] = []
): string[] | null {
    for (const folder of folders) {
        const caminho = [...caminhoAtual, folder.name];

        if (folder.id === folderId) {
            return caminho;
        }

        const encontrado = encontrarCaminho(
            folder.children,
            folderId,
            caminho
        );

        if (encontrado) {
            return encontrado;
        }
    }

    return null;
}

// Retorna os IDs das pastas de primeiro nível.
// Eles são abertos automaticamente quando o seletor aparece.
function obterIdsRaiz(
    folders: LibraryFolderOption[]
): Set<number> {
    return new Set(folders.map((folder) => folder.id));
}

// ============================================================
// COMPONENTE
// ============================================================

function LibraryFolderPicker({
    open,
    title,
    description,
    folders,
    selectedFolderId,
    disabledFolderIds = new Set<number>(),
    confirmLabel = "Selecionar",
    busy = false,
    onChange,
    onCancel,
    onConfirm,
}: LibraryFolderPickerProps) {
    // Texto de busca local do seletor.
    const [search, setSearch] = useState("");

    // Guarda quais pastas estão abertas somente dentro deste modal.
    const [expandedFolders, setExpandedFolders] =
        useState<Set<number>>(new Set());

    // Sempre que o modal abrir, limpa a busca e abre as pastas raiz.
    useEffect(() => {
        if (!open) {
            return;
        }

        setSearch("");
        setExpandedFolders(obterIdsRaiz(folders));
    }, [open, folders]);

    const visibleFolders = useMemo(
        () => filtrarPastas(folders, search),
        [folders, search]
    );

    const selectedPath = useMemo(() => {
        if (selectedFolderId === null) {
            return ["Bibliotecas"];
        }

        return [
            "Bibliotecas",
            ...(encontrarCaminho(folders, selectedFolderId) || []),
        ];
    }, [folders, selectedFolderId]);

    if (!open) {
        return null;
    }

    const alternarPasta = (
        folderId: number
    ) => {
        setExpandedFolders((atual) => {
            const novo = new Set(atual);

            if (novo.has(folderId)) {
                novo.delete(folderId);
            } else {
                novo.add(folderId);
            }

            return novo;
        });
    };

    const renderFolder = (
        folder: LibraryFolderOption,
        level: number = 0
    ): React.ReactNode => {
        const hasChildren = folder.children.length > 0;
        const forceExpanded = Boolean(search.trim());
        const expanded = forceExpanded || expandedFolders.has(folder.id);
        const disabled = disabledFolderIds.has(folder.id);
        const selected = selectedFolderId === folder.id;

        return (
            <div
                key={folder.id}
                className="library-picker-node"
            >
                <div
                    className={`library-picker-row ${
                        selected
                            ? "library-picker-row-selected"
                            : ""
                    } ${
                        disabled
                            ? "library-picker-row-disabled"
                            : ""
                    }`}
                    style={{
                        paddingLeft: `${12 + level * 22}px`,
                    }}
                >
                    {hasChildren ? (
                        <button
                            type="button"
                            className="library-picker-expand"
                            disabled={busy}
                            onClick={() => alternarPasta(folder.id)}
                            aria-label={
                                expanded
                                    ? `Recolher ${folder.name}`
                                    : `Expandir ${folder.name}`
                            }
                        >
                            {expanded ? (
                                <ChevronDown size={15} />
                            ) : (
                                <ChevronRight size={15} />
                            )}
                        </button>
                    ) : (
                        <span className="library-picker-expand-placeholder" />
                    )}

                    <button
                        type="button"
                        className="library-picker-select"
                        disabled={disabled || busy}
                        onClick={() => onChange(folder.id)}
                    >
                        <Folder
                            size={16}
                            strokeWidth={1.8}
                        />

                        <span>{folder.name}</span>

                        {disabled && (
                            <small>destino inválido</small>
                        )}

                        {selected && !disabled && (
                            <Check
                                className="library-picker-check"
                                size={15}
                                strokeWidth={2}
                            />
                        )}
                    </button>
                </div>

                {expanded && hasChildren && (
                    <div className="library-picker-children">
                        {folder.children.map((child) =>
                            renderFolder(child, level + 1)
                        )}
                    </div>
                )}
            </div>
        );
    };

    return (
        <div
            className="library-picker-backdrop"
            role="presentation"
            onMouseDown={(event) => {
                if (
                    !busy &&
                    event.target === event.currentTarget
                ) {
                    onCancel();
                }
            }}
        >
            <div
                className="library-picker-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="library-folder-picker-title"
            >
                <div className="library-picker-header">
                    <div>
                        <div className="library-picker-eyebrow">
                            ORGANIZAÇÃO
                        </div>

                        <h3 id="library-folder-picker-title">
                            {title}
                        </h3>

                        {description && (
                            <p>{description}</p>
                        )}
                    </div>

                    <button
                        type="button"
                        className="library-picker-close"
                        disabled={busy}
                        onClick={onCancel}
                        aria-label="Fechar seletor de pasta"
                    >
                        <X size={18} />
                    </button>
                </div>

                <div className="library-picker-body">
                    <div className="library-picker-current-path">
                        <span>Destino selecionado</span>
                        <strong>
                            {selectedPath.join(" / ")}
                        </strong>
                    </div>

                    <div className="library-picker-search">
                        <Search
                            size={15}
                            strokeWidth={1.8}
                        />

                        <input
                            type="search"
                            value={search}
                            placeholder="Buscar pasta..."
                            disabled={busy}
                            onChange={(event) =>
                                setSearch(event.target.value)
                            }
                            aria-label="Buscar pasta"
                        />

                        {search && (
                            <button
                                type="button"
                                disabled={busy}
                                onClick={() => setSearch("")}
                                aria-label="Limpar busca"
                            >
                                <X size={14} />
                            </button>
                        )}
                    </div>

                    <div className="library-picker-tree">
                        <div
                            className={`library-picker-row library-picker-root-row ${
                                selectedFolderId === null
                                    ? "library-picker-row-selected"
                                    : ""
                            }`}
                        >
                            <span className="library-picker-expand-placeholder" />

                            <button
                                type="button"
                                className="library-picker-select"
                                disabled={busy}
                                onClick={() => onChange(null)}
                            >
                                <BookOpen
                                    size={16}
                                    strokeWidth={1.8}
                                />

                                <span>Bibliotecas</span>
                                <small>Raiz</small>

                                {selectedFolderId === null && (
                                    <Check
                                        className="library-picker-check"
                                        size={15}
                                        strokeWidth={2}
                                    />
                                )}
                            </button>
                        </div>

                        {visibleFolders.length === 0 ? (
                            <div className="library-picker-empty">
                                Nenhuma pasta encontrada.
                            </div>
                        ) : (
                            visibleFolders.map((folder) =>
                                renderFolder(folder)
                            )
                        )}
                    </div>
                </div>

                <div className="library-picker-footer">
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
                        disabled={busy}
                        onClick={onConfirm}
                    >
                        {busy ? "Salvando..." : confirmLabel}
                    </button>
                </div>
            </div>
        </div>
    );
}

export default LibraryFolderPicker;

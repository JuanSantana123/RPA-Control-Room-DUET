import {
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";
import {
    FileArchive,
    Move,
    Upload,
    X,
} from "lucide-react";

import LibraryFolderPicker from "./LibraryFolderPicker";

import type {
    LibraryFolderOption,
} from "./LibraryFolderPicker";

import "./ImportLibraryModal.css";


export interface ImportLibraryPayload {
    name: string;
    importName: string;
    description: string;
    version: string;
    folderId: number | null;
    file: File;
}


interface ImportLibraryModalProps {
    open: boolean;
    folders: LibraryFolderOption[];
    initialFolderId?: number | null;
    busy?: boolean;
    error?: string;
    onCancel: () => void;
    onImport: (
        payload: ImportLibraryPayload
    ) => void | Promise<void>;
}


// ============================================================
// FUNÇÕES AUXILIARES
// ============================================================

function normalizarImportName(
    fileName: string
): string {
    /*
     * Usa o nome do ZIP somente como sugestão inicial.
     *
     * Exemplo:
     *
     *     logging_core.zip
     *         -> logging_core
     *
     * A validação definitiva continua sendo feita pelo backend.
     */
    let value = fileName
        .replace(/\.zip$/i, "")
        .trim()
        .replace(/[^A-Za-z0-9_]/g, "_")
        .replace(/_+/g, "_");

    if (/^\d/.test(value)) {
        value = `lib_${value}`;
    }

    return value;
}


function nomeAmigavel(
    importName: string
): string {
    /*
     * Converte:
     *
     *     logging_core
     *
     * em:
     *
     *     Logging Core
     */
    return importName
        .split("_")
        .filter(Boolean)
        .map(
            (part) =>
                part.charAt(0).toUpperCase() +
                part.slice(1)
        )
        .join(" ");
}


function formatarTamanhoArquivo(
    bytes: number
): string {
    /*
     * Mantém a informação de tamanho compacta dentro do modal.
     */
    if (bytes < 1024) {
        return `${bytes} B`;
    }

    const kb = bytes / 1024;

    if (kb < 1024) {
        return `${kb.toFixed(1)} KB`;
    }

    const mb = kb / 1024;

    return `${mb.toFixed(1)} MB`;
}


function encontrarCaminhoPasta(
    folders: LibraryFolderOption[],
    folderId: number | null,
    prefix: string[] = []
): string[] | null {
    /*
     * Resolve o breadcrumb amigável da pasta escolhida.
     *
     * Isso evita exibir algo pouco profissional como:
     *
     *     Pasta #15
     *
     * e passa a exibir:
     *
     *     Bibliotecas / Core / Utilitários
     */
    if (folderId === null) {
        return [];
    }

    for (const folder of folders) {
        const currentPath = [
            ...prefix,
            folder.name,
        ];

        if (folder.id === folderId) {
            return currentPath;
        }

        const childPath =
            encontrarCaminhoPasta(
                folder.children || [],
                folderId,
                currentPath
            );

        if (childPath) {
            return childPath;
        }
    }

    return null;
}


// ============================================================
// COMPONENTE
// ============================================================

function ImportLibraryModal({
    open,
    folders,
    initialFolderId = null,
    busy = false,
    error = "",
    onCancel,
    onImport,
}: ImportLibraryModalProps) {
    const fileInputRef =
        useRef<HTMLInputElement | null>(null);

    const [name, setName] =
        useState("");

    const [importName, setImportName] =
        useState("");

    const [description, setDescription] =
        useState("");

    const [version, setVersion] =
        useState("1.0.0");

    const [folderId, setFolderId] =
        useState<number | null>(
            initialFolderId
        );

    const [file, setFile] =
        useState<File | null>(null);

    const [folderPickerOpen, setFolderPickerOpen] =
        useState(false);

    const [localError, setLocalError] =
        useState("");

    const [dragActive, setDragActive] =
        useState(false);


    // ========================================================
    // LOCAL ATUAL
    // ========================================================

    const folderPath = useMemo(
        () =>
            encontrarCaminhoPasta(
                folders,
                folderId
            ),
        [
            folders,
            folderId,
        ]
    );

    const destinationLabel =
        folderId === null
            ? "Bibliotecas"
            : [
                "Bibliotecas",
                ...(folderPath || []),
            ].join(" / ");


    // ========================================================
    // RESET
    // ========================================================

    useEffect(() => {
        if (!open) {
            return;
        }

        setName("");
        setImportName("");
        setDescription("");
        setVersion("1.0.0");
        setFolderId(
            initialFolderId ?? null
        );
        setFile(null);
        setLocalError("");
        setFolderPickerOpen(false);
        setDragActive(false);

        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }

    }, [
        open,
        initialFolderId,
    ]);


    if (!open) {
        return null;
    }


    // ========================================================
    // ARQUIVO
    // ========================================================

    const selecionarArquivo = (
        selectedFile: File | null
    ) => {
        setLocalError("");
        setDragActive(false);

        if (!selectedFile) {
            setFile(null);
            return;
        }

        if (
            !selectedFile.name
                .toLowerCase()
                .endsWith(".zip")
        ) {
            setFile(null);

            setLocalError(
                "Selecione um arquivo ZIP válido."
            );

            return;
        }

        setFile(
            selectedFile
        );

        /*
         * Preenche os metadados somente quando o usuário
         * ainda não digitou valores manualmente.
         */
        const suggestedImportName =
            normalizarImportName(
                selectedFile.name
            );

        if (!importName.trim()) {
            setImportName(
                suggestedImportName
            );
        }

        if (!name.trim()) {
            setName(
                nomeAmigavel(
                    suggestedImportName
                )
            );
        }
    };


    const removerArquivo = () => {
        if (busy) {
            return;
        }

        setFile(null);
        setLocalError("");

        if (fileInputRef.current) {
            fileInputRef.current.value = "";
        }
    };


    // ========================================================
    // SUBMIT
    // ========================================================

    const submit = async () => {
        setLocalError("");

        if (!file) {
            setLocalError(
                "Selecione o ZIP da biblioteca."
            );
            return;
        }

        if (!name.trim()) {
            setLocalError(
                "Informe o nome da biblioteca."
            );
            return;
        }

        if (!importName.trim()) {
            setLocalError(
                "Informe o import_name."
            );
            return;
        }

        if (!version.trim()) {
            setLocalError(
                "Informe a versão inicial."
            );
            return;
        }

        await onImport({
            name: name.trim(),
            importName: importName.trim(),
            description:
                description.trim(),
            version: version.trim(),
            folderId,
            file,
        });
    };


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <>
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
                    className="library-modal library-modal-large library-import-modal"
                    role="dialog"
                    aria-modal="true"
                    aria-labelledby="library-import-title"
                    onClick={(event) =>
                        event.stopPropagation()
                    }
                >
                    {/* ==================================================
                        HEADER
                       ================================================== */}

                    <div className="library-modal-header">
                        <div>
                            <div className="library-modal-eyebrow">
                                CATÁLOGO GLOBAL
                            </div>

                            <h3 id="library-import-title">
                                Importar biblioteca
                            </h3>

                            <p>
                                Adicione uma biblioteca Python já pronta
                                ao catálogo do DUET e publique sua primeira
                                versão sem criar uma Automação.
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


                    {/* ==================================================
                        BODY
                       ================================================== */}

                    <div className="library-modal-body">
                        {(localError || error) && (
                            <div className="library-inline-alert library-inline-alert-error">
                                <span>
                                    {localError || error}
                                </span>
                            </div>
                        )}


                        {/* ----------------------------------------------
                            PACOTE ZIP
                           ---------------------------------------------- */}

                        <div className="library-modal-field">
                            <div className="library-modal-field-heading">
                                <label>
                                    Pacote da biblioteca
                                </label>

                                <span>
                                    Arquivo .zip
                                </span>
                            </div>

                            <input
                                ref={fileInputRef}
                                className="library-import-file-input"
                                type="file"
                                accept=".zip,application/zip"
                                disabled={busy}
                                onChange={(event) =>
                                    selecionarArquivo(
                                        event.target.files?.[0] ||
                                        null
                                    )
                                }
                            />

                            {!file ? (
                                <button
                                    type="button"
                                    className={`library-import-dropzone ${
                                        dragActive
                                            ? "library-import-dropzone-active"
                                            : ""
                                    }`}
                                    disabled={busy}
                                    onClick={() =>
                                        fileInputRef.current?.click()
                                    }
                                    onDragEnter={(event) => {
                                        event.preventDefault();
                                        event.stopPropagation();
                                        setDragActive(true);
                                    }}
                                    onDragOver={(event) => {
                                        event.preventDefault();
                                        event.stopPropagation();
                                        setDragActive(true);
                                    }}
                                    onDragLeave={(event) => {
                                        event.preventDefault();
                                        event.stopPropagation();
                                        setDragActive(false);
                                    }}
                                    onDrop={(event) => {
                                        event.preventDefault();
                                        event.stopPropagation();

                                        selecionarArquivo(
                                            event.dataTransfer.files?.[0] ||
                                            null
                                        );
                                    }}
                                >
                                    <span className="library-import-dropzone-icon">
                                        <Upload
                                            size={19}
                                            strokeWidth={1.8}
                                        />
                                    </span>

                                    <span className="library-import-dropzone-copy">
                                        <strong>
                                            Selecione ou arraste o ZIP
                                        </strong>

                                        <small>
                                            O pacote deve conter a pasta do
                                            import_name e um __init__.py.
                                        </small>
                                    </span>

                                    <span className="library-import-dropzone-action">
                                        Procurar arquivo
                                    </span>
                                </button>
                            ) : (
                                <div className="library-import-file-card">
                                    <span className="library-import-file-icon">
                                        <FileArchive
                                            size={19}
                                            strokeWidth={1.8}
                                        />
                                    </span>

                                    <div className="library-import-file-info">
                                        <strong>
                                            {file.name}
                                        </strong>

                                        <small>
                                            {formatarTamanhoArquivo(
                                                file.size
                                            )}
                                            {" · "}
                                            Pacote ZIP selecionado
                                        </small>
                                    </div>

                                    <button
                                        type="button"
                                        className="library-import-file-remove"
                                        disabled={busy}
                                        onClick={removerArquivo}
                                        aria-label="Remover arquivo selecionado"
                                        title="Remover arquivo"
                                    >
                                        <X size={15} />
                                    </button>
                                </div>
                            )}
                        </div>


                        {/* ----------------------------------------------
                            IDENTIDADE
                           ---------------------------------------------- */}

                        <div className="library-import-section">
                            <div className="library-import-section-heading">
                                <span>Identidade</span>

                                <small>
                                    Como a biblioteca aparecerá no catálogo
                                </small>
                            </div>

                            <div className="library-modal-grid">
                                <div className="library-modal-field">
                                    <label htmlFor="library-import-name">
                                        Nome
                                    </label>

                                    <input
                                        id="library-import-name"
                                        type="text"
                                        value={name}
                                        placeholder="Ex.: Logging Core"
                                        disabled={busy}
                                        onChange={(event) =>
                                            setName(
                                                event.target.value
                                            )
                                        }
                                    />
                                </div>

                                <div className="library-modal-field">
                                    <label htmlFor="library-import-import-name">
                                        import_name
                                    </label>

                                    <input
                                        id="library-import-import-name"
                                        type="text"
                                        value={importName}
                                        placeholder="Ex.: logging_core"
                                        disabled={busy}
                                        onChange={(event) =>
                                            setImportName(
                                                event.target.value
                                            )
                                        }
                                    />

                                    <small>
                                        Namespace utilizado nos imports Python.
                                    </small>
                                </div>
                            </div>
                        </div>


                        {/* ----------------------------------------------
                            PUBLICAÇÃO
                           ---------------------------------------------- */}

                        <div className="library-import-section">
                            <div className="library-import-section-heading">
                                <span>Publicação inicial</span>

                                <small>
                                    A primeira versão será marcada como Produção
                                </small>
                            </div>

                            <div className="library-modal-grid">
                                <div className="library-modal-field">
                                    <label htmlFor="library-import-version">
                                        Versão
                                    </label>

                                    <input
                                        id="library-import-version"
                                        type="text"
                                        value={version}
                                        placeholder="1.0.0"
                                        disabled={busy}
                                        onChange={(event) =>
                                            setVersion(
                                                event.target.value
                                            )
                                        }
                                    />

                                    <small>
                                        Utilize versionamento semântico.
                                    </small>
                                </div>

                                <div className="library-modal-field">
                                    <label>
                                        Local no catálogo
                                    </label>

                                    <div className="library-import-location">
                                        <div className="library-import-location-copy">
                                            <span>
                                                Destino
                                            </span>

                                            <strong title={destinationLabel}>
                                                {destinationLabel}
                                            </strong>
                                        </div>

                                        <button
                                            type="button"
                                            className="library-import-location-button"
                                            disabled={busy}
                                            onClick={() =>
                                                setFolderPickerOpen(true)
                                            }
                                        >
                                            <Move size={14} />
                                            Alterar
                                        </button>
                                    </div>
                                </div>
                            </div>
                        </div>


                        {/* ----------------------------------------------
                            DESCRIÇÃO
                           ---------------------------------------------- */}

                        <div className="library-modal-field">
                            <label htmlFor="library-import-description">
                                Descrição
                            </label>

                            <textarea
                                id="library-import-description"
                                rows={3}
                                value={description}
                                placeholder="Explique a finalidade desta biblioteca..."
                                disabled={busy}
                                onChange={(event) =>
                                    setDescription(
                                        event.target.value
                                    )
                                }
                            />
                        </div>
                    </div>


                    {/* ==================================================
                        FOOTER
                       ================================================== */}

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
                                !file ||
                                !name.trim() ||
                                !importName.trim() ||
                                !version.trim()
                            }
                            onClick={() =>
                                void submit()
                            }
                        >
                            <Upload
                                size={15}
                                strokeWidth={1.9}
                            />

                            {busy
                                ? "Importando..."
                                : "Importar biblioteca"}
                        </button>
                    </div>
                </div>
            </div>


            {/* ======================================================
                SELETOR DE PASTA
               ====================================================== */}

            <LibraryFolderPicker
                open={folderPickerOpen}
                title="Escolha onde importar a biblioteca"
                description="O local organiza a biblioteca no catálogo e não altera o namespace Python."
                folders={folders}
                selectedFolderId={folderId}
                disabledFolderIds={new Set<number>()}
                busy={busy}
                confirmLabel="Selecionar"
                onChange={setFolderId}
                onCancel={() =>
                    setFolderPickerOpen(false)
                }
                onConfirm={() =>
                    setFolderPickerOpen(false)
                }
            />
        </>
    );
}


export default ImportLibraryModal;

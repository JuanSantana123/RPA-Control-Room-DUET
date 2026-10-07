// ============================================================
// DUET CORE - DEVELOPMENT LIBRARY IMPORT MODAL
// ============================================================
//
// Responsabilidade:
// - coletar o ZIP e os metadados da Library;
// - validar somente requisitos básicos da interface;
// - delegar a importação real ao hook do Robot Studio.
//
// Este componente NÃO:
// - chama API diretamente;
// - conhece projectId;
// - cria LibraryVersion;
// - conhece regras de banco;
// - publica em Produção.
//
// Toda regra de negócio permanece no backend.
// ============================================================


import {
    useEffect,
    useRef,
    useState,
} from "react";

import {
    FileArchive,
    Upload,
    X,
} from "lucide-react";

import "./DevelopmentLibraryImportModal.css";


// ============================================================
// PAYLOAD
// ============================================================

export interface DevelopmentLibraryImportPayload {
    name: string;
    importName: string;
    description: string;
    file: File;
}


// ============================================================
// PROPS
// ============================================================

interface DevelopmentLibraryImportModalProps {
    open: boolean;
    busy: boolean;
    error: string;

    onCancel: () => void;

    onImport: (
        payload: DevelopmentLibraryImportPayload
    ) => Promise<void>;

    suggestImportName: (
        value: string
    ) => string;
}


// ============================================================
// HELPERS
// ============================================================

function removerExtensaoZip(
    filename: string
): string {

    return filename.replace(
        /\.zip$/i,
        ""
    );
}


function nomeAmigavel(
    importName: string
): string {

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


function formatarTamanho(
    bytes: number
): string {

    if (bytes < 1024) {
        return `${bytes} B`;
    }

    const kb =
        bytes / 1024;

    if (kb < 1024) {
        return `${kb.toFixed(1)} KB`;
    }

    const mb =
        kb / 1024;

    return `${mb.toFixed(1)} MB`;
}


// ============================================================
// COMPONENTE
// ============================================================

function DevelopmentLibraryImportModal({
    open,
    busy,
    error,
    onCancel,
    onImport,
    suggestImportName,
}: DevelopmentLibraryImportModalProps) {

    const fileInputRef =
        useRef<HTMLInputElement | null>(
            null
        );


    // ========================================================
    // FORMULÁRIO
    // ========================================================

    const [
        file,
        setFile,
    ] =
        useState<File | null>(
            null
        );


    const [
        name,
        setName,
    ] =
        useState("");


    const [
        importName,
        setImportName,
    ] =
        useState("");


    const [
        description,
        setDescription,
    ] =
        useState("");


    const [
        importNameTouched,
        setImportNameTouched,
    ] =
        useState(false);


    const [
        localError,
        setLocalError,
    ] =
        useState("");


    const [
        dragActive,
        setDragActive,
    ] =
        useState(false);


    // ========================================================
    // RESET AO ABRIR
    // ========================================================

    useEffect(
        () => {

            if (!open) {
                return;
            }

            setFile(
                null
            );

            setName(
                ""
            );

            setImportName(
                ""
            );

            setDescription(
                ""
            );

            setImportNameTouched(
                false
            );

            setLocalError(
                ""
            );

            setDragActive(
                false
            );

            if (
                fileInputRef.current
            ) {

                fileInputRef.current.value =
                    "";
            }
        },
        [
            open,
        ]
    );


    // ========================================================
    // ARQUIVO
    // ========================================================

    const selecionarArquivo =
        (
            selectedFile:
                File | null
        ) => {

            setLocalError(
                ""
            );

            setDragActive(
                false
            );


            if (
                !selectedFile
            ) {

                setFile(
                    null
                );

                return;
            }


            if (
                !selectedFile.name
                    .toLowerCase()
                    .endsWith(".zip")
            ) {

                setFile(
                    null
                );

                setLocalError(
                    "Selecione um arquivo ZIP válido."
                );

                return;
            }


            // A validação definitiva de tamanho continua
            // sendo responsabilidade do backend.
            setFile(
                selectedFile
            );


            const filenameWithoutExtension =
                removerExtensaoZip(
                    selectedFile.name
                );


            const suggestedImportName =
                suggestImportName(
                    filenameWithoutExtension
                );


            if (
                !importNameTouched &&
                !importName.trim()
            ) {

                setImportName(
                    suggestedImportName
                );
            }


            if (
                !name.trim()
            ) {

                setName(
                    nomeAmigavel(
                        suggestedImportName
                    )
                );
            }
        };


    // ========================================================
    // CANCELAR
    // ========================================================

    const cancelar =
        () => {

            if (
                busy
            ) {
                return;
            }

            onCancel();
        };


    // ========================================================
    // SUBMIT
    // ========================================================

    const submit =
        async () => {

            setLocalError(
                ""
            );


            if (
                !file
            ) {

                setLocalError(
                    "Selecione o ZIP da biblioteca."
                );

                return;
            }


            if (
                !name.trim()
            ) {

                setLocalError(
                    "Informe o nome da biblioteca."
                );

                return;
            }


            if (
                !importName.trim()
            ) {

                setLocalError(
                    "Informe o import_name da biblioteca."
                );

                return;
            }


            await onImport({
                name:
                    name.trim(),

                importName:
                    importName.trim(),

                description:
                    description.trim(),

                file,
            });
        };


    if (
        !open
    ) {
        return null;
    }


    const visibleError =
        localError ||
        error;


    // ========================================================
    // RENDER
    // ========================================================

    return (
        <div
            className="development-library-import-backdrop"
            onMouseDown={(event) => {

                if (
                    event.target ===
                        event.currentTarget &&
                    !busy
                ) {

                    cancelar();
                }
            }}
        >
            <section
                className="development-library-import-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="development-library-import-title"
            >

                {/* =============================================
                    CABEÇALHO
                ============================================= */}

                <header
                    className="development-library-import-header"
                >
                    <div>
                        <span
                            className="development-library-import-eyebrow"
                        >
                            PROJECT LIBRARY
                        </span>

                        <h2
                            id="development-library-import-title"
                        >
                            Importar biblioteca
                        </h2>

                        <p>
                            Importe um pacote ZIP diretamente
                            para a Working Copy deste projeto.
                            Nenhuma versão será publicada agora.
                        </p>
                    </div>


                    <button
                        type="button"
                        className="development-library-import-close"
                        onClick={
                            cancelar
                        }
                        disabled={
                            busy
                        }
                        aria-label="Fechar"
                    >
                        <X
                            size={17}
                        />
                    </button>
                </header>


                {/* =============================================
                    BODY
                ============================================= */}

                <div
                    className="development-library-import-body"
                >

                    {/* =========================================
                        ZIP
                    ========================================= */}

                    <input
                        ref={
                            fileInputRef
                        }
                        type="file"
                        accept=".zip,application/zip"
                        className="development-library-import-file-input"
                        disabled={
                            busy
                        }
                        onChange={(event) => {

                            selecionarArquivo(
                                event.target
                                    .files?.[0] ??
                                null
                            );
                        }}
                    />


                    <button
                        type="button"
                        className={[
                            "development-library-import-dropzone",

                            dragActive
                                ? "development-library-import-dropzone-active"
                                : "",
                        ]
                            .filter(Boolean)
                            .join(" ")}
                        disabled={
                            busy
                        }
                        onClick={() => {

                            fileInputRef.current
                                ?.click();
                        }}
                        onDragEnter={(event) => {

                            event.preventDefault();

                            if (!busy) {
                                setDragActive(
                                    true
                                );
                            }
                        }}
                        onDragOver={(event) => {

                            event.preventDefault();
                        }}
                        onDragLeave={(event) => {

                            event.preventDefault();

                            setDragActive(
                                false
                            );
                        }}
                        onDrop={(event) => {

                            event.preventDefault();

                            if (
                                busy
                            ) {
                                return;
                            }

                            selecionarArquivo(
                                event.dataTransfer
                                    .files?.[0] ??
                                null
                            );
                        }}
                    >
                        <span
                            className="development-library-import-dropzone-icon"
                        >
                            <Upload
                                size={20}
                            />
                        </span>


                        <span
                            className="development-library-import-dropzone-copy"
                        >
                            <strong>
                                {file
                                    ? file.name
                                    : "Selecione ou arraste o ZIP"}
                            </strong>

                            <small>
                                {file
                                    ? `${formatarTamanho(file.size)} · pacote pronto para validação`
                                    : "O pacote deve conter o namespace Python da biblioteca na raiz."}
                            </small>
                        </span>


                        <span
                            className="development-library-import-dropzone-action"
                        >
                            {file
                                ? "Trocar"
                                : "Selecionar"}
                        </span>
                    </button>


                    {/* =========================================
                        INFORMAÇÃO DE DEVELOPMENT
                    ========================================= */}

                    <div
                        className="development-library-import-info"
                    >
                        <FileArchive
                            size={17}
                        />

                        <div>
                            <strong>
                                Importação em Desenvolvimento
                            </strong>

                            <span>
                                O código será criado somente
                                como Working Copy. A publicação
                                para Produção acontecerá junto
                                ao Release do projeto.
                            </span>
                        </div>
                    </div>


                    {/* =========================================
                        NOME
                    ========================================= */}

                    <label
                        className="development-library-import-field"
                    >
                        <span>
                            Nome
                        </span>

                        <input
                            type="text"
                            value={
                                name
                            }
                            disabled={
                                busy
                            }
                            placeholder="Ex.: Logging Core"
                            onChange={(event) => {

                                const value =
                                    event.target.value;

                                setName(
                                    value
                                );

                                setLocalError(
                                    ""
                                );


                                if (
                                    !importNameTouched
                                ) {

                                    setImportName(
                                        suggestImportName(
                                            value
                                        )
                                    );
                                }
                            }}
                        />
                    </label>


                    {/* =========================================
                        IMPORT NAME
                    ========================================= */}

                    <label
                        className="development-library-import-field"
                    >
                        <span>
                            import_name
                        </span>

                        <input
                            type="text"
                            value={
                                importName
                            }
                            disabled={
                                busy
                            }
                            placeholder="logging_core"
                            spellCheck={
                                false
                            }
                            autoCapitalize="none"
                            onChange={(event) => {

                                setImportNameTouched(
                                    true
                                );

                                setImportName(
                                    event.target.value
                                );

                                setLocalError(
                                    ""
                                );
                            }}
                        />

                        <small>
                            Namespace Python do pacote.
                            Exemplo: from logging_core import ...
                        </small>
                    </label>


                    {/* =========================================
                        DESCRIÇÃO
                    ========================================= */}

                    <label
                        className="development-library-import-field"
                    >
                        <span>
                            Descrição
                            <em>
                                opcional
                            </em>
                        </span>

                        <textarea
                            value={
                                description
                            }
                            disabled={
                                busy
                            }
                            placeholder="Responsabilidade desta biblioteca..."
                            onChange={(event) => {

                                setDescription(
                                    event.target.value
                                );

                                setLocalError(
                                    ""
                                );
                            }}
                        />
                    </label>


                    {/* =========================================
                        ERRO
                    ========================================= */}

                    {visibleError && (
                        <div
                            className="development-library-import-error"
                            role="alert"
                        >
                            {visibleError}
                        </div>
                    )}
                </div>


                {/* =============================================
                    FOOTER
                ============================================= */}

                <footer
                    className="development-library-import-footer"
                >
                    <button
                        type="button"
                        className="development-library-import-secondary"
                        disabled={
                            busy
                        }
                        onClick={
                            cancelar
                        }
                    >
                        Cancelar
                    </button>


                    <button
                        type="button"
                        className="development-library-import-primary"
                        disabled={
                            busy ||
                            !file ||
                            !name.trim() ||
                            !importName.trim()
                        }
                        onClick={() =>
                            void submit()
                        }
                    >
                        {busy
                            ? "Importando..."
                            : "Importar para o projeto"}
                    </button>
                </footer>
            </section>
        </div>
    );
}


export default DevelopmentLibraryImportModal;
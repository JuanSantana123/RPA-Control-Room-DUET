// ============================================================
// DEVELOPMENT PROJECT IMPORT DIALOG
// ============================================================
//
// Responsabilidade:
//     Renderiza exclusivamente a interface do fluxo de importação.
//
// Este componente NÃO:
//     - chama APIs;
//     - cria projetos;
//     - altera permissões;
//     - cria Checkout;
//     - escolhe EntryPoint automaticamente.
// ============================================================

import {
    createPortal,
} from "react-dom";

import {
    PackageOpen,
    Upload,
    X,
} from "lucide-react";

import type {
    DevelopmentProjectImportAnalysis,
} from "../../../services/developmentProjectImportApi";


interface ProjectImportDialogProps {
    open: boolean;
    canCreate: boolean;

    selectedFile: File | null;
    analysis: DevelopmentProjectImportAnalysis | null;

    projectName: string;
    projectDescription: string;
    entrypointPath: string;

    analyzing: boolean;
    confirming: boolean;
    error: string;

    onFileChange: (file: File | null) => void;
    onProjectNameChange: (value: string) => void;
    onProjectDescriptionChange: (value: string) => void;
    onEntrypointChange: (value: string) => void;

    onAnalyze: () => void | Promise<void>;
    onConfirm: () => void | Promise<void>;
    onClose: () => void;
}


function ProjectImportDialog({
    open,
    canCreate,

    selectedFile,
    analysis,

    projectName,
    projectDescription,
    entrypointPath,

    analyzing,
    confirming,
    error,

    onFileChange,
    onProjectNameChange,
    onProjectDescriptionChange,
    onEntrypointChange,

    onAnalyze,
    onConfirm,
    onClose,
}: ProjectImportDialogProps) {

    if (
        !open ||
        !canCreate
    ) {
        return null;
    }

    const busy =
        analyzing ||
        confirming;

    const canConfirm =
        Boolean(
            analysis &&
            projectName.trim() &&
            entrypointPath
        ) &&
        !busy;


    return createPortal(
        <div
            role="presentation"
            onMouseDown={() => {
                if (!busy) {
                    onClose();
                }
            }}
            style={{
                position: "fixed",
                inset: 0,
                zIndex: 10000,
                display: "flex",
                alignItems: "center",
                justifyContent: "center",
                padding: 20,
                background: "var(--overlay-backdrop, rgba(15, 23, 42, 0.48))",
                boxSizing: "border-box",
            }}
        >
            <div
                role="dialog"
                aria-modal="true"
                aria-labelledby="development-project-import-title"
                onMouseDown={(event) => {
                    event.stopPropagation();
                }}
                style={{
                    width: "100%",
                    maxWidth: 720,
                    maxHeight: "calc(100vh - 40px)",
                    overflowY: "auto",
                    padding: 22,
                    border: "1px solid var(--border-color, #dfe3ea)",
                    borderRadius: 12,
                    background: "var(--surface-color, #ffffff)",
                    boxShadow: "var(--shadow-xl, 0 24px 70px rgba(15, 23, 42, 0.28))",
                    boxSizing: "border-box",
                }}
            >
                <div
                    style={{
                        display: "flex",
                        alignItems: "flex-start",
                        justifyContent: "space-between",
                        gap: 16,
                    }}
                >
                    <div>
                        <div
                            style={{
                                fontSize: 11,
                                fontWeight: 800,
                                letterSpacing: "0.08em",
                                opacity: 0.58,
                            }}
                        >
                            DEVELOPMENT
                        </div>

                        <h2
                            id="development-project-import-title"
                            style={{
                                margin: "6px 0 0",
                                fontSize: 20,
                            }}
                        >
                            Importar projeto Python
                        </h2>

                        <p
                            style={{
                                margin: "8px 0 0",
                                fontSize: 13,
                                lineHeight: 1.55,
                                opacity: 0.72,
                            }}
                        >
                            Analise o pacote, escolha explicitamente o EntryPoint e só então confirme a criação do AutomationProject.
                        </p>
                    </div>

                    <button
                        type="button"
                        className="secondary-button"
                        disabled={busy}
                        aria-label="Fechar importação"
                        title="Fechar"
                        onClick={onClose}
                        style={{
                            minWidth: 38,
                            paddingInline: 10,
                        }}
                    >
                        <X
                            size={16}
                            strokeWidth={1.9}
                        />
                    </button>
                </div>


                <div
                    style={{
                        marginTop: 18,
                        padding: 14,
                        border: "1px solid var(--border-color, #dfe3ea)",
                        borderRadius: 8,
                        background: "var(--surface-hover, rgba(100, 116, 139, 0.06))",
                    }}
                >
                    <div
                        style={{
                            display: "flex",
                            gap: 10,
                            alignItems: "flex-start",
                        }}
                    >
                        <PackageOpen
                            size={18}
                            strokeWidth={1.8}
                            aria-hidden="true"
                        />

                        <div>
                            <strong
                                style={{
                                    display: "block",
                                    fontSize: 13,
                                }}
                            >
                                Importação em duas etapas
                            </strong>

                            <p
                                style={{
                                    margin: "4px 0 0",
                                    fontSize: 12,
                                    lineHeight: 1.5,
                                    opacity: 0.72,
                                }}
                            >
                                A análise apenas inspeciona o ZIP e localiza arquivos Python. O projeto só é criado depois que você selecionar o EntryPoint.
                            </p>
                        </div>
                    </div>
                </div>


                <div
                    className="form-field"
                    style={{
                        marginTop: 18,
                    }}
                >
                    <label htmlFor="development-project-import-file">
                        Pacote ZIP
                    </label>

                    <input
                        key={analysis?.import_token || "new-package"}
                        id="development-project-import-file"
                        type="file"
                        accept=".zip,application/zip"
                        disabled={busy}
                        onChange={(event) => {
                            onFileChange(
                                event.target.files?.[0] || null
                            );
                        }}
                    />

                    {selectedFile && (
                        <small>
                            Selecionado: {selectedFile.name}
                        </small>
                    )}
                </div>


                {!analysis && (
                    <div
                        style={{
                            display: "flex",
                            justifyContent: "flex-end",
                            gap: 8,
                            marginTop: 18,
                        }}
                    >
                        <button
                            type="button"
                            className="secondary-button"
                            disabled={busy}
                            onClick={onClose}
                        >
                            Cancelar
                        </button>

                        <button
                            type="button"
                            className="primary-button"
                            disabled={
                                !selectedFile ||
                                busy
                            }
                            onClick={onAnalyze}
                        >
                            <Upload
                                size={15}
                                strokeWidth={1.9}
                            />

                            {analyzing
                                ? "Analisando..."
                                : "Analisar pacote"}
                        </button>
                    </div>
                )}


                {analysis && (
                    <>
                        <div
                            style={{
                                marginTop: 18,
                                padding: 14,
                                border: "1px solid var(--border-color, #dfe3ea)",
                                borderRadius: 8,
                            }}
                        >
                            <strong
                                style={{
                                    display: "block",
                                    fontSize: 13,
                                }}
                            >
                                Pacote analisado com sucesso
                            </strong>

                            <div
                                style={{
                                    marginTop: 6,
                                    fontSize: 12,
                                    lineHeight: 1.55,
                                    opacity: 0.72,
                                }}
                            >
                                {analysis.filename} · {analysis.python_files.length} arquivo(s) Python encontrado(s)
                            </div>
                        </div>


                        <div
                            className="form-field"
                            style={{
                                marginTop: 18,
                            }}
                        >
                            <label htmlFor="development-project-import-name">
                                Nome do projeto
                            </label>

                            <input
                                id="development-project-import-name"
                                type="text"
                                maxLength={255}
                                value={projectName}
                                disabled={busy}
                                onChange={(event) => {
                                    onProjectNameChange(
                                        event.target.value
                                    );
                                }}
                            />
                        </div>


                        <div
                            className="form-field"
                            style={{
                                marginTop: 14,
                            }}
                        >
                            <label htmlFor="development-project-import-description">
                                Descrição
                            </label>

                            <textarea
                                id="development-project-import-description"
                                maxLength={5000}
                                rows={4}
                                value={projectDescription}
                                disabled={busy}
                                onChange={(event) => {
                                    onProjectDescriptionChange(
                                        event.target.value
                                    );
                                }}
                            />
                        </div>


                        <div
                            className="form-field"
                            style={{
                                marginTop: 14,
                            }}
                        >
                            <label htmlFor="development-project-import-entrypoint">
                                EntryPoint *
                            </label>

                            <select
                                id="development-project-import-entrypoint"
                                value={entrypointPath}
                                disabled={busy}
                                onChange={(event) => {
                                    onEntrypointChange(
                                        event.target.value
                                    );
                                }}
                            >
                                <option value="">
                                    Selecione explicitamente o EntryPoint
                                </option>

                                {analysis.python_files.map(
                                    (pythonFile) => (
                                        <option
                                            key={pythonFile}
                                            value={pythonFile}
                                        >
                                            {pythonFile}
                                            {analysis.suggested_entrypoint === pythonFile
                                                ? " — sugerido"
                                                : ""}
                                        </option>
                                    )
                                )}
                            </select>

                            <small>
                                O DUET não seleciona automaticamente. A importação só é confirmada depois da sua escolha.
                            </small>
                        </div>


                        <div
                            style={{
                                display: "flex",
                                justifyContent: "space-between",
                                gap: 8,
                                marginTop: 20,
                                flexWrap: "wrap",
                            }}
                        >
                            <button
                                type="button"
                                className="secondary-button"
                                disabled={busy}
                                onClick={() => {
                                    onFileChange(null);
                                }}
                            >
                                Trocar pacote
                            </button>

                            <div
                                style={{
                                    display: "flex",
                                    justifyContent: "flex-end",
                                    gap: 8,
                                }}
                            >
                                <button
                                    type="button"
                                    className="secondary-button"
                                    disabled={busy}
                                    onClick={onClose}
                                >
                                    Cancelar
                                </button>

                                <button
                                    type="button"
                                    className="primary-button"
                                    disabled={!canConfirm}
                                    onClick={onConfirm}
                                >
                                    <Upload
                                        size={15}
                                        strokeWidth={1.9}
                                    />

                                    {confirming
                                        ? "Importando..."
                                        : "Importar projeto"}
                                </button>
                            </div>
                        </div>
                    </>
                )}


                {error && (
                    <div
                        className="alert alert-error"
                        style={{
                            marginTop: 14,
                            marginBottom: 0,
                            whiteSpace: "pre-line",
                            lineHeight: 1.5,
                        }}
                    >
                        {error}
                    </div>
                )}
            </div>
        </div>,
        document.body
    );
}


export default ProjectImportDialog;

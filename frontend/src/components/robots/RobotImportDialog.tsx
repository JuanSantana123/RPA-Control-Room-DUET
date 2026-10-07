// ============================================================
// DUET CORE - ROBOTS - IMPORT DIALOG
// ============================================================
//
// Responsabilidade:
// - selecionar o ZIP;
// - solicitar análise;
// - apresentar arquivos Python encontrados;
// - permitir escolher o EntryPoint;
// - confirmar a importação.
//
// Este componente NÃO chama APIs.
// Toda regra pertence a useRobotImport.
// ============================================================

import {
    FileCode2,
    PackageOpen,
    ShieldCheck,
    Upload,
    X,
} from "lucide-react";

import {
    createPortal,
} from "react-dom";

import {
    useDialogFocus,
} from "../../hooks/ui/useDialogFocus";

import type {
    RobotImportAnalysis,
} from "../../services/robotPackagesApi";

import {
    Button,
    IconButton,
} from "../ui/Button";

import FeedbackBanner
    from "../ui/FeedbackBanner";

import PremiumSelect
    from "../ui/PremiumSelect";


// ============================================================
// PROPS
// ============================================================

interface RobotImportDialogProps {

    open: boolean;

    targetLocation: string;

    selectedFile:
        File | null;

    analysis:
        RobotImportAnalysis | null;

    entrypointPath:
        string;

    analyzing:
        boolean;

    importing:
        boolean;

    error:
        string;

    onFileChange:
        (file: File | null) => void;

    onEntrypointChange:
        (value: string) => void;

    onAnalyze:
        () => void | Promise<void>;

    onImport:
        () => void | Promise<void>;

    onClose:
        () => void;
}


// ============================================================
// COMPONENTE
// ============================================================

export default function RobotImportDialog({
    open,

    targetLocation,

    selectedFile,
    analysis,
    entrypointPath,

    analyzing,
    importing,
    error,

    onFileChange,
    onEntrypointChange,

    onAnalyze,
    onImport,
    onClose,
}: RobotImportDialogProps) {

    const busy =
        analyzing ||
        importing;


    const dialogRef =
        useDialogFocus<HTMLDivElement>({
            open,
            onClose,
            closeOnEscape: !busy,
        });


    if (!open) {
        return null;
    }


    const entrypointLocked =
        Boolean(
            analysis?.entrypoint_locked &&
            analysis.configured_entrypoint
        );


    const canImport =
        Boolean(
            selectedFile &&
            analysis &&
            entrypointPath
        ) &&
        !busy;


    return createPortal(

        <div
            className="ui-modal-backdrop"
            role="presentation"

            onMouseDown={(event) => {

                if (
                    event.target ===
                        event.currentTarget &&
                    !busy
                ) {
                    onClose();
                }
            }}

            style={{
                position: "fixed",
                inset: 0,
                zIndex: 1320,

                display: "grid",
                placeItems: "center",

                padding: "clamp(12px, 3vw, 32px)",
            }}
        >

            <div
                ref={dialogRef}

                className="ui-modal-surface"

                role="dialog"
                aria-modal="true"

                aria-labelledby="robot-import-title"
                aria-describedby="robot-import-description"

                tabIndex={-1}

                style={{
                    width: "min(680px, 100%)",

                    maxHeight:
                        "min(780px, calc(100dvh - 32px))",

                    display: "grid",

                    gridTemplateRows:
                        "auto minmax(0, 1fr) auto",

                    overflow: "hidden",
                }}
            >

                {/* ====================================================
                    HEADER
                ==================================================== */}

                <header
                    className="ui-modal-header"

                    style={{
                        display: "flex",

                        alignItems:
                            "flex-start",

                        justifyContent:
                            "space-between",

                        gap: 18,

                        padding:
                            "20px 22px",
                    }}
                >

                    <div
                        style={{
                            display: "flex",
                            gap: 12,
                            alignItems: "flex-start",
                        }}
                    >

                        <PackageOpen
                            size={21}
                            strokeWidth={1.8}
                            aria-hidden="true"
                        />

                        <div>

                            <span className="page-eyebrow">
                                IMPORTAR PACOTE
                            </span>

                            <h2
                                id="robot-import-title"
                            >
                                Importar robô publicado
                            </h2>

                            <p
                                id="robot-import-description"
                            >
                                Analise o ZIP, escolha o arquivo Python
                                que inicia a automação e confirme a publicação.
                            </p>

                        </div>

                    </div>


                    <IconButton
                        data-autofocus

                        label="Fechar importação"

                        icon={
                            <X
                                size={18}
                                aria-hidden="true"
                            />
                        }

                        disabled={busy}

                        onClick={onClose}
                    />

                </header>


                {/* ====================================================
                    BODY
                ==================================================== */}

                <div
                    style={{
                        overflowY: "auto",
                        padding: 22,

                        display: "grid",
                        gap: 18,
                    }}
                >

                    {error && (

                        <FeedbackBanner
                            tone="error"

                            title={
                                "Não foi possível concluir a importação"
                            }

                            message={error}

                            hint={
                                "Nenhum Robot foi publicado. Revise o pacote e tente novamente."
                            }
                        />

                    )}


                    {/* DESTINO */}

                    <section
                        className="content-panel"
                        style={{
                            padding: 14,
                        }}
                    >

                        <span className="page-eyebrow">
                            DESTINO
                        </span>

                        <strong
                            style={{
                                display: "block",
                                marginTop: 5,
                            }}
                        >
                            {targetLocation}
                        </strong>

                    </section>


                    {/* PACOTE */}

                    <div className="form-field">

                        <label
                            htmlFor="robot-import-file"
                        >
                            Pacote ZIP
                        </label>

                        <input
                            id="robot-import-file"

                            type="file"

                            accept=".zip,application/zip"

                            disabled={busy}

                            onChange={(event) => {

                                onFileChange(
                                    event.target.files?.[0]
                                    ?? null,
                                );
                            }}
                        />

                        {selectedFile && (

                            <small>
                                Selecionado: {selectedFile.name}
                            </small>

                        )}

                    </div>


                    {/* RESULTADO DA ANÁLISE */}

                    {analysis && (

                        <section
                            className="content-panel"

                            style={{
                                padding: 14,

                                display: "grid",
                                gap: 10,
                            }}
                        >

                            <div
                                style={{
                                    display: "flex",
                                    gap: 10,
                                    alignItems: "center",
                                }}
                            >

                                <ShieldCheck
                                    size={18}
                                    strokeWidth={1.8}
                                    aria-hidden="true"
                                />

                                <div>

                                    <strong>
                                        Pacote analisado
                                    </strong>

                                    <div>
                                        <small>
                                            {analysis.filename}
                                            {" · "}
                                            {analysis.python_files.length}
                                            {" arquivo(s) Python"}
                                        </small>
                                    </div>

                                </div>

                            </div>

                        </section>

                    )}


                    {/* ENTRYPOINT */}

                    {analysis && (

                        <div className="form-field">

                            <label
                                htmlFor="robot-import-entrypoint"
                            >
                                EntryPoint
                            </label>


                            <PremiumSelect
                                id="robot-import-entrypoint"

                                value={entrypointPath}

                                disabled={
                                    busy ||
                                    entrypointLocked
                                }

                                onChange={(event) => {

                                    onEntrypointChange(
                                        event.target.value,
                                    );
                                }}
                            >

                                {!entrypointLocked && (

                                    <option value="">
                                        Selecione o arquivo Python
                                    </option>

                                )}


                                {analysis.python_files.map(
                                    (pythonFile) => (

                                        <option
                                            key={pythonFile}
                                            value={pythonFile}
                                        >
                                            {pythonFile}

                                            {
                                                !entrypointLocked &&
                                                analysis
                                                    .suggested_entrypoint
                                                === pythonFile
                                                    ? " — sugerido"
                                                    : ""
                                            }

                                        </option>

                                    ),
                                )}

                            </PremiumSelect>


                            {entrypointLocked ? (

                                <small>
                                    Este pacote já é um Release DUET.
                                    O EntryPoint faz parte da versão
                                    publicada e será preservado.
                                </small>

                            ) : (

                                <small>
                                    Escolha explicitamente qual arquivo
                                    .py inicia a automação.
                                </small>

                            )}

                        </div>

                    )}


                    {/* LISTAGEM AUXILIAR */}

                    {analysis && (
                        <section>

                            <span className="page-eyebrow">
                                ARQUIVOS PYTHON ENCONTRADOS
                            </span>

                            <div
                                style={{
                                    display: "grid",
                                    gap: 6,
                                    marginTop: 10,
                                }}
                            >

                                {analysis.python_files.map(
                                    (pythonFile) => (

                                        <div
                                            key={pythonFile}

                                            style={{
                                                display: "flex",
                                                alignItems: "center",
                                                gap: 8,
                                            }}
                                        >

                                            <FileCode2
                                                size={15}
                                                strokeWidth={1.8}
                                                aria-hidden="true"
                                            />

                                            <code>
                                                {pythonFile}
                                            </code>

                                        </div>

                                    ),
                                )}

                            </div>

                        </section>
                    )}

                </div>


                {/* ====================================================
                    FOOTER
                ==================================================== */}

                <footer
                    style={{
                        display: "flex",

                        justifyContent:
                            "space-between",

                        alignItems:
                            "center",

                        gap: 10,

                        padding:
                            "18px 22px",

                        flexWrap:
                            "wrap",
                    }}
                >

                    <div>

                        {analysis && (

                            <Button
                                variant="secondary"

                                disabled={busy}

                                onClick={() => {
                                    onFileChange(
                                        null,
                                    );
                                }}
                            >
                                Trocar pacote
                            </Button>

                        )}

                    </div>


                    <div
                        style={{
                            display: "flex",
                            gap: 8,
                        }}
                    >

                        <Button
                            variant="secondary"

                            disabled={busy}

                            onClick={onClose}
                        >
                            Cancelar
                        </Button>


                        {!analysis ? (

                            <Button
                                disabled={
                                    !selectedFile ||
                                    busy
                                }

                                busy={analyzing}

                                loadingLabel={
                                    "Analisando pacote"
                                }

                                onClick={() => {
                                    void onAnalyze();
                                }}
                            >

                                <Upload
                                    size={15}
                                    aria-hidden="true"
                                />

                                Analisar pacote

                            </Button>

                        ) : (

                            <Button
                                disabled={!canImport}

                                busy={importing}

                                loadingLabel={
                                    "Importando pacote"
                                }

                                onClick={() => {
                                    void onImport();
                                }}
                            >

                                <Upload
                                    size={15}
                                    aria-hidden="true"
                                />

                                Importar pacote

                            </Button>

                        )}

                    </div>

                </footer>

            </div>

        </div>,

        document.body,
    );
}
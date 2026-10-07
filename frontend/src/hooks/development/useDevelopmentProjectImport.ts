// ============================================================
// USE DEVELOPMENT PROJECT IMPORT
// ============================================================
//
// Responsabilidade:
//     Orquestra o fluxo de importação de um projeto Python sem
//     acoplar a página Development.tsx às chamadas HTTP.
//
// Regras importantes:
//     - analisar o pacote NÃO cria AutomationProject;
//     - o EntryPoint fica vazio após a análise para exigir uma
//       escolha explícita do usuário;
//     - somente confirmImport() cria o projeto;
//     - não cria Checkout automaticamente;
//     - o projeto importado nasce na raiz de Development nesta V1,
//       preservando a regra atual da criação normal.
// ============================================================

import {
    useState,
} from "react";

import {
    analyzeDevelopmentProjectImport,
    confirmDevelopmentProjectImport,
} from "../../services/developmentProjectImportApi";

import type {
    DevelopmentProjectImportAnalysis,
} from "../../services/developmentProjectImportApi";

import {
    getApiErrorMessage,
} from "../../utils/apiErrors";

import type {
    DevelopmentProject,
} from "../../types/development";


interface UseDevelopmentProjectImportParams {
    canCreateDevelopment: boolean;
    isKanbanView: boolean;

    onProjectImported:
        (project: DevelopmentProject) => void;

    onRefreshKanban:
        () => Promise<void>;
}


interface UseDevelopmentProjectImportResult {
    importDialogOpen: boolean;
    selectedImportFile: File | null;
    importAnalysis: DevelopmentProjectImportAnalysis | null;

    importProjectName: string;
    importProjectDescription: string;
    importEntrypointPath: string;

    analyzingImport: boolean;
    confirmingImport: boolean;
    importError: string;

    openImportDialog: () => void;
    closeImportDialog: () => void;

    changeImportFile: (file: File | null) => void;
    setImportProjectName: (value: string) => void;
    setImportProjectDescription: (value: string) => void;
    setImportEntrypointPath: (value: string) => void;

    analyzeImport: () => Promise<void>;
    confirmImport: () => Promise<void>;
}


function deriveProjectNameFromFile(
    file: File | null
): string {

    if (!file) {
        return "";
    }

    return file.name.replace(/\.zip$/i, "");
}
// ============================================================
// FORMATAR ERRO DE IMPORTAÇÃO
// ============================================================
//
// Mantém a mensagem técnica devolvida pelo backend como motivo,
// mas apresenta o erro ao desenvolvedor em um formato claro.
//
// Exemplo:
//
// O pacote não pôde ser importado.
//
// Motivo:
// Nenhum arquivo Python (.py) foi encontrado no pacote.
// ============================================================

function formatImportError(
    err: unknown,
    fallbackReason: string
): string {

    const reason =
        getApiErrorMessage(
            err,
            fallbackReason
        ).trim();

    return [
        "O pacote não pôde ser importado.",
        "",
        "Motivo:",
        reason,
    ].join("\n");
}

function useDevelopmentProjectImport({
    canCreateDevelopment,
    isKanbanView,
    onProjectImported,
    onRefreshKanban,
}: UseDevelopmentProjectImportParams): UseDevelopmentProjectImportResult {

    const [importDialogOpen, setImportDialogOpen] =
        useState(false);

    const [selectedImportFile, setSelectedImportFile] =
        useState<File | null>(null);

    const [importAnalysis, setImportAnalysis] =
        useState<DevelopmentProjectImportAnalysis | null>(null);

    const [importProjectName, setImportProjectName] =
        useState("");

    const [importProjectDescription, setImportProjectDescription] =
        useState("");

    const [importEntrypointPath, setImportEntrypointPath] =
        useState("");

    const [analyzingImport, setAnalyzingImport] =
        useState(false);

    const [confirmingImport, setConfirmingImport] =
        useState(false);

    const [importError, setImportError] =
        useState("");


    const resetImportState = () => {
        setSelectedImportFile(null);
        setImportAnalysis(null);
        setImportProjectName("");
        setImportProjectDescription("");
        setImportEntrypointPath("");
        setImportError("");
    };


    const openImportDialog = () => {

        if (!canCreateDevelopment) {
            return;
        }

        resetImportState();
        setImportDialogOpen(true);
    };


    const closeImportDialog = () => {

        if (
            analyzingImport ||
            confirmingImport
        ) {
            return;
        }

        setImportDialogOpen(false);
        resetImportState();
    };


    const changeImportFile = (
        file: File | null
    ) => {

        setSelectedImportFile(file);

        // Toda troca de pacote invalida a análise anterior.
        setImportAnalysis(null);
        setImportEntrypointPath("");
        setImportError("");

        // Facilita o preenchimento sem impedir edição manual.
        setImportProjectName(
            deriveProjectNameFromFile(file)
        );
    };


    const analyzeImport = async () => {

        if (
            !canCreateDevelopment ||
            !selectedImportFile ||
            analyzingImport ||
            confirmingImport
        ) {
            return;
        }

        try {
            setAnalyzingImport(true);
            setImportError("");

            const analysis =
                await analyzeDevelopmentProjectImport(
                    selectedImportFile
                );

            setImportAnalysis(analysis);

            // Não selecionamos automaticamente nem mesmo main.py.
            // O requisito é exigir a confirmação explícita do usuário.
            setImportEntrypointPath("");

        } catch (err) {
            console.error(
                "Erro ao analisar pacote de projeto:",
                err
            );

            setImportAnalysis(null);
            setImportEntrypointPath("");

            setImportError(
                formatImportError(
                    err,
                    "Não foi possível analisar o pacote do projeto."
                )
            );

        } finally {
            setAnalyzingImport(false);
        }
    };


    const confirmImport = async () => {

        const name =
            importProjectName.trim();

        if (
            !canCreateDevelopment ||
            !importAnalysis ||
            !name ||
            !importEntrypointPath ||
            analyzingImport ||
            confirmingImport
        ) {
            return;
        }

        try {
            setConfirmingImport(true);
            setImportError("");

            const response =
                await confirmDevelopmentProjectImport({
                    import_token:
                        importAnalysis.import_token,

                    name,

                    description:
                        importProjectDescription.trim() || null,

                    // A criação normal atual também nasce na raiz.
                    // Mantemos o mesmo comportamento nesta V1.
                    folder_id:
                        null,

                    entrypoint_path:
                        importEntrypointPath,
                });

            if (!response.project) {
                throw new Error(
                    "O backend não retornou o projeto importado."
                );
            }

            onProjectImported(
                response.project
            );

            if (isKanbanView) {
                await onRefreshKanban();
            }

            setImportDialogOpen(false);
            resetImportState();

        } catch (err) {
            console.error(
                "Erro ao importar projeto de Desenvolvimento:",
                err
            );

            setImportError(
                formatImportError(
                    err,
                    "Não foi possível importar o projeto."
                )
            );

        } finally {
            setConfirmingImport(false);
        }
    };


    return {
        importDialogOpen,
        selectedImportFile,
        importAnalysis,

        importProjectName,
        importProjectDescription,
        importEntrypointPath,

        analyzingImport,
        confirmingImport,
        importError,

        openImportDialog,
        closeImportDialog,

        changeImportFile,
        setImportProjectName,
        setImportProjectDescription,
        setImportEntrypointPath,

        analyzeImport,
        confirmImport,
    };
}


export default useDevelopmentProjectImport;

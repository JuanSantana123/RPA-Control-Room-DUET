// ============================================================
// DUET CORE - ROBOTS - IMPORT HOOK
// ============================================================
//
// Responsabilidade:
// - abrir o fluxo de Importação;
// - guardar a pasta de destino;
// - analisar o ZIP;
// - exigir/resolver o EntryPoint;
// - confirmar a publicação;
// - atualizar a localização após sucesso.
//
// IMPORTANTE:
// - analisar NÃO cria Robot;
// - ZIP comum NÃO recebe EntryPoint automaticamente;
// - pacote DUET preserva o EntryPoint do Release;
// - este hook NÃO reutiliza /robots/upload.
// ============================================================

import {
    useCallback,
    useState,
} from "react";

import {
    analyzeRobotPackage,
    importRobotPackage,
} from "../../services/robotPackagesApi";

import type {
    RobotImportAnalysis,
} from "../../services/robotPackagesApi";

import {
    obterMensagemErro,
} from "../../utils/robotErrors";


// ============================================================
// CONTRATO
// ============================================================

interface UseRobotImportOptions {

    setError: (
        message: string,
    ) => void;

    setSuccess: (
        message: string,
    ) => void;

    onImported: (
        folderId: number | null,
    ) => Promise<void> | void;
}


// ============================================================
// HOOK
// ============================================================

export function useRobotImport({
    setError,
    setSuccess,
    onImported,
}: UseRobotImportOptions) {

    // ========================================================
    // MODAL
    // ========================================================

    const [
        dialogOpen,
        setDialogOpen,
    ] = useState(false);


    // ========================================================
    // DESTINO
    // ========================================================

    const [
        targetFolderId,
        setTargetFolderId,
    ] = useState<number | null>(
        null,
    );


    // ========================================================
    // PACOTE
    // ========================================================

    const [
        selectedFile,
        setSelectedFile,
    ] = useState<File | null>(
        null,
    );


    // ========================================================
    // RESULTADO DA ANÁLISE
    // ========================================================

    const [
        analysis,
        setAnalysis,
    ] = useState<RobotImportAnalysis | null>(
        null,
    );


    // ========================================================
    // ENTRYPOINT
    // ========================================================

    const [
        entrypointPath,
        setEntrypointPath,
    ] = useState("");


    // ========================================================
    // ESTADOS OPERACIONAIS
    // ========================================================

    const [
        analyzing,
        setAnalyzing,
    ] = useState(false);

    const [
        importing,
        setImporting,
    ] = useState(false);

    const [
        importError,
        setImportError,
    ] = useState("");


    const busy =
        analyzing ||
        importing;


    // ========================================================
    // RESET DO PACOTE
    // ========================================================

    const resetPackageState =
        useCallback(() => {

            setSelectedFile(
                null,
            );

            setAnalysis(
                null,
            );

            setEntrypointPath(
                "",
            );

            setImportError(
                "",
            );

        }, []);


    // ========================================================
    // ABRIR
    // ========================================================

    const open =
        useCallback((
            folderId: number | null,
        ) => {

            if (busy) {
                return;
            }

            resetPackageState();

            setTargetFolderId(
                folderId,
            );

            // Remove mensagens antigas da página.
            setError("");
            setSuccess("");

            setDialogOpen(
                true,
            );

        }, [
            busy,
            resetPackageState,
            setError,
            setSuccess,
        ]);


    // ========================================================
    // FECHAR
    // ========================================================

    const close =
        useCallback(() => {

            if (busy) {
                return;
            }

            setDialogOpen(
                false,
            );

            setTargetFolderId(
                null,
            );

            resetPackageState();

        }, [
            busy,
            resetPackageState,
        ]);


    // ========================================================
    // TROCAR ARQUIVO
    // ========================================================

    const changeFile =
        useCallback((
            file: File | null,
        ) => {

            if (busy) {
                return;
            }

            setSelectedFile(
                file,
            );

            // Qualquer troca de ZIP invalida a análise anterior.
            setAnalysis(
                null,
            );

            setEntrypointPath(
                "",
            );

            setImportError(
                "",
            );

        }, [
            busy,
        ]);


    // ========================================================
    // ANALISAR
    // ========================================================

    const analyze =
        useCallback(async () => {

            if (
                !selectedFile ||
                busy
            ) {
                return;
            }

            try {

                setAnalyzing(
                    true,
                );

                setImportError(
                    "",
                );

                const result =
                    await analyzeRobotPackage(
                        selectedFile,
                    );

                setAnalysis(
                    result,
                );

                // ------------------------------------------------
                // PACOTE DUET
                // ------------------------------------------------
                //
                // Se o Release já possui EntryPoint, ele faz parte
                // daquela RobotVersion e não deve ser alterado.
                // ------------------------------------------------

                if (
                    result.entrypoint_locked &&
                    result.configured_entrypoint
                ) {

                    setEntrypointPath(
                        result.configured_entrypoint,
                    );

                    return;
                }

                // ------------------------------------------------
                // ZIP PYTHON COMUM
                // ------------------------------------------------
                //
                // Mesmo que exista uma sugestão como main.py,
                // exigimos escolha explícita do usuário.
                // ------------------------------------------------

                setEntrypointPath(
                    "",
                );

            } catch (requestError) {

                console.error(
                    "Erro ao analisar pacote de Robot:",
                    requestError,
                );

                setAnalysis(
                    null,
                );

                setEntrypointPath(
                    "",
                );

                setImportError(
                    obterMensagemErro(
                        requestError,
                        (
                            `Não foi possível analisar o pacote ` +
                            `"${selectedFile.name}".`
                        ),
                    ),
                );

            } finally {

                setAnalyzing(
                    false,
                );
            }

        }, [
            busy,
            selectedFile,
        ]);


    // ========================================================
    // CONFIRMAR IMPORTAÇÃO
    // ========================================================

    const confirm =
        useCallback(async () => {

            if (
                !selectedFile ||
                !analysis ||
                !entrypointPath ||
                busy
            ) {
                return;
            }

            // Precisamos preservar o destino mesmo que o estado
            // seja limpo depois do sucesso.
            const destinationFolderId =
                targetFolderId;

            try {

                setImporting(
                    true,
                );

                setImportError(
                    "",
                );

                const result =
                    await importRobotPackage(
                        selectedFile,
                        destinationFolderId,
                        entrypointPath,
                    );

                setSuccess(
                    result.message ||
                    `Pacote "${selectedFile.name}" importado com sucesso.`,
                );

                // Fecha antes de atualizar a grade.
                setDialogOpen(
                    false,
                );

                resetPackageState();

                setTargetFolderId(
                    null,
                );

                await onImported(
                    destinationFolderId,
                );

            } catch (requestError) {

                console.error(
                    "Erro ao importar pacote de Robot:",
                    requestError,
                );

                setImportError(
                    obterMensagemErro(
                        requestError,
                        (
                            `Não foi possível importar o pacote ` +
                            `"${selectedFile.name}".`
                        ),
                    ),
                );

            } finally {

                setImporting(
                    false,
                );
            }

        }, [
            analysis,
            busy,
            entrypointPath,
            onImported,
            resetPackageState,
            selectedFile,
            setSuccess,
            targetFolderId,
        ]);


    // ========================================================
    // RETORNO
    // ========================================================

    return {
        dialogOpen,

        targetFolderId,

        selectedFile,
        analysis,
        entrypointPath,

        analyzing,
        importing,
        importError,

        open,
        close,

        changeFile,
        setEntrypointPath,

        analyze,
        confirm,
    };
}
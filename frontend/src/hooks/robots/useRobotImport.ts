// ============================================================
// DUET CORE - ROBOTS - IMPORT HOOK
// ============================================================
//
// Responsabilidade:
// - abrir exclusivamente o seletor de pacote para Importação;
// - guardar a pasta de destino;
// - enviar o ZIP para /robots/import;
// - informar sucesso/erro à página;
// - solicitar atualização da localização após a importação.
//
// IMPORTANTE:
// Este hook NÃO reutiliza o fluxo de upload tradicional.
// ============================================================

import {
    type ChangeEvent,
    useCallback,
    useRef,
    useState,
} from "react";

import {
    importRobotPackage,
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

    // Input exclusivo da operação "Importar pacote".
    const inputRef =
        useRef<HTMLInputElement>(null);

    // Guarda a localização escolhida antes da abertura
    // do seletor do Windows.
    //
    // null é um valor VÁLIDO e significa:
    //
    //     Raiz de Robôs
    const targetFolderIdRef =
        useRef<number | null>(null);

    // Precisamos diferenciar:
    //
    // null = raiz válida
    //
    // de:
    //
    // nenhuma importação iniciada.
    const hasImportTargetRef =
        useRef(false);

    const [
        importing,
        setImporting,
    ] = useState(false);


    // ========================================================
    // ABRIR SELETOR
    // ========================================================

    const open = useCallback((
        folderId: number | null,
    ) => {

        if (importing) {
            return;
        }

        targetFolderIdRef.current =
            folderId;

        hasImportTargetRef.current =
            true;

        inputRef.current?.click();

    }, [
        importing,
    ]);


    // ========================================================
    // PROCESSAR ARQUIVO SELECIONADO
    // ========================================================

    const handleFileChange = useCallback(async (
        event: ChangeEvent<HTMLInputElement>,
    ) => {

        const input =
            event.currentTarget;

        const file =
            input.files?.[0];

        // Permite selecionar novamente exatamente o mesmo ZIP.
        input.value = "";

        if (!file) {
            hasImportTargetRef.current =
                false;

            return;
        }

        if (!hasImportTargetRef.current) {
            return;
        }

        const folderId =
            targetFolderIdRef.current;

        // A seleção já foi consumida.
        hasImportTargetRef.current =
            false;

        setImporting(true);

        setError("");
        setSuccess("");

        try {

            const result =
                await importRobotPackage(
                    file,
                    folderId,
                );

            setSuccess(
                result.message ||
                `Pacote "${file.name}" importado com sucesso.`,
            );

            // Atualiza exatamente a localização onde o pacote
            // foi importado.
            await onImported(
                folderId,
            );

        } catch (requestError) {

            setError(
                obterMensagemErro(
                    requestError,
                    (
                        `Não foi possível importar o pacote ` +
                        `"${file.name}".`
                    ),
                ),
            );

        } finally {

            setImporting(false);
        }

    }, [
        onImported,
        setError,
        setSuccess,
    ]);


    return {
        inputRef,
        importing,
        open,
        handleFileChange,
    };
}
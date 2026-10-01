// ============================================================
// USE TEMPLATES ADMIN
// ============================================================
//
// Responsabilidade:
//     Centraliza o estado e as operações da administração de
//     Templates de automação do DUET CORE.
//
// Este hook controla:
//     - listagem de Templates ativos e inativos;
//     - criação do Template com sua primeira versão;
//     - publicação de uma nova versão imutável;
//     - alteração de nome/descrição;
//     - ativação/desativação;
//     - definição explícita da versão atual;
//     - download de uma versão publicada.
//
// Este arquivo NÃO renderiza interface.
// ============================================================

import {
    useCallback,
    useEffect,
    useState,
} from "react";

import {
    createAutomationTemplate,
    downloadAutomationTemplateVersion,
    getAutomationTemplates,
    publishAutomationTemplateVersion,
    setAutomationTemplateCurrentVersion,
    updateAutomationTemplate,
} from "../../services/developmentApi";

import {
    getApiErrorMessage,
} from "../../utils/apiErrors";

import type {
    AutomationTemplate,
    AutomationTemplateVersion,
} from "../../types/development";


// ============================================================
// CONTRATO PÚBLICO
// ============================================================

interface UseTemplatesAdminResult {
    templates: AutomationTemplate[];
    loading: boolean;
    busyAction: string | null;
    error: string;
    success: string;

    clearFeedback: () => void;
    reloadTemplates: () => Promise<void>;

    createTemplate: (
        name: string,
        description: string,
        file: File,
    ) => Promise<boolean>;

    publishVersion: (
        templateId: number,
        file: File,
    ) => Promise<boolean>;

    saveMetadata: (
        templateId: number,
        name: string,
        description: string,
    ) => Promise<boolean>;

    setTemplateActive: (
        templateId: number,
        active: boolean,
    ) => Promise<boolean>;

    setCurrentVersion: (
        templateId: number,
        versionId: number,
    ) => Promise<boolean>;

    downloadVersion: (
        template: AutomationTemplate,
        version: AutomationTemplateVersion,
    ) => Promise<void>;
}


// ============================================================
// HOOK
// ============================================================

export function useTemplatesAdmin(): UseTemplatesAdminResult {
    const [templates, setTemplates] =
        useState<AutomationTemplate[]>([]);

    const [loading, setLoading] =
        useState(true);

    const [busyAction, setBusyAction] =
        useState<string | null>(null);

    const [error, setError] =
        useState("");

    const [success, setSuccess] =
        useState("");


    // ========================================================
    // FEEDBACK
    // ========================================================

    const clearFeedback = useCallback(() => {
        setError("");
        setSuccess("");
    }, []);


    // ========================================================
    // ATUALIZA UM ITEM LOCALMENTE
    // ========================================================

    const replaceTemplate = useCallback(
        (
            updated: AutomationTemplate,
        ) => {
            setTemplates((current) =>
                current
                    .map((item) =>
                        item.id === updated.id
                            ? updated
                            : item
                    )
                    .sort((left, right) =>
                        left.name.localeCompare(
                            right.name,
                            "pt-BR",
                        )
                    )
            );
        },
        [],
    );


    // ========================================================
    // LISTAGEM
    // ========================================================

    const reloadTemplates = useCallback(
        async () => {
            try {
                setLoading(true);
                setError("");

                // includeInactive=true mantém a tela administrativa
                // capaz de reativar Templates desativados.
                const result =
                    await getAutomationTemplates(true);

                setTemplates(result);

            } catch (err) {
                setTemplates([]);
                setError(
                    getApiErrorMessage(
                        err,
                        "Não foi possível carregar os Templates.",
                    )
                );

            } finally {
                setLoading(false);
            }
        },
        [],
    );


    useEffect(() => {
        void reloadTemplates();
    }, [reloadTemplates]);


    // ========================================================
    // CRIAR TEMPLATE
    // ========================================================

    const createTemplate = async (
        name: string,
        description: string,
        file: File,
    ): Promise<boolean> => {
        try {
            clearFeedback();
            setBusyAction("create");

            const created =
                await createAutomationTemplate({
                    name: name.trim(),
                    description:
                        description.trim() || null,
                    file,
                });

            setTemplates((current) =>
                [created, ...current].sort(
                    (left, right) =>
                        left.name.localeCompare(
                            right.name,
                            "pt-BR",
                        )
                )
            );

            setSuccess(
                `Template "${created.name}" criado com a versão v${created.current_version ?? 1}.`
            );

            return true;

        } catch (err) {
            setError(
                getApiErrorMessage(
                    err,
                    "Não foi possível criar o Template.",
                )
            );

            return false;

        } finally {
            setBusyAction(null);
        }
    };


    // ========================================================
    // PUBLICAR NOVA VERSÃO
    // ========================================================

    const publishVersion = async (
        templateId: number,
        file: File,
    ): Promise<boolean> => {
        try {
            clearFeedback();
            setBusyAction(`publish:${templateId}`);

            const updated =
                await publishAutomationTemplateVersion(
                    templateId,
                    file,
                );

            replaceTemplate(updated);

            setSuccess(
                `Nova versão v${updated.current_version} publicada e definida como atual.`
            );

            return true;

        } catch (err) {
            setError(
                getApiErrorMessage(
                    err,
                    "Não foi possível publicar a nova versão.",
                )
            );

            return false;

        } finally {
            setBusyAction(null);
        }
    };


    // ========================================================
    // METADADOS
    // ========================================================

    const saveMetadata = async (
        templateId: number,
        name: string,
        description: string,
    ): Promise<boolean> => {
        try {
            clearFeedback();
            setBusyAction(`metadata:${templateId}`);

            const updated =
                await updateAutomationTemplate(
                    templateId,
                    {
                        name: name.trim(),

                        // String vazia é enviada de propósito.
                        // O backend a converte para NULL e permite
                        // remover uma descrição já existente.
                        description:
                            description.trim(),
                    },
                );

            replaceTemplate(updated);
            setSuccess("Template atualizado com sucesso.");

            return true;

        } catch (err) {
            setError(
                getApiErrorMessage(
                    err,
                    "Não foi possível atualizar o Template.",
                )
            );

            return false;

        } finally {
            setBusyAction(null);
        }
    };


    // ========================================================
    // ATIVAR / DESATIVAR
    // ========================================================

    const setTemplateActive = async (
        templateId: number,
        active: boolean,
    ): Promise<boolean> => {
        try {
            clearFeedback();
            setBusyAction(`active:${templateId}`);

            const updated =
                await updateAutomationTemplate(
                    templateId,
                    {
                        is_active: active,
                    },
                );

            replaceTemplate(updated);

            setSuccess(
                active
                    ? "Template reativado."
                    : "Template desativado para novos projetos."
            );

            return true;

        } catch (err) {
            setError(
                getApiErrorMessage(
                    err,
                    "Não foi possível alterar o status do Template.",
                )
            );

            return false;

        } finally {
            setBusyAction(null);
        }
    };


    // ========================================================
    // DEFINIR VERSÃO ATUAL
    // ========================================================

    const setCurrentVersion = async (
        templateId: number,
        versionId: number,
    ): Promise<boolean> => {
        try {
            clearFeedback();
            setBusyAction(
                `current:${templateId}:${versionId}`
            );

            const updated =
                await setAutomationTemplateCurrentVersion(
                    templateId,
                    versionId,
                );

            replaceTemplate(updated);

            setSuccess(
                `A versão v${updated.current_version} agora é a versão atual do Template.`
            );

            return true;

        } catch (err) {
            setError(
                getApiErrorMessage(
                    err,
                    "Não foi possível definir a versão atual.",
                )
            );

            return false;

        } finally {
            setBusyAction(null);
        }
    };


    // ========================================================
    // DOWNLOAD
    // ========================================================

    const downloadVersion = async (
        template: AutomationTemplate,
        version: AutomationTemplateVersion,
    ): Promise<void> => {
        try {
            clearFeedback();
            setBusyAction(
                `download:${template.id}:${version.id}`
            );

            const blob =
                await downloadAutomationTemplateVersion(
                    template.id,
                    version.id,
                );

            const url =
                window.URL.createObjectURL(blob);

            const link =
                document.createElement("a");

            const safeName =
                template.name
                    .trim()
                    .replace(/[^a-zA-Z0-9._-]+/g, "_") ||
                `template_${template.id}`;

            link.href = url;
            link.download =
                `${safeName}_v${version.version}.zip`;

            document.body.appendChild(link);
            link.click();
            link.remove();

            window.URL.revokeObjectURL(url);

        } catch (err) {
            setError(
                getApiErrorMessage(
                    err,
                    "Não foi possível baixar a versão do Template.",
                )
            );

        } finally {
            setBusyAction(null);
        }
    };


    return {
        templates,
        loading,
        busyAction,
        error,
        success,

        clearFeedback,
        reloadTemplates,
        createTemplate,
        publishVersion,
        saveMetadata,
        setTemplateActive,
        setCurrentVersion,
        downloadVersion,
    };
}

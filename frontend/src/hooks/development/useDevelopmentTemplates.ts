// ============================================================
// USE DEVELOPMENT TEMPLATES
// ============================================================
//
// Responsabilidade:
//     Controla a seleção de Template dentro do formulário de
//     criação de AutomationProject.
//
// O hook:
//     - carrega Templates disponíveis;
//     - mantém o Template selecionado;
//     - seleciona automaticamente a versão atual;
//     - permite escolher uma versão anterior conscientemente;
//     - não cria projetos e não altera Templates.
// ============================================================

import {
    useEffect,
    useMemo,
    useState,
} from "react";


import {
    getAvailableAutomationTemplates,
} from "../../services/developmentApi";


import {
    getApiErrorMessage,
} from "../../utils/apiErrors";


import type {
    AutomationTemplate,
    AutomationTemplateVersion,
} from "../../types/development";


interface UseDevelopmentTemplatesResult {

    templates:
        AutomationTemplate[];

    loadingTemplates:
        boolean;

    templatesError:
        string;

    selectedTemplateId:
        string;

    selectedTemplateVersionId:
        string;

    selectedTemplate:
        AutomationTemplate | null;

    selectedTemplateVersion:
        AutomationTemplateVersion | null;

    selectTemplate:
        (templateId: string) => void;

    selectTemplateVersion:
        (versionId: string) => void;
}


function useDevelopmentTemplates(
    enabled: boolean
): UseDevelopmentTemplatesResult {

    const [
        templates,
        setTemplates,
    ] =
        useState<AutomationTemplate[]>(
            []
        );


    const [
        loadingTemplates,
        setLoadingTemplates,
    ] =
        useState(false);


    const [
        templatesError,
        setTemplatesError,
    ] =
        useState("");


    const [
        selectedTemplateId,
        setSelectedTemplateId,
    ] =
        useState("");


    const [
        selectedTemplateVersionId,
        setSelectedTemplateVersionId,
    ] =
        useState("");


    // ========================================================
    // TEMPLATE SELECIONADO
    // ========================================================

    const selectedTemplate =
        useMemo(
            () =>
                templates.find(
                    (template) =>
                        String(
                            template.id
                        ) ===
                        selectedTemplateId
                ) ??
                null,
            [
                templates,
                selectedTemplateId,
            ]
        );


    // ========================================================
    // VERSÃO SELECIONADA
    // ========================================================

    const selectedTemplateVersion =
        useMemo(
            () =>
                selectedTemplate
                    ?.versions
                    .find(
                        (version) =>
                            String(
                                version.id
                            ) ===
                            selectedTemplateVersionId
                    ) ??
                null,
            [
                selectedTemplate,
                selectedTemplateVersionId,
            ]
        );


    // ========================================================
    // CARREGAR TEMPLATES
    // ========================================================

    useEffect(
        () => {

            if (!enabled) {

                setSelectedTemplateId(
                    ""
                );

                setSelectedTemplateVersionId(
                    ""
                );

                return;
            }


            let active =
                true;


            setLoadingTemplates(
                true
            );

            setTemplatesError(
                ""
            );


            getAvailableAutomationTemplates()
                .then(
                    (
                        result
                    ) => {

                        if (!active) {
                            return;
                        }


                        setTemplates(
                            result
                        );
                    }
                )
                .catch(
                    (
                        error
                    ) => {

                        if (!active) {
                            return;
                        }


                        setTemplates(
                            []
                        );

                        setTemplatesError(
                            getApiErrorMessage(
                                error,
                                "Não foi possível carregar os Templates."
                            )
                        );
                    }
                )
                .finally(
                    () => {

                        if (!active) {
                            return;
                        }


                        setLoadingTemplates(
                            false
                        );
                    }
                );


            return () => {

                active =
                    false;
            };
        },
        [
            enabled,
        ]
    );


    // ========================================================
    // SELECIONAR TEMPLATE
    // ========================================================

    const selectTemplate =
        (
            templateId: string
        ) => {

            setSelectedTemplateId(
                templateId
            );


            const template =
                templates.find(
                    (item) =>
                        String(
                            item.id
                        ) ===
                        templateId
                );


            // Sempre que o usuário escolhe um Template,
            // a versão atual vem selecionada por padrão.
            setSelectedTemplateVersionId(
                template
                    ?.current_version_id
                    ? String(
                        template.current_version_id
                    )
                    : ""
            );
        };


    // ========================================================
    // SELECIONAR VERSÃO
    // ========================================================

    const selectTemplateVersion =
        (
            versionId: string
        ) => {

            setSelectedTemplateVersionId(
                versionId
            );
        };


    return {
        templates,
        loadingTemplates,
        templatesError,

        selectedTemplateId,
        selectedTemplateVersionId,

        selectedTemplate,
        selectedTemplateVersion,

        selectTemplate,
        selectTemplateVersion,
    };
}


export default useDevelopmentTemplates;

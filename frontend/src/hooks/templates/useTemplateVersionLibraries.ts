// ============================================================
// USE TEMPLATE VERSION LIBRARIES
// ============================================================
//
// Responsabilidade:
//     Carregar e manter em cache o snapshot de Libraries de uma
//     AutomationTemplateVersion já publicada.
//
// Uso principal:
//     - histórico de versões;
//     - preparação da tela de "Nova versão", que começa exatamente
//       com a composição da versão atualmente marcada como Atual.
//
// Este arquivo NÃO renderiza interface.
// ============================================================

import {
    useCallback,
    useRef,
    useState,
} from "react";

import {
    getAutomationTemplateVersionLibraries,
} from "../../services/developmentApi";

import {
    getApiErrorMessage,
} from "../../utils/apiErrors";

import type {
    TemplateVersionLibraryDependency,
} from "../../types/development";


// ============================================================
// CONTRATO PÚBLICO
// ============================================================

interface UseTemplateVersionLibrariesResult {
    librariesByVersionId: Record<
        number,
        TemplateVersionLibraryDependency[]
    >;

    errorsByVersionId: Record<
        number,
        string
    >;

    isLoading: (
        versionId: number,
    ) => boolean;

    loadVersionLibraries: (
        templateId: number,
        versionId: number,
    ) => Promise<TemplateVersionLibraryDependency[] | null>;
}


// ============================================================
// HOOK
// ============================================================

export function useTemplateVersionLibraries():
    UseTemplateVersionLibrariesResult {

    const [librariesByVersionId, setLibrariesByVersionId] =
        useState<Record<
            number,
            TemplateVersionLibraryDependency[]
        >>({});

    const cacheRef =
        useRef<Record<
            number,
            TemplateVersionLibraryDependency[]
        >>({});

    const pendingRef =
        useRef<Record<
            number,
            Promise<TemplateVersionLibraryDependency[] | null>
        >>({});

    const [loadingIds, setLoadingIds] =
        useState<Set<number>>(
            () => new Set<number>()
        );

    const [errorsByVersionId, setErrorsByVersionId] =
        useState<Record<number, string>>({});


    // ========================================================
    // CARREGAMENTO SOB DEMANDA
    // ========================================================

    const loadVersionLibraries = useCallback(
        async (
            templateId: number,
            versionId: number,
        ): Promise<TemplateVersionLibraryDependency[] | null> => {

            const cached =
                cacheRef.current[versionId];

            if (cached) {
                return cached;
            }

            const pending =
                pendingRef.current[versionId];

            if (pending) {
                return pending;
            }

            setLoadingIds((current) => {
                const next = new Set(current);
                next.add(versionId);
                return next;
            });

            setErrorsByVersionId((current) => {
                if (!(versionId in current)) {
                    return current;
                }

                const next = {
                    ...current,
                };

                delete next[versionId];
                return next;
            });

            const request = (
                async () => {
                    try {
                        const response =
                            await getAutomationTemplateVersionLibraries(
                                templateId,
                                versionId,
                            );

                        const libraries =
                            response.libraries || [];

                        cacheRef.current = {
                            ...cacheRef.current,
                            [versionId]: libraries,
                        };

                        setLibrariesByVersionId((current) => ({
                            ...current,
                            [versionId]: libraries,
                        }));

                        return libraries;

                    } catch (error) {
                        const message =
                            getApiErrorMessage(
                                error,
                                "Não foi possível carregar as Libraries desta versão.",
                            );

                        setErrorsByVersionId((current) => ({
                            ...current,
                            [versionId]: message,
                        }));

                        return null;

                    } finally {
                        delete pendingRef.current[
                            versionId
                        ];

                        setLoadingIds((current) => {
                            const next = new Set(current);
                            next.delete(versionId);
                            return next;
                        });
                    }
                }
            )();

            pendingRef.current[versionId] = request;

            return request;
        },
        [],
    );


    const isLoading = useCallback(
        (
            versionId: number,
        ) => loadingIds.has(versionId),
        [loadingIds],
    );


    return {
        librariesByVersionId,
        errorsByVersionId,
        isLoading,
        loadVersionLibraries,
    };
}

// ============================================================
// USE TEMPLATE LIBRARY CATALOG
// ============================================================
//
// Responsabilidade:
//     Fornecer ao seletor de Libraries dos Templates uma visão
//     simples do catálogo global já existente no DUET.
//
// Este hook:
//     - carrega o catálogo incluindo identidades arquivadas para que
//       snapshots históricos continuem representáveis;
//     - achata a árvore de pastas para seleção;
//     - carrega versões sob demanda;
//     - mantém cache por Library para evitar chamadas repetidas.
//
// Este arquivo NÃO renderiza interface e NÃO conhece URLs HTTP.
// ============================================================

import {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
} from "react";

import {
    getLibrariesTree,
    getLibraryVersions,
} from "../../components/libraries/services/librariesApi";

import type {
    LibraryCatalogItem,
    LibraryTreeNode,
    LibraryVersionItem,
} from "../../components/libraries/types/libraries";

import {
    getApiErrorMessage,
} from "../../utils/apiErrors";


// ============================================================
// AUXILIAR - ACHATA A ÁRVORE DO CATÁLOGO
// ============================================================

function flattenLibraries(
    nodes: LibraryTreeNode[],
): LibraryCatalogItem[] {
    const result: LibraryCatalogItem[] = [];

    const visit = (
        items: LibraryTreeNode[],
    ) => {
        for (const item of items) {
            if (item.type === "library") {
                result.push(item);
                continue;
            }

            visit(item.children || []);
        }
    };

    visit(nodes);

    return result.sort((left, right) =>
        left.name.localeCompare(
            right.name,
            "pt-BR",
        )
    );
}


// ============================================================
// CONTRATO PÚBLICO
// ============================================================

interface UseTemplateLibraryCatalogResult {
    libraries: LibraryCatalogItem[];
    loadingCatalog: boolean;
    catalogError: string;

    versionsByLibraryId: Record<
        number,
        LibraryVersionItem[]
    >;

    isLoadingVersions: (
        libraryId: number,
    ) => boolean;

    loadVersions: (
        libraryId: number,
    ) => Promise<LibraryVersionItem[]>;
}


// ============================================================
// HOOK
// ============================================================

export function useTemplateLibraryCatalog():
    UseTemplateLibraryCatalogResult {

    const [tree, setTree] =
        useState<LibraryTreeNode[]>([]);

    const [loadingCatalog, setLoadingCatalog] =
        useState(true);

    const [catalogError, setCatalogError] =
        useState("");

    const [versionsByLibraryId, setVersionsByLibraryId] =
        useState<Record<number, LibraryVersionItem[]>>({});

    const versionsRef =
        useRef<Record<number, LibraryVersionItem[]>>({});

    const requestsRef =
        useRef<Record<number, Promise<LibraryVersionItem[]>>>({});

    const [loadingVersionIds, setLoadingVersionIds] =
        useState<Set<number>>(
            () => new Set<number>()
        );


    // ========================================================
    // CATÁLOGO
    // ========================================================

    useEffect(() => {
        let active = true;

        const loadCatalog = async () => {
            try {
                setLoadingCatalog(true);
                setCatalogError("");

                const response =
                    await getLibrariesTree(true);

                if (!active) {
                    return;
                }

                setTree(response.tree || []);

            } catch (error) {
                if (!active) {
                    return;
                }

                setTree([]);
                setCatalogError(
                    getApiErrorMessage(
                        error,
                        "Não foi possível carregar o catálogo de Libraries.",
                    )
                );

            } finally {
                if (active) {
                    setLoadingCatalog(false);
                }
            }
        };

        void loadCatalog();

        return () => {
            active = false;
        };
    }, []);


    // ========================================================
    // VERSÕES SOB DEMANDA
    // ========================================================

    const loadVersions = useCallback(
        async (
            libraryId: number,
        ): Promise<LibraryVersionItem[]> => {

            const cached =
                versionsRef.current[libraryId];

            if (cached) {
                return cached;
            }

            const pending =
                requestsRef.current[libraryId];

            if (pending) {
                return pending;
            }

            setLoadingVersionIds((current) => {
                const next = new Set(current);
                next.add(libraryId);
                return next;
            });

            const request = (
                async () => {
                    try {
                        // includeInactive=true é proposital.
                        // Uma versão histórica já fixada em um Template
                        // precisa continuar visível, embora não possa ser
                        // escolhida para um novo vínculo se estiver inativa.
                        const response =
                            await getLibraryVersions(
                                libraryId,
                                true,
                            );

                        const versions =
                            response.versions || [];

                        versionsRef.current = {
                            ...versionsRef.current,
                            [libraryId]: versions,
                        };

                        setVersionsByLibraryId((current) => ({
                            ...current,
                            [libraryId]: versions,
                        }));

                        return versions;

                    } finally {
                        delete requestsRef.current[
                            libraryId
                        ];

                        setLoadingVersionIds((current) => {
                            const next = new Set(current);
                            next.delete(libraryId);
                            return next;
                        });
                    }
                }
            )();

            requestsRef.current[libraryId] = request;

            return request;
        },
        [],
    );


    const libraries = useMemo(
        () => flattenLibraries(tree),
        [tree],
    );


    const isLoadingVersions = useCallback(
        (
            libraryId: number,
        ) => loadingVersionIds.has(libraryId),
        [loadingVersionIds],
    );


    return {
        libraries,
        loadingCatalog,
        catalogError,
        versionsByLibraryId,
        isLoadingVersions,
        loadVersions,
    };
}

// ============================================================
// DUET CORE - ROBOT STUDIO - LIBRARY CHECKOUT
// ============================================================
//
// Mantém o Checkout global das Libraries usadas dentro do Studio.
// O Checkout do AutomationProject continua sendo controlado por
// useRobotStudioCheckout e não é substituído por este hook.
// ============================================================

import {
    useCallback,
    useEffect,
    useMemo,
    useState,
    type Dispatch,
    type SetStateAction,
} from "react";

import {
    checkinLibrary,
    checkoutLibrary,
    getLibraryCheckoutOverview,
} from "../../services/libraryCheckoutApi";

import type {
    LibraryCheckoutState,
} from "../../services/libraryCheckoutApi";

import {
    getApiErrorMessage,
} from "../../utils/apiErrors";


interface UseRobotStudioLibraryCheckoutParams {
    projectId?: string;
    enabled: boolean;
    canWriteWorkspace: boolean;
    dirtyFiles: Set<string>;
    setOutputLines: Dispatch<SetStateAction<string[]>>;
}


const namespaceFromPath = (
    path?: string | null
): string | null => {
    if (!path) return null;

    const normalized = path
        .replace(/\\/g, "/")
        .replace(/^\/+|\/+$/g, "");

    const match = normalized.match(
        /^_libraries\/([^/]+)/
    );

    return match?.[1] || null;
};


export function useRobotStudioLibraryCheckout({
    projectId,
    enabled,
    canWriteWorkspace,
    dirtyFiles,
    setOutputLines,
}: UseRobotStudioLibraryCheckoutParams) {

    const [states, setStates] = useState<LibraryCheckoutState[]>([]);
    const [loading, setLoading] = useState(false);
    const [overviewLoaded, setOverviewLoaded] = useState(false);
    const [actionLibraryId, setActionLibraryId] = useState<number | null>(null);


    const refresh = useCallback(async (
        silent = false
    ) => {
        if (!projectId || !enabled) {
            setStates([]);
            setOverviewLoaded(false);
            return;
        }

        try {
            if (!silent) {
                setLoading(true);
            }

            const response =
                await getLibraryCheckoutOverview(
                    Number(projectId)
                );

            setStates(
                Array.isArray(response.libraries)
                    ? response.libraries
                    : []
            );
            setOverviewLoaded(true);
        } catch (error: unknown) {
            // Fail closed também para o Terminal, que trabalha
            // diretamente no filesystem do Workspace.
            setOverviewLoaded(false);
            if (!silent) {
                setOutputLines((current) => [
                    ...current,
                    `[DUET] ${getApiErrorMessage(
                        error,
                        "Não foi possível consultar o Checkout das bibliotecas."
                    )}`,
                ]);
            }
        } finally {
            if (!silent) {
                setLoading(false);
            }
        }
    }, [
        projectId,
        enabled,
        setOutputLines,
    ]);


    useEffect(() => {
        void refresh(false);
    }, [refresh]);


    useEffect(() => {
        if (!projectId || !enabled) return;

        const timer = window.setInterval(() => {
            void refresh(true);
        }, 5000);

        return () => {
            window.clearInterval(timer);
        };
    }, [
        projectId,
        enabled,
        refresh,
    ]);


    const statesByNamespace = useMemo(() => {
        const result: Record<string, LibraryCheckoutState> = {};

        states.forEach((state) => {
            result[state.import_name] = state;
        });

        return result;
    }, [states]);


    const getStateForPath = useCallback((
        path?: string | null
    ): LibraryCheckoutState | null => {
        const namespace = namespaceFromPath(path);

        if (!namespace) return null;

        return statesByNamespace[namespace] || null;
    }, [statesByNamespace]);


    const getStateForNamespace = useCallback((
        namespace: string
    ): LibraryCheckoutState | null => {
        return statesByNamespace[namespace] || null;
    }, [statesByNamespace]);


    const canWritePath = useCallback((
        path?: string | null
    ): boolean => {
        if (!canWriteWorkspace) {
            return false;
        }

        const normalized = (path || "")
            .replace(/\\/g, "/")
            .replace(/^\/+|\/+$/g, "");

        // _libraries é apenas o container técnico. Arquivos/pastas
        // de código só podem ser criados dentro de uma Library real.
        if (normalized === "_libraries") {
            return false;
        }

        const namespace = namespaceFromPath(path);

        if (!namespace) {
            return true;
        }

        // Fail closed: enquanto o overview ainda não carregou,
        // uma Library permanece somente leitura.
        return statesByNamespace[namespace]
            ?.owns_checkout === true;
    }, [
        canWriteWorkspace,
        statesByNamespace,
    ]);


    const readOnlyMessageForPath = useCallback((
        path?: string | null,
        workspaceMessage?: string
    ): string => {
        if (!canWriteWorkspace) {
            return workspaceMessage ||
                "Faça Checkout do projeto para editar.";
        }

        const state = getStateForPath(path);

        if (!state) {
            return "Faça Checkout da biblioteca para editar seus arquivos.";
        }

        if (state.owns_checkout) {
            return "";
        }

        if (state.checked_out) {
            const owner =
                state.checkout?.user_name ||
                "outro usuário";

            return `Biblioteca em edição por ${owner}.`;
        }

        return "Faça Checkout da biblioteca para editar seus arquivos.";
    }, [
        canWriteWorkspace,
        getStateForPath,
    ]);


    const performCheckout = useCallback(async (
        libraryId: number
    ) => {
        if (!projectId || !canWriteWorkspace) {
            return;
        }

        try {
            setActionLibraryId(libraryId);

            const state = await checkoutLibrary(
                Number(projectId),
                libraryId
            );

            setStates((current) => {
                const exists = current.some(
                    (item) => item.library_id === libraryId
                );

                if (!exists) {
                    return [...current, state];
                }

                return current.map((item) =>
                    item.library_id === libraryId
                        ? state
                        : item
                );
            });

            setOutputLines((current) => [
                ...current,
                `[DUET] Checkout da biblioteca ${state.library_name} adquirido.`,
            ]);
        } catch (error: unknown) {
            setOutputLines((current) => [
                ...current,
                `[DUET] ${getApiErrorMessage(
                    error,
                    "Não foi possível fazer Checkout da biblioteca."
                )}`,
            ]);

            await refresh(true);
        } finally {
            setActionLibraryId(null);
        }
    }, [
        projectId,
        canWriteWorkspace,
        refresh,
        setOutputLines,
    ]);


    const performCheckin = useCallback(async (
        libraryId: number
    ) => {
        if (!projectId) return;

        const state = states.find(
            (item) => item.library_id === libraryId
        );

        if (!state?.owns_checkout) {
            return;
        }

        const namespaceRoot =
            `_libraries/${state.import_name}`;

        const hasDirtyFiles = Array.from(
            dirtyFiles
        ).some((path) =>
            path === namespaceRoot ||
            path.startsWith(`${namespaceRoot}/`)
        );

        if (hasDirtyFiles) {
            setOutputLines((current) => [
                ...current,
                `[DUET] CHECK-IN DA LIBRARY BLOQUEADO: salve as alterações de ${state.library_name} antes de liberar o Checkout.`,
            ]);
            return;
        }

        try {
            setActionLibraryId(libraryId);

            const nextState = await checkinLibrary(
                Number(projectId),
                libraryId
            );

            setStates((current) =>
                current.map((item) =>
                    item.library_id === libraryId
                        ? nextState
                        : item
                )
            );

            setOutputLines((current) => [
                ...current,
                `[DUET] Check-in da biblioteca ${state.library_name} realizado. O draft foi preservado e nenhuma versão foi publicada.`,
            ]);
        } catch (error: unknown) {
            setOutputLines((current) => [
                ...current,
                `[DUET] ${getApiErrorMessage(
                    error,
                    "Não foi possível fazer Check-in da biblioteca."
                )}`,
            ]);

            await refresh(true);
        } finally {
            setActionLibraryId(null);
        }
    }, [
        projectId,
        states,
        dirtyFiles,
        refresh,
        setOutputLines,
    ]);


    const hasOwnedCheckouts = states.some(
        (state) => state.owns_checkout
    );

    const allLibrariesOwnedForTerminal =
        enabled &&
        overviewLoaded &&
        states.every(
            (state) => state.owns_checkout
        );


    return {
        states,
        loading,
        overviewLoaded,
        allLibrariesOwnedForTerminal,
        actionLibraryId,
        hasOwnedCheckouts,
        refresh,
        getStateForPath,
        getStateForNamespace,
        canWritePath,
        readOnlyMessageForPath,
        performCheckout,
        performCheckin,
    };
}

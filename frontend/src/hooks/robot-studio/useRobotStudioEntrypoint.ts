// ============================================================
// DUET CORE - ROBOT STUDIO - PROJECT ENTRYPOINT
// ============================================================
// Mantém a configuração do arquivo de entrada fora da página.
// Alterar entrypoint não adquire Checkout: o backend exige que o
// usuário já seja o proprietário do Checkout do projeto.
// ============================================================

import {
    useCallback,
    useEffect,
    useMemo,
    useRef,
    useState,
    type Dispatch,
    type SetStateAction,
} from "react";

import type { StudioNode } from "../../types/robotStudio";
import {
    getProjectEntrypoint,
    updateProjectEntrypoint,
    type ProjectEntrypointState,
} from "../../services/projectEntrypointApi";

interface UseRobotStudioEntrypointParams {
    projectId?: string;
    canWriteWorkspace: boolean;
    workspace: StudioNode[];
    openFile: (node: StudioNode) => void | Promise<void>;
    closeTab: (fileId: string) => void;
    setOutputLines: Dispatch<SetStateAction<string[]>>;
}

function findNodeByPath(
    nodes: StudioNode[],
    path: string
): StudioNode | null {
    for (const node of nodes) {
        if (node.id === path) return node;

        if (node.children?.length) {
            const child = findNodeByPath(
                node.children,
                path
            );

            if (child) return child;
        }
    }

    return null;
}

function collectPythonFiles(
    nodes: StudioNode[]
): string[] {
    const paths: string[] = [];

    const visit = (
        currentNodes: StudioNode[]
    ) => {
        for (const node of currentNodes) {
            if (
                node.type === "file" &&
                node.id.toLowerCase().endsWith(".py")
            ) {
                paths.push(node.id);
            }

            if (node.children?.length) {
                visit(node.children);
            }
        }
    };

    visit(nodes);

    return paths.sort((left, right) =>
        left.localeCompare(
            right,
            undefined,
            { sensitivity: "base" }
        )
    );
}

export function useRobotStudioEntrypoint({
    projectId,
    canWriteWorkspace,
    workspace,
    openFile,
    closeTab,
    setOutputLines,
}: UseRobotStudioEntrypointParams) {
    const [state, setState] =
        useState<ProjectEntrypointState | null>(null);

    const [loading, setLoading] =
        useState(false);

    const [saving, setSaving] =
        useState(false);

    const openedKeyRef =
        useRef<string>("");

    // A lista é derivada da árvore atual do Workspace para que novos
    // arquivos .py apareçam imediatamente sem depender de outro GET.
    const pythonFiles = useMemo(
        () => collectPythonFiles(workspace),
        [workspace]
    );

    const load = useCallback(async () => {
        if (!projectId) return;

        try {
            setLoading(true);

            const current =
                await getProjectEntrypoint(
                    projectId
                );

            setState(current);
        } catch (error) {
            console.error(
                "Erro ao consultar entrypoint do projeto:",
                error
            );

            setOutputLines((current) => [
                ...current,
                "[DUET] Não foi possível consultar o arquivo de entrada do projeto.",
            ]);
        } finally {
            setLoading(false);
        }
    }, [projectId, setOutputLines]);

    useEffect(() => {
        openedKeyRef.current = "";
        setState(null);
        void load();
    }, [load]);

    // Após o Workspace carregar, seleciona o entrypoint configurado.
    // Projetos legados continuam usando main.py por padrão.
    useEffect(() => {
        if (
            !projectId ||
            !state ||
            !state.exists ||
            workspace.length === 0
        ) {
            return;
        }

        const key =
            `${projectId}:${state.entrypoint_path}`;

        if (openedKeyRef.current === key) {
            return;
        }

        const node = findNodeByPath(
            workspace,
            state.entrypoint_path
        );

        if (
            !node ||
            node.type !== "file"
        ) {
            return;
        }

        openedKeyRef.current = key;

        void Promise.resolve(
            openFile(node)
        ).then(() => {
            // O Workspace legado ainda pode abrir main.py inicialmente.
            // Quando o entrypoint é outro, removemos essa aba automática
            // para que main.py deixe de ter tratamento visual especial.
            if (
                state.entrypoint_path !== "main.py"
            ) {
                closeTab("main.py");
            }
        });
    }, [
        projectId,
        state,
        workspace,
        openFile,
        closeTab,
    ]);

    const changeEntrypoint = useCallback(
        async (
            entrypointPath: string
        ) => {
            if (
                !projectId ||
                !canWriteWorkspace ||
                saving
            ) {
                return;
            }

            try {
                setSaving(true);

                const updated =
                    await updateProjectEntrypoint(
                        projectId,
                        entrypointPath
                    );

                openedKeyRef.current = "";
                setState(updated);

                setOutputLines((current) => [
                    ...current,
                    `[DUET] Arquivo de entrada alterado para ${updated.entrypoint_path}.`,
                ]);
            } catch (error: any) {
                console.error(
                    "Erro ao alterar entrypoint do projeto:",
                    error
                );

                const message =
                    error?.response?.data?.detail ||
                    error?.response?.data?.message ||
                    "Não foi possível alterar o arquivo de entrada.";

                setOutputLines((current) => [
                    ...current,
                    `[DUET] ENTRYPOINT: ${
                        typeof message === "string"
                            ? message
                            : JSON.stringify(message)
                    }`,
                ]);
            } finally {
                setSaving(false);
            }
        },
        [
            projectId,
            canWriteWorkspace,
            saving,
            setOutputLines,
        ]
    );

    return {
        state,
        loading,
        saving,
        pythonFiles,
        load,
        changeEntrypoint,
    };
}

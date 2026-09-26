import { useEffect, useEffectEvent } from "react";

interface PollingTaskOptions {
    enabled?: boolean;
    intervalMs: number;
    refreshWhenVisible?: boolean;
}

/**
 * Executa uma consulta imediatamente e agenda a próxima somente depois que a
 * atual termina. Isso impede sobreposição quando a API demora mais que o
 * intervalo e pausa tráfego desnecessário em abas ocultas.
 */
export function usePollingTask(
    task: (signal: AbortSignal) => void | Promise<void>,
    {
        enabled = true,
        intervalMs,
        refreshWhenVisible = true,
    }: PollingTaskOptions,
) {
    const runLatestTask = useEffectEvent(task);

    useEffect(() => {
        if (!enabled) {
            return;
        }

        let disposed = false;
        let running = false;
        let timer: number | undefined;
        let controller: AbortController | undefined;

        const clearTimer = () => {
            if (timer !== undefined) {
                window.clearTimeout(timer);
                timer = undefined;
            }
        };

        const schedule = () => {
            clearTimer();

            if (!disposed && document.visibilityState === "visible") {
                timer = window.setTimeout(run, intervalMs);
            }
        };

        const run = async () => {
            if (disposed || running || document.visibilityState === "hidden") {
                return;
            }

            running = true;
            controller = new AbortController();

            try {
                await runLatestTask(controller.signal);
            } finally {
                running = false;
                controller = undefined;
                schedule();
            }
        };

        const handleVisibilityChange = () => {
            if (document.visibilityState === "hidden") {
                clearTimer();
                return;
            }

            if (refreshWhenVisible) {
                void run();
            } else {
                schedule();
            }
        };

        const handleOnline = () => {
            void run();
        };

        document.addEventListener("visibilitychange", handleVisibilityChange);
        window.addEventListener("online", handleOnline);
        void run();

        return () => {
            disposed = true;
            clearTimer();
            controller?.abort();
            document.removeEventListener("visibilitychange", handleVisibilityChange);
            window.removeEventListener("online", handleOnline);
        };
    }, [enabled, intervalMs, refreshWhenVisible]);
}

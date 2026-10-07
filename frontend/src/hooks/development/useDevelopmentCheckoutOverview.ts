import { useCallback, useEffect, useState } from "react";

import api from "../../services/api";

export interface ProjectCheckoutOverview {
    project_id: number;
    checked_out: boolean;
    owns_checkout: boolean;
    checkout: {
        id: number;
        project_id: number;
        user_id: number;
        user_name: string | null;
        checked_out_at: string | null;
    } | null;
}

export type ProjectCheckoutOverviewMap =
    Record<number, ProjectCheckoutOverview>;

interface UseDevelopmentCheckoutOverviewParams {
    enabled: boolean;
}

function useDevelopmentCheckoutOverview({
    enabled,
}: UseDevelopmentCheckoutOverviewParams) {

    const [checkoutStates, setCheckoutStates] =
        useState<ProjectCheckoutOverviewMap>({});

    const [loadingCheckoutStates, setLoadingCheckoutStates] =
        useState(false);

    const refreshCheckoutStates = useCallback(async () => {
        if (!enabled) {
            return;
        }

        try {
            setLoadingCheckoutStates(true);

            const response = await api.get(
                "/development/checkout/projects/states"
            );

            const raw = response.data?.projects || {};
            const normalized: ProjectCheckoutOverviewMap = {};

            Object.entries(raw).forEach(([projectId, value]) => {
                normalized[Number(projectId)] =
                    value as ProjectCheckoutOverview;
            });

            setCheckoutStates(normalized);
        } catch (error) {
            // Não apagamos o último estado conhecido em erro transitório.
            console.error(
                "Erro ao atualizar estados de Checkout dos projetos:",
                error
            );
        } finally {
            setLoadingCheckoutStates(false);
        }
    }, [enabled]);

    useEffect(() => {
        if (!enabled) {
            setCheckoutStates({});
            return;
        }

        void refreshCheckoutStates();

        const intervalId = window.setInterval(() => {
            void refreshCheckoutStates();
        }, 5000);

        return () => {
            window.clearInterval(intervalId);
        };
    }, [enabled, refreshCheckoutStates]);

    return {
        checkoutStates,
        loadingCheckoutStates,
        refreshCheckoutStates,
    };
}

export default useDevelopmentCheckoutOverview;

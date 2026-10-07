import { useState } from "react";

import api from "../../services/api";
import { getApiErrorMessage } from "../../utils/apiErrors";
import type { DevelopmentProject } from "../../types/development";

export interface ProjectCheckoutHistoryEvent {
    id: number;
    project_id: number | null;
    project_name: string;
    event_type: "checkout" | "checkin" | "force_release";
    actor_user_id: number | null;
    actor_user_name: string;
    checkout_owner_user_id: number | null;
    checkout_owner_user_name: string;
    checkout_started_at: string | null;
    occurred_at: string | null;
}

function useProjectCheckoutHistory() {
    const [checkoutHistoryProject, setCheckoutHistoryProject] =
        useState<DevelopmentProject | null>(null);

    const [checkoutHistoryEvents, setCheckoutHistoryEvents] =
        useState<ProjectCheckoutHistoryEvent[]>([]);

    const [loadingCheckoutHistory, setLoadingCheckoutHistory] =
        useState(false);

    const [checkoutHistoryError, setCheckoutHistoryError] =
        useState("");

    const openCheckoutHistory = async (
        project: DevelopmentProject
    ) => {
        setCheckoutHistoryProject(project);
        setCheckoutHistoryEvents([]);
        setCheckoutHistoryError("");

        try {
            setLoadingCheckoutHistory(true);

            const response = await api.get(
                `/development/checkout/projects/${project.id}/history`
            );

            setCheckoutHistoryEvents(
                response.data?.events || []
            );
        } catch (error: any) {
            setCheckoutHistoryError(
                getApiErrorMessage(
                    error,
                    "Não foi possível carregar o histórico de Checkout."
                )
            );
        } finally {
            setLoadingCheckoutHistory(false);
        }
    };

    const closeCheckoutHistory = () => {
        setCheckoutHistoryProject(null);
        setCheckoutHistoryEvents([]);
        setCheckoutHistoryError("");
    };

    return {
        checkoutHistoryProject,
        checkoutHistoryEvents,
        loadingCheckoutHistory,
        checkoutHistoryError,
        openCheckoutHistory,
        closeCheckoutHistory,
    };
}

export default useProjectCheckoutHistory;

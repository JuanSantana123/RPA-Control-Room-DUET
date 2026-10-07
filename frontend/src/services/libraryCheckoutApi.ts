// ============================================================
// DUET CORE - LIBRARY CHECKOUT API CLIENT
// ============================================================

import api from "./api";

export interface LibraryCheckoutOwner {
    id: number;
    library_id: number;
    project_id: number;
    user_id: number;
    user_name: string | null;
    checked_out_at: string | null;
    updated_at: string | null;
}

export interface LibraryCheckoutState {
    library_id: number;
    library_name: string;
    import_name: string;
    checked_out: boolean;
    owns_checkout: boolean;
    checkout: LibraryCheckoutOwner | null;
}

export interface LibraryCheckoutOverviewResponse {
    status: string;
    project_id: number;
    libraries: LibraryCheckoutState[];
}

export async function getLibraryCheckoutOverview(
    projectId: number
): Promise<LibraryCheckoutOverviewResponse> {
    const response = await api.get(
        `/development/projects/${projectId}/libraries/checkout-overview`
    );

    return response.data;
}

export async function checkoutLibrary(
    projectId: number,
    libraryId: number
): Promise<LibraryCheckoutState> {
    const response = await api.post(
        `/development/projects/${projectId}/libraries/${libraryId}/checkout`
    );

    return response.data.state;
}

export async function checkinLibrary(
    projectId: number,
    libraryId: number
): Promise<LibraryCheckoutState> {
    const response = await api.post(
        `/development/projects/${projectId}/libraries/${libraryId}/checkin`
    );

    return response.data.state;
}

// ============================================================
// DUET CORE - EXTERNAL IDE API
// ============================================================
//
// Responsabilidade:
// - solicitar código de abertura ao Control Room;
// - disparar o protocolo local duet://;
// - não conhecer regras de Checkout/Workspace.
// ============================================================

import api from "./api";


export interface DeveloperIdeLaunchResponse {
    status: string;

    project: {
        id: number;
        name: string;
    };

    launch_code: string;
    launch_expires_at: string;
}


export async function createDeveloperIdeLaunch(
    projectId: number
): Promise<DeveloperIdeLaunchResponse> {

    const response =
        await api.post<DeveloperIdeLaunchResponse>(
            `/development/external-ide/projects/${projectId}/launch`
        );

    return response.data;
}


export function openDeveloperIdeProtocol(
    launch: DeveloperIdeLaunchResponse
): void {

    const server =
        String(
            api.defaults.baseURL || ""
        ).replace(
            /\/+$/,
            ""
        );

    if (!server) {
        throw new Error(
            "A URL do Control Room não está configurada."
        );
    }

    const params =
        new URLSearchParams({
            server,
            project_id:
                String(
                    launch.project.id
                ),
            project_name:
                launch.project.name,
            code:
                launch.launch_code,
        });

    // O protocolo é registrado localmente pelo
    // DUET Developer Tools.
    window.location.href =
        `duet://open?${params.toString()}`;
}

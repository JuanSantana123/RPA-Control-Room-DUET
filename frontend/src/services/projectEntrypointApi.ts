// ============================================================
// DUET CORE - PROJECT ENTRYPOINT API
// ============================================================

import api from "./api";

export interface ProjectEntrypointState {
    status: string;
    project_id: number;
    entrypoint_path: string;
    exists: boolean;
    valid: boolean;
    python_files: string[];
}

export async function getProjectEntrypoint(
    projectId: number | string
): Promise<ProjectEntrypointState> {
    const response = await api.get(
        `/development/projects/${projectId}/entrypoint`
    );
    return response.data as ProjectEntrypointState;
}

export async function updateProjectEntrypoint(
    projectId: number | string,
    entrypointPath: string
): Promise<ProjectEntrypointState> {
    const response = await api.put(
        `/development/projects/${projectId}/entrypoint`,
        {
            entrypoint_path: entrypointPath,
        }
    );
    return response.data as ProjectEntrypointState;
}

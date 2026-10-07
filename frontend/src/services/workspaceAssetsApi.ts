import api from "./api";


export interface WorkspaceAssetUploadResponse {
    status: string;
    project_id: number;
    path: string;
    filename: string;
    size: number;
}


export async function uploadWorkspaceAsset(
    projectId: string,
    targetPath: string,
    file: File
): Promise<WorkspaceAssetUploadResponse> {
    const formData = new FormData();

    formData.append(
        "target_path",
        targetPath
    );

    formData.append(
        "file",
        file
    );

    const response = await api.post(
        `/development/projects/${projectId}/workspace/assets`,
        formData
    );

    return response.data as WorkspaceAssetUploadResponse;
}


export async function downloadWorkspaceAsset(
    projectId: string,
    path: string
): Promise<Blob> {
    const response = await api.get(
        `/development/projects/${projectId}/workspace/assets`,
        {
            params: {
                path,
            },
            responseType: "blob",
        }
    );

    return response.data as Blob;
}

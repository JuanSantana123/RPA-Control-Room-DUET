// ============================================================
// DUET CORE - ROBOTS - PACKAGE API
// ============================================================
//
// Responsabilidade:
// - concentrar as chamadas HTTP relacionadas aos artefatos
//   publicados dos Robots;
// - listar o histórico imutável de versões;
// - obter o ZIP exato de uma versão publicada.
//
// Este módulo NÃO:
// - mantém estado React;
// - abre modais;
// - dispara download no navegador;
// - decide qual versão deve ser exportada.
// ============================================================

import api from "./api";

import type {
    RobotReleaseVersion,
    RobotVersionsResponse,
} from "../types/robots";


export async function listRobotVersions(
    robotId: number,
): Promise<RobotReleaseVersion[]> {
    const response = await api.get<RobotVersionsResponse>(
        `/robots/${robotId}/versions`,
    );

    return response.data.versions ?? [];
}


export async function downloadRobotVersion(
    robotId: number,
    version: number,
): Promise<Blob> {
    const response = await api.get(
        `/robots/${robotId}/versions/${version}/download`,
        {
            responseType: "blob",
        },
    );

    const contentTypeHeader = response.headers?.["content-type"];

    const contentType =
        typeof contentTypeHeader === "string"
            ? contentTypeHeader
            : "application/zip";

    return new Blob([response.data], {
        type: contentType,
    });
}

// ============================================================
// IMPORTAÇÃO DE PACOTE DUET
// ============================================================

export interface RobotImportResponse {
    status: string;
    message: string;

    robot: {
        id: number;
        name: string;
        version: number;
        folder_id: number | null;
        file_hash: string;
    };

    dependencies: number;
}


/**
 * Importa um pacote DUET para o Control Room.
 *
 * Diferente do upload tradicional, esta operação utiliza
 * /robots/import para que o backend regenere o manifesto
 * duet-release.json com a identidade local do Robot.
 */
export async function importRobotPackage(
    file: File,
    folderId: number | null,
): Promise<RobotImportResponse> {

    const formData = new FormData();

    formData.append(
        "file",
        file,
    );

    // NULL representa a Raiz de Robôs.
    if (folderId !== null) {
        formData.append(
            "folder_id",
            String(folderId),
        );
    }

    const response =
        await api.post<RobotImportResponse>(
            "/robots/import",
            formData,
        );

    return response.data;
}
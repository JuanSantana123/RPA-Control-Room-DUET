// ============================================================
// DUET CORE - ROBOTS - PACKAGE API
// ============================================================
//
// Responsabilidade:
// - concentrar chamadas HTTP dos artefatos publicados;
// - analisar ZIP antes da importação;
// - importar o ZIP com EntryPoint explícito;
// - listar e baixar RobotVersions.
//
// Este módulo NÃO mantém estado React e NÃO renderiza UI.
// ============================================================

import api from "./api";

import type {
    RobotReleaseVersion,
    RobotVersionsResponse,
} from "../types/robots";


// ============================================================
// VERSÕES PUBLICADAS
// ============================================================

export async function listRobotVersions(
    robotId: number,
): Promise<RobotReleaseVersion[]> {

    const response = await api.get<RobotVersionsResponse>(
        `/robots/${robotId}/versions`,
    );

    return response.data.versions ?? [];
}


// ============================================================
// DOWNLOAD / EXPORTAÇÃO
// ============================================================

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

    const contentTypeHeader =
        response.headers?.["content-type"];

    const contentType =
        typeof contentTypeHeader === "string"
            ? contentTypeHeader
            : "application/zip";

    return new Blob(
        [response.data],
        {
            type: contentType,
        },
    );
}


// ============================================================
// ANÁLISE DE IMPORTAÇÃO
// ============================================================

export interface RobotImportAnalysis {
    status: string;

    filename: string;

    python_files: string[];

    configured_entrypoint:
        string | null;

    suggested_entrypoint:
        string | null;

    entrypoint_locked:
        boolean;
}


/**
 * Analisa um ZIP sem criar Robot ou RobotVersion.
 *
 * O backend:
 * - valida a segurança do ZIP;
 * - localiza arquivos .py;
 * - verifica eventual duet-release.json;
 * - informa EntryPoint existente/sugerido.
 */
export async function analyzeRobotPackage(
    file: File,
): Promise<RobotImportAnalysis> {

    const formData =
        new FormData();

    formData.append(
        "file",
        file,
    );

    const response =
        await api.post<RobotImportAnalysis>(
            "/robots/import/analyze",
            formData,
        );

    return response.data;
}


// ============================================================
// IMPORTAÇÃO DEFINITIVA
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
 * Confirma a importação do pacote.
 *
 * Para ZIP comum, entrypointPath representa a escolha explícita
 * feita pelo usuário.
 *
 * Para pacote DUET exportado, corresponde ao EntryPoint imutável
 * já registrado no Release.
 */
export async function importRobotPackage(
    file: File,
    folderId: number | null,
    entrypointPath: string,
): Promise<RobotImportResponse> {

    const formData =
        new FormData();

    formData.append(
        "file",
        file,
    );

    if (folderId !== null) {
        formData.append(
            "folder_id",
            String(folderId),
        );
    }

    formData.append(
        "entrypoint_path",
        entrypointPath,
    );

    const response =
        await api.post<RobotImportResponse>(
            "/robots/import",
            formData,
        );

    return response.data;
}
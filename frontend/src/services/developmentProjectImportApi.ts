// ============================================================
// DUET CORE - DEVELOPMENT PROJECT IMPORT API
// ============================================================
//
// Responsabilidade:
//     Centraliza exclusivamente as chamadas HTTP do fluxo de
//     importação de projetos Python para Development.
//
// Fluxo:
//     1. analyze  -> envia o ZIP temporariamente e lista .py;
//     2. confirm  -> confirma nome + EntryPoint e cria o projeto.
//
// Este módulo NÃO controla estado visual e NÃO renderiza UI.
// ============================================================

import api from "./api";

import type {
    DevelopmentProject,
} from "../types/development";


export interface DevelopmentProjectImportAnalysis {
    status: string;
    import_token: string;
    filename: string;
    python_files: string[];
    suggested_entrypoint: string | null;
    entrypoint_required: boolean;
}


export interface DevelopmentProjectImportConfirmPayload {
    import_token: string;
    name: string;
    description: string | null;
    folder_id: number | null;
    entrypoint_path: string;
}


export interface DevelopmentProjectImportConfirmResponse {
    status: string;
    message: string;
    project: DevelopmentProject;
}


export async function analyzeDevelopmentProjectImport(
    file: File
): Promise<DevelopmentProjectImportAnalysis> {

    const formData = new FormData();
    formData.append("file", file);

    const response = await api.post(
        "/development/projects/import/analyze",
        formData
    );

    return response.data as DevelopmentProjectImportAnalysis;
}


export async function confirmDevelopmentProjectImport(
    payload: DevelopmentProjectImportConfirmPayload
): Promise<DevelopmentProjectImportConfirmResponse> {

    const response = await api.post(
        "/development/projects/import/confirm",
        payload
    );

    return response.data as DevelopmentProjectImportConfirmResponse;
}

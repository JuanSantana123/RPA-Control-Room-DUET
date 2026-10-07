/**
 * API DO MÓDULO DE BIBLIOTECAS
 * ============================
 *
 * Centraliza todas as chamadas HTTP específicas da feature.
 *
 * IMPORTANTE:
 * - componentes React não conhecem URLs diretamente;
 * - regras HTTP ficam somente nesta camada;
 * - nenhuma lógica visual deve existir aqui.
 */

import api from "../../../services/api";

import type {
    CreateLibraryFolderPayload,
    CreateLibraryPayload,
    ImportLibraryPayload,
    ImportLibraryResponse,
    LibraryResponse,
    LibraryTreeResponse,
    LibraryVersionsResponse,
    UpdateLibraryFolderPayload,
    UpdateLibraryPayload,
} from "../types/libraries";


/* ============================================================
   CATÁLOGO
   ============================================================ */

/**
 * Retorna a árvore completa do catálogo de Bibliotecas.
 */
export async function getLibrariesTree(
    includeInactive: boolean = false
): Promise<LibraryTreeResponse> {
    const response = await api.get(
        "/libraries/tree",
        {
            params: {
                include_inactive:
                    includeInactive,
            },
        }
    );

    return response.data;
}

/* ============================================================
   VERSÕES
   ============================================================ */

/**
 * Retorna as versões publicadas de uma Library.
 */
export async function getLibraryVersions(
    libraryId: number,
    includeInactive: boolean = true
): Promise<LibraryVersionsResponse> {
    const response = await api.get(
        `/libraries/${libraryId}/versions`,
        {
            params: {
                include_inactive:
                    includeInactive,
            },
        }
    );

    return response.data;
}


/* ============================================================
   PASTAS
   ============================================================ */

/**
 * Cria uma pasta organizacional no catálogo.
 */
export async function createLibraryFolder(
    payload: CreateLibraryFolderPayload
): Promise<void> {
    await api.post(
        "/libraries/folders",
        payload
    );
}


/**
 * Atualiza uma pasta.
 *
 * Pode ser utilizado para:
 * - renomear;
 * - mover para outra pasta.
 */
export async function updateLibraryFolder(
    folderId: number,
    payload: UpdateLibraryFolderPayload
): Promise<void> {
    await api.patch(
        `/libraries/folders/${folderId}`,
        payload
    );
}


/**
 * Exclui uma pasta do catálogo.
 */
export async function deleteLibraryFolder(
    folderId: number
): Promise<void> {
    await api.delete(
        `/libraries/folders/${folderId}`
    );
}


/* ============================================================
   LIBRARIES
   ============================================================ */

/**
 * Cria a identidade de uma Library.
 */
export async function createLibrary(
    payload: CreateLibraryPayload
): Promise<LibraryResponse> {
    const response = await api.post(
        "/libraries",
        payload
    );

    return response.data;
}


/**
 * Atualiza os metadados editáveis da Library.
 */
export async function updateLibrary(
    libraryId: number,
    payload: UpdateLibraryPayload
): Promise<void> {
    await api.patch(
        `/libraries/${libraryId}`,
        payload
    );
}


/**
 * Move uma Library para outra pasta.
 */
export async function moveLibrary(
    libraryId: number,
    folderId: number | null
): Promise<void> {
    await api.patch(
        `/libraries/${libraryId}/folder`,
        {
            folder_id: folderId,
        }
    );
}


/**
 * Desativa uma Library.
 *
 * O histórico/versionamento permanece controlado pelo backend.
 */
export async function deactivateLibrary(
    libraryId: number
): Promise<void> {
    await api.delete(
        `/libraries/${libraryId}`
    );
}

/**
 * Reativa uma Library anteriormente arquivada.
 *
 * A identidade e todo o histórico continuam sendo os mesmos.
 */
export async function reactivateLibrary(
    libraryId: number
): Promise<LibraryResponse> {
    const response = await api.post(
        `/libraries/${libraryId}/reactivate`
    );

    return response.data;
}
/* ============================================================
   IMPORTAÇÃO STANDALONE
   ============================================================ */

/**
 * Importa diretamente uma biblioteca Python já existente.
 *
 * IMPORTANTE:
 * Não definimos Content-Type manualmente.
 * O navegador/Axios gera automaticamente o boundary correto
 * para multipart/form-data.
 */
export async function importStandaloneLibrary(
    payload: ImportLibraryPayload
): Promise<ImportLibraryResponse> {
    const formData =
        new FormData();

    formData.append(
        "name",
        payload.name
    );

    formData.append(
        "import_name",
        payload.importName
    );

    formData.append(
        "version",
        payload.version
    );

    formData.append(
        "description",
        payload.description
    );

    if (
        payload.folderId !== null
    ) {
        formData.append(
            "folder_id",
            String(
                payload.folderId
            )
        );
    }

    formData.append(
        "file",
        payload.file
    );

    const response = await api.post(
        "/libraries/import",
        formData
    );

    return response.data;
}
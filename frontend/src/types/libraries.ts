/**
 * TIPOS DO MÓDULO DE BIBLIOTECAS
 * ==============================
 *
 * Centraliza os contratos TypeScript utilizados pela feature de Bibliotecas.
 *
 * IMPORTANTE
 * ----------
 * Este arquivo contém somente tipos.
 * Não deve conter chamadas HTTP, regras de negócio ou componentes React.
 */


/**
 * Pasta organizacional do catálogo global.
 *
 * Essa estrutura organiza Libraries no Control Room.
 * Ela NÃO representa as pastas Python existentes dentro da biblioteca.
 */
export interface LibraryFolderTreeNode {
    type: "folder";
    id: number;
    name: string;
    parent_id: number | null;
    created_by: number;
    created_at: string | null;
    updated_at: string | null;
    is_active: boolean;
    children: LibraryTreeNode[];
}


/**
 * Biblioteca reutilizável exibida no catálogo global.
 */
export interface LibraryCatalogItem {
    type: "library";
    id: number;
    name: string;
    import_name: string;
    description: string | null;
    folder_id: number | null;
    created_by: number;
    created_at: string | null;
    updated_at: string | null;
    is_active: boolean;
}


/**
 * Nó possível dentro da árvore do catálogo.
 */
export type LibraryTreeNode =
    | LibraryFolderTreeNode
    | LibraryCatalogItem;


/**
 * Versão publicada e imutável de uma Library.
 */
export interface LibraryVersionItem {
    id: number;
    library_id: number;
    version: string;
    source_type: string;
    source_robot_id: number | null;
    source_robot_version: number | null;
    source_path: string | null;
    file_hash: string;
    published_by: number;
    published_at: string | null;
    is_active: boolean;

    /**
     * Alguns endpoints podem informar explicitamente se a versão
     * é a versão vigente em Produção.
     *
     * Mantemos opcional para preservar compatibilidade com as
     * respostas atuais do backend.
     */
    is_production?: boolean;
}


/**
 * Estrutura simplificada utilizada pelos seletores de pasta.
 *
 * Ela é propositalmente independente dos demais metadados
 * retornados pelo backend.
 */
export interface LibraryFolderOption {
    id: number;
    name: string;
    parent_id: number | null;
    children: LibraryFolderOption[];
}


/**
 * Modos do modal de pasta.
 */
export type FolderEditorMode =
    | "create"
    | "rename"
    | null;


/**
 * Modos do modal de Library.
 */
export type LibraryEditorMode =
    | "create"
    | "edit"
    | null;


/**
 * Modos do seletor reutilizável de pasta.
 */
export type FolderPickerMode =
    | "folder-create-location"
    | "folder-move"
    | "library-create-location"
    | "library-move"
    | null;


/**
 * Confirmações destrutivas suportadas pelo catálogo.
 */
export type LibraryConfirmationState =
    | {
        kind: "delete-folder";
        folder: LibraryFolderTreeNode;
    }
    | {
        kind: "deactivate-library";
        library: LibraryCatalogItem;
    }
    | null;


/**
 * Dados enviados pelo modal de importação direta.
 */
export interface ImportLibraryPayload {
    name: string;
    importName: string;
    description: string;
    version: string;
    folderId: number | null;
    file: File;
}


/**
 * Payload para criação de pasta.
 */
export interface CreateLibraryFolderPayload {
    name: string;
    parent_id: number | null;
}


/**
 * Payload para atualização de pasta.
 */
export interface UpdateLibraryFolderPayload {
    name?: string;
    parent_id?: number | null;
}


/**
 * Payload para criação de Library.
 */
export interface CreateLibraryPayload {
    name: string;
    import_name: string;
    description: string | null;
    folder_id: number | null;
}


/**
 * Payload para edição dos metadados de uma Library.
 */
export interface UpdateLibraryPayload {
    name: string;
    description: string | null;
}


/**
 * Resposta do catálogo em árvore.
 */
export interface LibraryTreeResponse {
    tree: LibraryTreeNode[];
    total_folders: number;
    total_libraries: number;
}


/**
 * Resposta da listagem de versões.
 */
export interface LibraryVersionsResponse {
    versions: LibraryVersionItem[];
}


/**
 * Resposta mínima utilizada após criação/importação.
 */
export interface LibraryResponse {
    library?: Omit<LibraryCatalogItem, "type">;
}


/**
 * Resposta mínima da importação standalone.
 */
export interface ImportLibraryResponse extends LibraryResponse {
    version?: LibraryVersionItem;
    message?: string;
    status?: string;
}

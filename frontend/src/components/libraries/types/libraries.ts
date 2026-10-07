/**
 * TIPOS DO MÓDULO DE BIBLIOTECAS
 * ==============================
 *
 * Centraliza os contratos TypeScript utilizados pela feature
 * de Bibliotecas.
 *
 * IMPORTANTE
 * ----------
 * Este arquivo contém SOMENTE tipos.
 *
 * Não deve conter:
 * - chamadas HTTP;
 * - funções de API;
 * - componentes React;
 * - regras de negócio.
 */


/* ============================================================
   ÁRVORE DO CATÁLOGO
   ============================================================ */

/**
 * Pasta organizacional do catálogo global.
 *
 * IMPORTANTE:
 *
 * Esta pasta organiza Libraries dentro do Control Room.
 *
 * Ela NÃO representa uma pasta Python existente
 * dentro do código da biblioteca.
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
 * Um nó da árvore pode ser:
 *
 * - pasta;
 * - biblioteca.
 */
export type LibraryTreeNode =
    | LibraryFolderTreeNode
    | LibraryCatalogItem;

/**
 * Visões disponíveis no catálogo global.
 *
 * active:
 *     Libraries operacionais.
 *
 * archived:
 *     Libraries já publicadas e posteriormente desativadas.
 */
export type LibraryCatalogView =
    | "active"
    | "archived";
/* ============================================================
   VERSÕES
   ============================================================ */

/**
 * Representa uma versão publicada de uma Library.
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
     * Alguns endpoints podem informar explicitamente
     * se esta é a versão vigente em Produção.
     *
     * É opcional para manter compatibilidade com as
     * respostas atuais do backend.
     */
    is_production?: boolean;
}


/* ============================================================
   SELETOR DE PASTAS
   ============================================================ */

/**
 * Estrutura simplificada utilizada pelos componentes
 * que precisam apenas navegar pelas pastas.
 */
export interface LibraryFolderOption {
    id: number;

    name: string;

    parent_id: number | null;

    children: LibraryFolderOption[];
}


/* ============================================================
   MODOS DOS EDITORES
   ============================================================ */

/**
 * Modos disponíveis para edição de pasta.
 */
export type FolderEditorMode =
    | "create"
    | "rename"
    | null;


/**
 * Modos disponíveis para edição da Library.
 */
export type LibraryEditorMode =
    | "create"
    | "edit"
    | null;


/**
 * Contextos onde o seletor de pasta pode ser utilizado.
 */
export type FolderPickerMode =
    | "folder-create-location"
    | "folder-move"
    | "library-create-location"
    | "library-move"
    | null;


/* ============================================================
   CONFIRMAÇÕES
   ============================================================ */

/**
 * Ações destrutivas que precisam de confirmação.
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


/* ============================================================
   IMPORTAÇÃO DIRETA
   ============================================================ */

/**
 * Dados recebidos do modal de importação.
 */
export interface ImportLibraryPayload {
    name: string;

    importName: string;

    description: string;

    version: string;

    folderId: number | null;

    file: File;
}


/* ============================================================
   PAYLOADS - PASTAS
   ============================================================ */

/**
 * Payload utilizado para criar uma pasta.
 */
export interface CreateLibraryFolderPayload {
    name: string;

    parent_id: number | null;
}


/**
 * Payload utilizado para alterar uma pasta.
 *
 * Os campos são opcionais porque o mesmo endpoint
 * pode ser utilizado para:
 *
 * - renomear;
 * - mover.
 */
export interface UpdateLibraryFolderPayload {
    name?: string;

    parent_id?: number | null;
}


/* ============================================================
   PAYLOADS - LIBRARY
   ============================================================ */

/**
 * Payload utilizado para criar a identidade
 * de uma nova Library.
 */
export interface CreateLibraryPayload {
    name: string;

    import_name: string;

    description: string | null;

    folder_id: number | null;
}


/**
 * Payload utilizado para editar os metadados
 * de uma Library existente.
 */
export interface UpdateLibraryPayload {
    name: string;

    description: string | null;
}


/* ============================================================
   RESPOSTAS - API
   ============================================================ */

/**
 * Resposta do endpoint:
 *
 * GET /libraries/tree
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
 * Resposta mínima utilizada ao criar uma Library.
 */
export interface LibraryResponse {
    library?: Omit<
        LibraryCatalogItem,
        "type"
    >;
}


/**
 * Resposta da importação direta de uma biblioteca.
 */
export interface ImportLibraryResponse
    extends LibraryResponse {

    version?: LibraryVersionItem;

    message?: string;

    status?: string;
}
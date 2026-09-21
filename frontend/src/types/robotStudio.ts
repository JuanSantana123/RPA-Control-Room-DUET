// ============================================================
// DUET CORE - ROBOT STUDIO - TIPOS
// ============================================================
//
// Responsabilidade:
// - centralizar os contratos TypeScript atualmente utilizados
//   pelo RobotStudio.tsx;
// - representar workspace, abas, navegação, Checkout,
//   AutomationProject e Libraries;
// - permitir que os próximos módulos do Studio reutilizem
//   exatamente os mesmos contratos.
//
// IMPORTANTE:
// Este arquivo faz parte de uma refatoração estrutural.
// Nenhuma regra funcional do Robot Studio deve ser alterada
// durante esta extração.
//
// Este módulo NÃO deve:
// - executar chamadas HTTP;
// - possuir estado React;
// - implementar regras de negócio;
// - renderizar componentes.
//
// Os contratos abaixo reproduzem os tipos existentes no
// RobotStudio.tsx antes da modularização.
// ============================================================


// ============================================================
// WORKSPACE
// ============================================================

export type StudioNodeType = "file" | "folder";


export interface StudioNode {
    id: string;
    name: string;
    type: StudioNodeType;
    content?: string;
    children?: StudioNode[];
}


export interface OpenTab {
    id: string;
    name: string;
}


// ============================================================
// NAVEGAÇÃO
// ============================================================

export interface StudioLocationState {

    // Nome do projeto enviado pela página Desenvolvimento.
    projectName?: string;
}


// ============================================================
// CHECKOUT DO PROJETO
// ============================================================

export interface ProjectCheckout {
    id: number;
    project_id: number;
    user_id: number;
    user_name: string | null;
    checked_out_at: string | null;
}


export interface ProjectCheckoutState {
    checked_out: boolean;
    owns_checkout: boolean;
    checkout: ProjectCheckout | null;
}


// ============================================================
// PROJETO DE DESENVOLVIMENTO
// ============================================================
//
// Representa os metadados retornados pelo endpoint:
//
// GET /development/projects/{project_id}
//
// O conteúdo dos arquivos do workspace NÃO faz parte deste
// objeto.
// ============================================================

export interface AutomationProject {

    // ID real do projeto no PostgreSQL.
    id: number;

    // Nome exibido no DUET Studio.
    name: string;

    // Descrição opcional.
    description: string | null;

    // Pasta da área de Desenvolvimento.
    folder_id: number | null;

    // Estado atual do projeto.
    status: string;

    // Origem em produção, quando existir.
    base_robot_id: number | null;
    base_version: number | null;

    // Auditoria.
    created_by: number;
    created_at: string | null;
    updated_at: string | null;

    // Soft delete.
    is_active: boolean;
}


// ============================================================
// BIBLIOTECAS PUBLICADAS DISPONÍVEIS PARA O PROJETO
// ============================================================
//
// Estes tipos representam o retorno do endpoint:
//
// GET /libraries/projects/{project_id}/available
//
// A versão de Produção vem explicitamente identificada pelo
// backend e será a escolha padrão no Studio.
// ============================================================

export interface PublishedLibraryVersion {
    id: number;
    library_id: number;
    version: string;
    is_production: boolean;
    is_active: boolean;
}


export interface AvailableProjectLibrary {

    library: {
        id: number;
        name: string;
        import_name: string;
        description: string | null;
        is_active: boolean;
    };

    // Versão que deve ser utilizada por padrão quando
    // o desenvolvedor selecionar esta Biblioteca.
    default_version_id: number;

    production_version: PublishedLibraryVersion;

    // Informa se a Biblioteca já pertence ao projeto.
    already_added: boolean;

    current_dependency: {
        library_version_id?: number;
        version?: string;
    } | null;

    // Produção + versões anteriores ainda disponíveis.
    versions: PublishedLibraryVersion[];
}
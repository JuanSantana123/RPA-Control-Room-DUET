// ============================================================
// TIPOS - DEVELOPMENT
// ============================================================
//
// Responsabilidade:
//     Centraliza os tipos TypeScript utilizados pela área de
//     Desenvolvimento do DUET CORE.
//
// Este arquivo descreve estruturas utilizadas em:
//     - projetos de Desenvolvimento;
//     - menus de projeto;
//     - origem de novos projetos;
//     - Agents para execução;
//     - Workflow / Kanban;
//     - Checkout;
//     - planejamento dos cards;
//     - comentários;
//     - Release.
//
// Este arquivo contém SOMENTE definições de tipos.
//
// Não deve:
//     - possuir estado React;
//     - realizar chamadas HTTP;
//     - conter regras de negócio;
//     - renderizar componentes.
//
// Objetivo arquitetural:
//     Evitar que Development.tsx concentre modelos de dados que
//     podem ser reutilizados por componentes, hooks e services.
// ============================================================


// ============================================================
// MENU DO PROJETO
// ============================================================

export interface ProjectMenuState {

    // Projeto ao qual o menu aberto pertence.
    projectId: number;

    // Coordenadas da tela utilizadas pelo menu renderizado
    // através de Portal.
    top: number;
    left: number;
}


// ============================================================
// PROJETO DE DESENVOLVIMENTO
// ============================================================
//
// Representa um AutomationProject persistido no Control Room.
//
// O mesmo projeto pode aparecer:
//     - na lista tradicional;
//     - no Workflow / Kanban;
//     - no DUET Studio.
// ============================================================

export interface DevelopmentProject {

    // ID real gerado pelo PostgreSQL.
    id: number;

    // Dados principais do projeto.
    name: string;
    description: string | null;

    // Pasta da área de Desenvolvimento.
    folder_id: number | null;

    // Estado técnico do projeto.
    status:
        | "draft"
        | "modified"
        | "published";

    // Estágio atual do Workflow.
    current_stage_id: number | null;

    // Origem em Produção, quando o projeto nasceu
    // de um Robot já publicado.
    base_robot_id: number | null;
    // Nome amigável do Robot publicado que originou o projeto.
    //
    // null:
    //     projeto criado do zero ou Robot de origem indisponível.
    base_robot_name: string | null;
    base_version: number | null;


    // ========================================================
    // AUDITORIA
    // ========================================================

    created_by: number;
    created_at: string | null;
    updated_at: string | null;


    // ========================================================
    // CHECKOUT ATUAL
    // ========================================================
    //
    // null:
    //     ninguém está editando o projeto.
    //
    // objeto:
    //     identifica o usuário que possui o Checkout exclusivo.
    // ========================================================

    checkout?: {
        id: number;
        project_id: number;
        user_id: number;
        user_name: string | null;
        checked_out_at: string | null;
    } | null;


    // ========================================================
    // PLANEJAMENTO DO CARD
    // ========================================================
    //
    // Estes dados pertencem individualmente ao projeto.
    //
    // Responsável técnico NÃO representa o usuário que está
    // atualmente em Checkout.
    // ========================================================

    functional_responsible_id: number | null;
    functional_responsible_name?: string | null;

    technical_responsible_id: number | null;
    technical_responsible_name?: string | null;

    start_date: string | null;
    due_date: string | null;

    effort_hours: number | null;

    // O board devolve somente a quantidade.
    // Os comentários completos são carregados quando o painel
    // de detalhes do card é aberto.
    comments_count?: number;


    // ========================================================
    // LIXEIRA
    // ========================================================

    deleted_at: string | null;
    deleted_by: number | null;
    deleted_by_name?: string | null;


    // Soft delete.
    is_active: boolean;
}


// ============================================================
// ORIGEM DO NOVO PROJETO
// ============================================================
//
// "new":
//     automação criada do zero.
//
// "existing":
//     projeto criado a partir de um Robot existente.
// ============================================================

export type ProjectOriginMode =
    | "new"
    | "existing";


export interface OriginRobotFolder {

    // ID real da pasta na estrutura de Robôs.
    id: number;

    // Nome apresentado ao usuário.
    name: string;

    // null representa uma pasta diretamente na raiz.
    parent_id: number | null;
}


export interface OriginRobot {

    // Identidade permanente do Robot.
    id: number;

    // Nome atual em Produção.
    name: string;

    // Versão atualmente publicada.
    version: number;

    // Pasta real do Robot.
    folder_id: number | null;

    // Caminho amigável utilizado pela interface.
    folder_label: string;
}


// ============================================================
// AGENTS PARA EXECUÇÃO
// ============================================================
//
// Estrutura retornada pelo endpoint:
//     /agents/execution/available-agents
//
// Contém somente os dados necessários para o usuário escolher
// onde executar o projeto de Desenvolvimento.
// ============================================================

export interface ExecutionAgent {

    agent_id: string;

    name: string;

    host: string;
    port: number;

    status: string;

    session_status: string | null;

    username: string | null;
}


// ============================================================
// RELEASE
// ============================================================
//
// Representa a prévia calculada pelo backend antes de publicar
// um projeto de Desenvolvimento em Produção.
// ============================================================

export interface ReleasePreview {

    // Token que garante que a publicação utilize exatamente
    // a prévia que foi calculada.
    preview_token: string;


    // Robot existente quando o projeto representa uma nova
    // versão de uma automação já publicada.
    robot: {
        id: number;
        name: string;
        version: number;
        folder_id: number | null;
    } | null;


    // Próxima versão do Robot.
    next_version: number;


    // Pacotes encontrados no projeto que podem ser convertidos
    // em Libraries durante o Release.
    library_candidates: string[];


    // Estrutura de pastas de Produção disponível para destino.
    folders: {
        id: number;
        name: string;
        parent_id: number | null;
    }[];


    // Libraries já vinculadas ao projeto.
    dependencies: {
        library_id: number;
        library_name: string;
        version: string;
        modified: boolean;
        suggested_version: string;
    }[];
}


// ============================================================
// WORKFLOW / KANBAN
// ============================================================

export type DevelopmentViewMode =
    | "projects"
    | "kanban";


export interface DevelopmentStage {

    // Identificação do estágio persistido.
    id: number;

    code: string;
    name: string;

    position: number;

    is_active: boolean;


    // Quantidade total de projetos da coluna.
    total_projects: number;


    // Projetos pertencentes ao estágio.
    projects: DevelopmentProject[];
}


// ============================================================
// DETALHES DO CARD
// ============================================================

export interface CardUser {

    // Usuário ativo disponível para responsabilidade
    // funcional ou técnica.
    id: number;

    name: string;
}


export interface CardComment {

    // Identidade do comentário.
    id: number;

    // Projeto ao qual pertence.
    project_id: number;


    // Autor obtido pela sessão autenticada.
    user_id: number;

    user_name: string | null;


    // Conteúdo do comentário.
    content: string;


    // Auditoria.
    created_at: string | null;

    updated_at: string | null;
}

// ============================================================
// PAYLOAD - CRIAÇÃO DE PROJETO
// ============================================================
//
// Estrutura enviada ao backend ao criar um novo
// AutomationProject na área de Desenvolvimento.
// ============================================================

export interface CreateDevelopmentProjectPayload {

    // Título da demanda.
    name: string;

    // Descrição opcional.
    description: string | null;

    // Pasta de Desenvolvimento.
    folder_id: number | null;

    // Robot de Produção utilizado como origem.
    //
    // null:
    //     projeto criado do zero.
    base_robot_id: number | null;
}


// ============================================================
// PAYLOAD - PLANEJAMENTO DO CARD
// ============================================================
//
// Estrutura enviada ao endpoint de atualização dos metadados
// de planejamento de um card do Kanban.
// ============================================================

export interface CardDetailsUpdatePayload {

    functional_responsible_id: number | null;

    technical_responsible_id: number | null;

    start_date: string | null;

    due_date: string | null;

    effort_hours: number | null;
}


// ============================================================
// PAYLOAD - NOVA LIBRARY DURANTE RELEASE
// ============================================================
//
// Representa um pacote do projeto que será publicado como uma
// nova Library durante o processo de Release.
// ============================================================

export interface NewReleaseLibraryPayload {

    import_name: string;

    name: string;

    version: string;
}


// ============================================================
// PAYLOAD - PUBLICAÇÃO
// ============================================================
//
// Estrutura enviada ao backend quando o usuário confirma o
// Release de um AutomationProject.
//
// Ela mantém:
//     - confirmação da demanda;
//     - token da prévia;
//     - destino do Robot;
//     - nome definitivo de Produção;
//     - versões das Libraries;
//     - novas Libraries criadas durante o Release.
// ============================================================

export interface PublishDevelopmentProjectPayload {

    confirmation_name: string;

    preview_token: string;

    folder_id: number | null;

    new_folder_path: string;

    robot_name: string;

    library_versions: Record<number, string>;

    new_libraries: NewReleaseLibraryPayload[];
}
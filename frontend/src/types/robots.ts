// ============================================================
// DUET CORE - ROBOTS - TYPES
// ============================================================
//
// Responsabilidade:
// - centralizar os contratos TypeScript utilizados pela área
//   de Robots;
// - representar pastas, Robots publicados, Agents disponíveis
//   para execução e snapshots de Libraries de um Release.
//
// Este módulo NÃO:
// - realiza chamadas HTTP;
// - mantém estado React;
// - contém regras de negócio;
// - renderiza componentes.
//
// Integrações:
// - página Robots;
// - hooks de Robots;
// - componentes visuais da área de Robots;
// - respostas dos endpoints de Robots, Agents e Libraries.
//
// IMPORTANTE:
// Estes contratos foram extraídos do Robots.tsx atual sem
// alteração de estrutura ou comportamento.
// ============================================================


// ============================================================
// ROBOT FOLDER
// ============================================================
//
// Representa uma pasta real de Robots cadastrada no backend.
//
// A "Raiz de Robôs" NÃO utiliza este contrato, pois ela é uma
// localização lógica correspondente a Robots com folder_id NULL.
// ============================================================

export interface RobotFolder {
    id: number;
    name: string;
    parent_id: number | null;
}


// ============================================================
// EXECUTION AGENT
// ============================================================
//
// Representa um Agent disponível para execução manual.
//
// O agent_token não é enviado ao frontend e, portanto,
// deliberadamente não faz parte deste contrato.
// ============================================================

export interface ExecutionAgent {
    agent_id: string;
    name: string;
    host: string;
    port: number;
    rpa_directory: string | null;
    status: string;
    session_status: string;
    username: string | null;
}


// ============================================================
// ROBOT
// ============================================================
//
// Representa a versão atualmente publicada de um Robot
// apresentada na página de Robots.
// ============================================================

export interface Robot {
    id: number;
    name: string;
    filename: string;
    version: string;
    file_hash: string;
    file_path: string;
}


// ============================================================
// ROBOT LIBRARY DEPENDENCY
// ============================================================
//
// Representa uma versão EXATA de uma Library utilizada por
// uma versão publicada de um Robot.
//
// O snapshot pertence ao Release e deve permanecer imutável,
// mesmo quando outra versão da Library se tornar Production.
// ============================================================

export interface RobotLibraryDependency {
    library_id: number;
    name: string;
    import_name: string;
    library_version_id: number;
    version: string;

    // true:
    //     esta versão da Library também é atualmente a versão
    //     vigente em Produção.
    //
    // false:
    //     o Robot continua utilizando uma versão histórica,
    //     mesmo que exista outra versão vigente no catálogo.
    is_current_production: boolean;
}


// ============================================================
// ROBOT LIBRARIES RESPONSE
// ============================================================
//
// Contrato da resposta:
//
// GET /robots/{robot_id}/versions/{robot_version}/libraries
//
// A resposta representa o snapshot de Libraries registrado
// durante o Release daquela versão específica do Robot.
// ============================================================

export interface RobotLibrariesResponse {
    status: string;

    robot: {
        id: number;
        name: string;
        version: number;
        is_current_version: boolean;
    };

    total: number;

    libraries: RobotLibraryDependency[];
}
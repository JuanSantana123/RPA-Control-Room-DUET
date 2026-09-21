// ============================================================
// DUET CORE - ROLES - TYPES
// ============================================================
//
// Contratos TypeScript utilizados pela área de controle
// de acesso baseada em Roles.
//
// Responsabilidade:
// - representar Roles retornadas pelo Control Room;
// - representar permissões disponíveis no catálogo.
//
// Este módulo NÃO:
// - executa chamadas HTTP;
// - possui estado React;
// - contém regras de autorização;
// - renderiza componentes.
//
// Os contratos foram extraídos diretamente de pages/Roles.tsx.
// ============================================================


// ============================================================
// ROLE
// ============================================================

export interface Role {
    id: number;
    name: string;
    description: string | null;
}


// ============================================================
// PERMISSION
// ============================================================

export interface Permission {
    id: number;
    resource: string;
    action: string;
}
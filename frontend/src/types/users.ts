// ============================================================
// DUET CORE - USERS - TYPES
// ============================================================
//
// Contratos TypeScript utilizados pela gestão de usuários.
//
// Responsabilidade:
// - representar usuários;
// - representar Roles associadas aos usuários;
// - representar Roles disponíveis no Control Room.
//
// Este módulo NÃO:
// - possui estado React;
// - executa chamadas HTTP;
// - implementa regras de permissão;
// - renderiza interface.
// ============================================================


// ============================================================
// ROLE ASSOCIADA AO USUÁRIO
// ============================================================

export interface UserRole {
    id: number;
    name: string;
}


// ============================================================
// USUÁRIO
// ============================================================

export interface User {
    id: number;
    username: string;
    name: string;
    is_active: number;
    roles: UserRole[];
}


// ============================================================
// ROLE DISPONÍVEL
// ============================================================

export interface UserAvailableRole {
    id: number;
    name: string;
}
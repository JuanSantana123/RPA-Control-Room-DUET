// ============================================================
// DUET CORE - VAULT - TYPES
// ============================================================
//
// Contratos TypeScript utilizados pelo Credential Vault.
//
// Responsabilidade:
// - representar pastas;
// - representar credenciais;
// - representar campos retornados pelo backend;
// - representar campos durante criação;
// - representar campos durante edição.
//
// IMPORTANTE:
// EditCredentialField possui keep_existing.
// Essa propriedade faz parte da proteção dos valores secretos
// existentes e não deve ser removida ou simplificada.
// ============================================================


// ============================================================
// PASTA
// ============================================================

export interface VaultFolder {
    id: number;
    name: string;
    parent_id: number | null;
    children?: VaultFolder[];
}


// ============================================================
// CAMPO DE CREDENCIAL
// ============================================================

export interface VaultField {
    id?: number;
    name: string;
    value: string;
    is_secret: boolean;
}


// ============================================================
// CREDENCIAL
// ============================================================

export interface VaultCredential {
    id: number;
    name: string;
    folder_id: number;
    fields: VaultField[];
}


// ============================================================
// CAMPO DE NOVA CREDENCIAL
// ============================================================

export interface NewCredentialField {
    name: string;
    value: string;
    is_secret: boolean;
}


// ============================================================
// CAMPO DE CREDENCIAL EM EDIÇÃO
// ============================================================
//
// keep_existing=true significa que um segredo existente deve
// permanecer no backend sem que seu valor precise ser enviado
// novamente pelo frontend.
// ============================================================

export interface EditCredentialField {
    id?: number;
    name: string;
    value: string;
    is_secret: boolean;
    keep_existing?: boolean;
}
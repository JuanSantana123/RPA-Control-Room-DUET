// ============================================================
// DUET CORE - DEVICE CREDENTIAL TYPES
// ============================================================
//
// Tipos utilizados exclusivamente pelo frontend das
// Credenciais de Dispositivo.
//
// Responsabilidade:
//
// - representar a credencial Windows retornada pelo backend;
// - representar os payloads de criação e edição;
// - representar os envelopes de resposta da API;
// - manter os contratos do frontend separados dos tipos das
//   Credenciais de Automação.
//
// ESTE ARQUIVO NÃO:
//
// - executa chamadas HTTP;
// - acessa React;
// - manipula estado;
// - manipula senha em claro fora dos payloads de formulário;
// - conhece pastas do Vault;
// - conhece Agents/Devices.
//
// IMPORTANTE SOBRE SENHA:
//
// O campo "password" retornado pelo backend NUNCA representa
// a senha real. Ele pode conter somente o valor mascarado
// "********" ou uma string vazia.
//
// A senha em claro existe no frontend somente enquanto o
// usuário a digita em um formulário de criação/alteração.
// ============================================================


// ============================================================
// VALORES FIXOS DO DOMÍNIO
// ============================================================

export type DeviceCredentialScope =
    "device";


export type DeviceCredentialType =
    "windows";


export type DeviceCredentialApiStatus =
    | "success"
    | "error";


// ============================================================
// CREDENCIAL DE DISPOSITIVO
// ============================================================
//
// Representa uma credencial Windows segura retornada pela API.
//
// folder_id é mantido no contrato porque o backend o retorna,
// porém para Device Credentials o valor esperado é null.
//
// password NÃO deve ser utilizado para preencher formulário.
// O frontend deve usar has_password para saber se existe um
// segredo já cadastrado.
// ============================================================

export interface DeviceCredential {

    id: number;

    name: string;

    scope: DeviceCredentialScope;

    credential_type: DeviceCredentialType;

    folder_id:
        number | null;

    domain: string;

    username: string;

    password: string;

    has_password: boolean;

    created_at:
        string | null;

    updated_at:
        string | null;
}


// ============================================================
// PAYLOAD - CRIAÇÃO
// ============================================================
//
// Corresponde ao contrato:
//
// POST /vault/device-credentials
//
// A senha é obrigatória durante a criação.
// ============================================================

export interface DeviceCredentialCreatePayload {

    name: string;

    domain: string;

    username: string;

    password: string;
}


// ============================================================
// PAYLOAD - EDIÇÃO
// ============================================================
//
// Corresponde ao contrato:
//
// PUT /vault/device-credentials/{credential_id}
//
// Regras:
//
// keep_existing_password = true
//     mantém a senha já armazenada no Vault.
//     Nesse caso password pode ser "".
//
// keep_existing_password = false
//     informa que a senha deve ser substituída.
//     Nesse caso password deve conter o novo valor.
// ============================================================

export interface DeviceCredentialUpdatePayload {

    domain: string;

    username: string;

    password: string;

    keep_existing_password: boolean;
}


// ============================================================
// ESTADO DO FORMULÁRIO
// ============================================================
//
// Tipo utilizado somente pela camada visual/hook.
//
// Ele não é enviado diretamente ao backend porque criação e
// edição possuem contratos diferentes.
// ============================================================

export interface DeviceCredentialFormData {

    name: string;

    domain: string;

    username: string;

    password: string;
}


// ============================================================
// RESPOSTA - LISTAGEM
// ============================================================
//
// GET /vault/device-credentials
// ============================================================

export interface DeviceCredentialListResponse {

    status:
        DeviceCredentialApiStatus;

    message?: string;

    credentials:
        DeviceCredential[];
}


// ============================================================
// RESPOSTA - CONSULTA
// ============================================================
//
// GET /vault/device-credentials/{credential_id}
// ============================================================

export interface DeviceCredentialDetailResponse {

    status:
        DeviceCredentialApiStatus;

    message?: string;

    credential?:
        DeviceCredential;
}


// ============================================================
// RESPOSTA - CRIAÇÃO / EDIÇÃO
// ============================================================
//
// POST /vault/device-credentials
// PUT  /vault/device-credentials/{credential_id}
// ============================================================

export interface DeviceCredentialMutationResponse {

    status:
        DeviceCredentialApiStatus;

    message?: string;

    credential?:
        DeviceCredential;
}


// ============================================================
// RESPOSTA - EXCLUSÃO
// ============================================================
//
// DELETE /vault/device-credentials/{credential_id}
// ============================================================

export interface DeviceCredentialDeleteResponse {

    status:
        DeviceCredentialApiStatus;

    message?: string;

    credential_id?:
        number;
}

// ============================================================
// DUET CORE - DEVICE CREDENTIALS API
// ============================================================
//
// Camada HTTP exclusiva das Credenciais de Dispositivo.
//
// Responsabilidade:
//
// - centralizar as chamadas HTTP do módulo;
// - reutilizar a instância Axios oficial do DUET;
// - aplicar os contratos TypeScript corretos;
// - manter os endpoints de Device separados dos endpoints
//   das Credenciais de Automação.
//
// ESTE ARQUIVO NÃO:
//
// - manipula estado React;
// - exibe mensagens na interface;
// - implementa regras de formulário;
// - interpreta permissões;
// - conhece árvore de pastas;
// - conhece Agents;
// - armazena senha;
// - faz log de payloads contendo senha.
//
// IMPORTANTE:
//
// A senha em claro somente é enviada ao backend nos payloads
// de criação ou alteração quando o usuário a informou.
// Ela nunca deve ser escrita em console.log, error log ou cache.
// ============================================================


import api
    from "./api";


import type {
    DeviceCredentialCreatePayload,
    DeviceCredentialDeleteResponse,
    DeviceCredentialDetailResponse,
    DeviceCredentialListResponse,
    DeviceCredentialMutationResponse,
    DeviceCredentialUpdatePayload,
} from "../types/deviceCredentials";


// ============================================================
// ENDPOINT BASE
// ============================================================
//
// Mantemos o prefixo em uma única constante para impedir
// divergência entre as operações CRUD.
// ============================================================

const DEVICE_CREDENTIALS_ENDPOINT =
    "/vault/device-credentials";


// ============================================================
// LISTAR CREDENCIAIS DE DISPOSITIVO
// ============================================================
//
// GET /vault/device-credentials
//
// O backend retorna somente credenciais:
//
//     scope = "device"
//     credential_type = "windows"
//
// A senha nunca é retornada em texto claro.
// ============================================================

export const listarDeviceCredentials =
    async (): Promise<DeviceCredentialListResponse> => {

        const response =
            await api.get<DeviceCredentialListResponse>(
                DEVICE_CREDENTIALS_ENDPOINT
            );


        return response.data;
    };


// ============================================================
// CONSULTAR CREDENCIAL DE DISPOSITIVO
// ============================================================
//
// GET /vault/device-credentials/{credential_id}
//
// Utilizado quando a interface precisar obter a representação
// segura e atual de uma credencial específica.
// ============================================================

export const consultarDeviceCredential =
    async (
        credentialId: number
    ): Promise<DeviceCredentialDetailResponse> => {

        const response =
            await api.get<DeviceCredentialDetailResponse>(
                `${DEVICE_CREDENTIALS_ENDPOINT}/${credentialId}`
            );


        return response.data;
    };


// ============================================================
// CRIAR CREDENCIAL DE DISPOSITIVO
// ============================================================
//
// POST /vault/device-credentials
//
// Payload esperado:
//
// {
//     name,
//     domain,
//     username,
//     password
// }
//
// A senha é obrigatória na criação.
//
// SEGURANÇA:
//
// Não registrar o objeto payload em console/log porque ele
// contém a senha digitada pelo usuário.
// ============================================================

export const criarDeviceCredential =
    async (
        payload:
            DeviceCredentialCreatePayload
    ): Promise<DeviceCredentialMutationResponse> => {

        const response =
            await api.post<DeviceCredentialMutationResponse>(
                DEVICE_CREDENTIALS_ENDPOINT,
                payload
            );


        return response.data;
    };


// ============================================================
// EDITAR CREDENCIAL DE DISPOSITIVO
// ============================================================
//
// PUT /vault/device-credentials/{credential_id}
//
// O nome da credencial não faz parte do contrato de edição
// atual do backend.
//
// Se:
//
//     keep_existing_password = true
//
// a senha existente permanece preservada e password pode ser
// enviado como string vazia.
//
// Se:
//
//     keep_existing_password = false
//
// password precisa conter o novo segredo informado pelo usuário.
//
// SEGURANÇA:
//
// O payload nunca é escrito em logs.
// ============================================================

export const editarDeviceCredential =
    async (
        credentialId: number,
        payload:
            DeviceCredentialUpdatePayload
    ): Promise<DeviceCredentialMutationResponse> => {

        const response =
            await api.put<DeviceCredentialMutationResponse>(
                `${DEVICE_CREDENTIALS_ENDPOINT}/${credentialId}`,
                payload
            );


        return response.data;
    };


// ============================================================
// EXCLUIR CREDENCIAL DE DISPOSITIVO
// ============================================================
//
// DELETE /vault/device-credentials/{credential_id}
//
// A confirmação visual da exclusão pertence ao hook/componente,
// não à camada HTTP.
// ============================================================

export const excluirDeviceCredential =
    async (
        credentialId: number
    ): Promise<DeviceCredentialDeleteResponse> => {

        const response =
            await api.delete<DeviceCredentialDeleteResponse>(
                `${DEVICE_CREDENTIALS_ENDPOINT}/${credentialId}`
            );


        return response.data;
    };

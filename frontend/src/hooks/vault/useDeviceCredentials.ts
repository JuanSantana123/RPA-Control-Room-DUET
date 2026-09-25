// ============================================================
// DUET CORE - DEVICE CREDENTIALS HOOK
// ============================================================
//
// Hook responsável pelo estado e pelas operações de negócio
// da interface de Credenciais de Dispositivo.
//
// Responsabilidade:
//
// - carregar credenciais Windows de Device;
// - criar credencial;
// - editar credencial;
// - excluir credencial;
// - controlar estados de loading das operações;
// - encaminhar mensagens amigáveis para a interface.
//
// ESTE HOOK NÃO:
//
// - renderiza componentes;
// - abre modal;
// - pede confirmação com window.confirm;
// - conhece árvore de pastas;
// - conhece credenciais de Automação;
// - conhece Agents;
// - realiza chamadas Axios diretamente;
// - registra senha em console/log.
//
// As chamadas HTTP ficam isoladas em:
//
//     services/deviceCredentialsApi.ts
//
// Os contratos ficam isolados em:
//
//     types/deviceCredentials.ts
//
// A normalização de erros reutiliza:
//
//     utils/apiErrors.ts
// ============================================================


import {
    useCallback,
    useEffect,
    useState,
} from "react";


import {
    criarDeviceCredential,
    editarDeviceCredential,
    excluirDeviceCredential,
    listarDeviceCredentials,
} from "../../services/deviceCredentialsApi";


import type {
    DeviceCredential,
    DeviceCredentialCreatePayload,
    DeviceCredentialUpdatePayload,
} from "../../types/deviceCredentials";


import {
    getApiErrorMessage,
} from "../../utils/apiErrors";


// ============================================================
// PROPS
// ============================================================
//
// As mensagens permanecem coordenadas pela página Vault para
// manter o mesmo padrão visual utilizado no módulo atual.
//
// O hook recebe apenas os setters. Ele não conhece o componente
// de alerta nem a estrutura visual da página.
// ============================================================

interface UseDeviceCredentialsProps {

    setError:
        (message: string) => void;

    setSuccessMessage:
        (message: string) => void;
}


// ============================================================
// HOOK
// ============================================================

export const useDeviceCredentials =
    ({
        setError,
        setSuccessMessage,
    }: UseDeviceCredentialsProps) => {

        // ====================================================
        // LISTA
        // ====================================================

        const [
            credentials,
            setCredentials,
        ] = useState<DeviceCredential[]>(
            []
        );


        // ====================================================
        // LOADING DA LISTAGEM
        // ====================================================

        const [
            loadingCredentials,
            setLoadingCredentials,
        ] = useState(
            true
        );


        // ====================================================
        // LOADING DE CRIAÇÃO
        // ====================================================

        const [
            creatingCredential,
            setCreatingCredential,
        ] = useState(
            false
        );


        // ====================================================
        // LOADING DE EDIÇÃO
        // ====================================================

        const [
            updatingCredentialId,
            setUpdatingCredentialId,
        ] = useState<number | null>(
            null
        );


        // ====================================================
        // LOADING DE EXCLUSÃO
        // ====================================================

        const [
            deletingCredentialId,
            setDeletingCredentialId,
        ] = useState<number | null>(
            null
        );


        // ====================================================
        // CARREGAR
        // ====================================================
        //
        // GET /vault/device-credentials
        //
        // A API pode responder HTTP 200 com:
        //
        //     status = "error"
        //
        // por isso validamos também o envelope retornado pelo
        // backend e não somente erros Axios.
        // ====================================================

        const carregarCredenciais =
            useCallback(
                async () => {

                    try {

                        setLoadingCredentials(
                            true
                        );

                        setError(
                            ""
                        );


                        const response =
                            await listarDeviceCredentials();


                        if (
                            response.status !==
                            "success"
                        ) {

                            throw new Error(
                                response.message ||
                                "Não foi possível carregar as credenciais de dispositivo."
                            );
                        }


                        setCredentials(
                            response.credentials ||
                            []
                        );

                    } catch (error) {

                        setCredentials(
                            []
                        );


                        setError(
                            getApiErrorMessage(
                                error,
                                "Não foi possível carregar as credenciais de dispositivo."
                            )
                        );

                    } finally {

                        setLoadingCredentials(
                            false
                        );
                    }
                },
                [
                    setError,
                ]
            );


        // ====================================================
        // CARGA INICIAL
        // ====================================================
        //
        // Este hook será utilizado pelo painel específico de
        // Device Credentials.
        //
        // Como o painel é renderizado somente na aba Device,
        // a chamada inicial acontece apenas quando essa área
        // estiver ativa.
        // ====================================================

        useEffect(
            () => {

                void carregarCredenciais();

            },
            [
                carregarCredenciais,
            ]
        );


        // ====================================================
        // CRIAR
        // ====================================================
        //
        // POST /vault/device-credentials
        //
        // A senha existe no payload apenas durante esta chamada.
        // Este hook não copia o segredo para logs nem para outro
        // estado persistente.
        // ====================================================

        const criarCredencial =
            async (
                payload:
                    DeviceCredentialCreatePayload
            ): Promise<boolean> => {

                try {

                    setCreatingCredential(
                        true
                    );

                    setError(
                        ""
                    );

                    setSuccessMessage(
                        ""
                    );


                    const response =
                        await criarDeviceCredential(
                            payload
                        );


                    if (
                        response.status !==
                        "success"
                    ) {

                        throw new Error(
                            response.message ||
                            "Não foi possível criar a credencial de dispositivo."
                        );
                    }


                    setSuccessMessage(
                        response.message ||
                        "Credencial de dispositivo criada com sucesso."
                    );


                    await carregarCredenciais();


                    return true;

                } catch (error) {

                    setError(
                        getApiErrorMessage(
                            error,
                            "Não foi possível criar a credencial de dispositivo."
                        )
                    );


                    return false;

                } finally {

                    setCreatingCredential(
                        false
                    );
                }
            };


        // ====================================================
        // EDITAR
        // ====================================================
        //
        // PUT /vault/device-credentials/{credential_id}
        //
        // A decisão de manter ou substituir a senha vem pronta
        // no payload:
        //
        // keep_existing_password = true
        //     preserva o segredo existente.
        //
        // keep_existing_password = false
        //     substitui pelo novo password.
        // ====================================================

        const editarCredencial =
            async (
                credentialId: number,
                payload:
                    DeviceCredentialUpdatePayload
            ): Promise<boolean> => {

                try {

                    setUpdatingCredentialId(
                        credentialId
                    );

                    setError(
                        ""
                    );

                    setSuccessMessage(
                        ""
                    );


                    const response =
                        await editarDeviceCredential(
                            credentialId,
                            payload
                        );


                    if (
                        response.status !==
                        "success"
                    ) {

                        throw new Error(
                            response.message ||
                            "Não foi possível atualizar a credencial de dispositivo."
                        );
                    }


                    setSuccessMessage(
                        response.message ||
                        "Credencial de dispositivo atualizada com sucesso."
                    );


                    await carregarCredenciais();


                    return true;

                } catch (error) {

                    setError(
                        getApiErrorMessage(
                            error,
                            "Não foi possível atualizar a credencial de dispositivo."
                        )
                    );


                    return false;

                } finally {

                    setUpdatingCredentialId(
                        null
                    );
                }
            };


        // ====================================================
        // EXCLUIR
        // ====================================================
        //
        // DELETE /vault/device-credentials/{credential_id}
        //
        // A confirmação visual NÃO fica aqui.
        //
        // O componente deverá confirmar a intenção do usuário
        // antes de chamar esta função.
        // ====================================================

        const excluirCredencial =
            async (
                credentialId: number
            ): Promise<boolean> => {

                try {

                    setDeletingCredentialId(
                        credentialId
                    );

                    setError(
                        ""
                    );

                    setSuccessMessage(
                        ""
                    );


                    const response =
                        await excluirDeviceCredential(
                            credentialId
                        );


                    if (
                        response.status !==
                        "success"
                    ) {

                        throw new Error(
                            response.message ||
                            "Não foi possível excluir a credencial de dispositivo."
                        );
                    }


                    setSuccessMessage(
                        response.message ||
                        "Credencial de dispositivo excluída com sucesso."
                    );


                    await carregarCredenciais();


                    return true;

                } catch (error) {

                    setError(
                        getApiErrorMessage(
                            error,
                            "Não foi possível excluir a credencial de dispositivo."
                        )
                    );


                    return false;

                } finally {

                    setDeletingCredentialId(
                        null
                    );
                }
            };


        // ====================================================
        // RETORNO PÚBLICO
        // ====================================================

        return {

            credentials,

            loadingCredentials,
            creatingCredential,
            updatingCredentialId,
            deletingCredentialId,

            carregarCredenciais,
            criarCredencial,
            editarCredencial,
            excluirCredencial,
        };
    };

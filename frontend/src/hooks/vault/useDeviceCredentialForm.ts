// ============================================================
// DUET CORE - DEVICE CREDENTIAL FORM WORKFLOW
// ============================================================
//
// Hook responsável SOMENTE pelo fluxo do formulário de
// Credenciais de Dispositivo.
//
// Responsabilidade:
// - abrir criação;
// - abrir edição;
// - manter os campos do formulário;
// - validar os campos básicos;
// - montar os payloads corretos;
// - fechar e limpar o formulário após sucesso.
//
// NÃO:
// - renderiza UI;
// - chama Axios;
// - lista credenciais;
// - confirma exclusão;
// - conhece pastas;
// - conhece Agents.
//
// As operações de persistência são recebidas por callback.
// ============================================================

import {
    useState,
} from "react";

import type {
    DeviceCredential,
    DeviceCredentialCreatePayload,
    DeviceCredentialFormData,
    DeviceCredentialUpdatePayload,
} from "../../types/deviceCredentials";

import type {
    DeviceCredentialFormMode,
} from "../../components/vault/device/DeviceCredentialForm";


// ============================================================
// TIPOS DOS CALLBACKS
// ============================================================

interface UseDeviceCredentialFormProps {

    setError:
        (message: string) => void;

    setSuccessMessage:
        (message: string) => void;

    createCredential:
        (
            payload: DeviceCredentialCreatePayload
        ) => Promise<boolean>;

    updateCredential:
        (
            credentialId: number,
            payload: DeviceCredentialUpdatePayload
        ) => Promise<boolean>;
}


// ============================================================
// ESTADO VAZIO
// ============================================================

const EMPTY_FORM_DATA: DeviceCredentialFormData = {
    name: "",
    domain: "",
    username: "",
    password: "",
};


// ============================================================
// HOOK
// ============================================================

export const useDeviceCredentialForm =
    ({
        setError,
        setSuccessMessage,
        createCredential,
        updateCredential,
    }: UseDeviceCredentialFormProps) => {

        const [
            formMode,
            setFormMode,
        ] = useState<DeviceCredentialFormMode | null>(
            null
        );

        const [
            formData,
            setFormData,
        ] = useState<DeviceCredentialFormData>({
            ...EMPTY_FORM_DATA,
        });

        const [
            editingCredential,
            setEditingCredential,
        ] = useState<DeviceCredential | null>(
            null
        );


        // ====================================================
        // FECHAR / LIMPAR
        // ====================================================

        const closeForm =
            () => {

                setFormMode(
                    null
                );

                setEditingCredential(
                    null
                );

                setFormData({
                    ...EMPTY_FORM_DATA,
                });
            };


        // ====================================================
        // ABRIR CRIAÇÃO
        // ====================================================

        const openCreateForm =
            () => {

                setError(
                    ""
                );

                setSuccessMessage(
                    ""
                );

                setEditingCredential(
                    null
                );

                setFormData({
                    ...EMPTY_FORM_DATA,
                });

                setFormMode(
                    "create"
                );
            };


        // ====================================================
        // ABRIR EDIÇÃO
        // ====================================================
        //
        // A senha nunca é copiada do backend para o formulário.
        // ====================================================

        const openEditForm =
            (
                credential: DeviceCredential
            ) => {

                setError(
                    ""
                );

                setSuccessMessage(
                    ""
                );

                setEditingCredential(
                    credential
                );

                setFormData({
                    name:
                        credential.name,

                    domain:
                        credential.domain,

                    username:
                        credential.username,

                    password:
                        "",
                });

                setFormMode(
                    "edit"
                );
            };


        // ====================================================
        // ALTERAR CAMPO
        // ====================================================

        const updateField =
            (
                field:
                    keyof DeviceCredentialFormData,
                value: string
            ) => {

                setFormData(
                    (current) => ({
                        ...current,
                        [field]: value,
                    })
                );
            };


        // ====================================================
        // VALIDAÇÃO
        // ====================================================

        const validate =
            (): boolean => {

                if (
                    formMode === "create"
                    &&
                    !formData.name.trim()
                ) {

                    setError(
                        "Informe o nome da credencial."
                    );

                    return false;
                }


                if (
                    !formData.domain.trim()
                ) {

                    setError(
                        "Informe o domínio da conta Windows."
                    );

                    return false;
                }


                if (
                    !formData.username.trim()
                ) {

                    setError(
                        "Informe o usuário da conta Windows."
                    );

                    return false;
                }


                if (
                    formMode === "create"
                    &&
                    !formData.password
                ) {

                    setError(
                        "Informe a senha da conta Windows."
                    );

                    return false;
                }


                if (
                    formMode === "edit"
                    &&
                    editingCredential
                    &&
                    !editingCredential.has_password
                    &&
                    !formData.password
                ) {

                    setError(
                        "Esta credencial ainda não possui senha. Informe uma senha."
                    );

                    return false;
                }


                return true;
            };


        // ====================================================
        // SALVAR
        // ====================================================

        const submitForm =
            async (): Promise<boolean> => {

                if (
                    !formMode
                    ||
                    !validate()
                ) {

                    return false;
                }


                // --------------------------------------------
                // CRIAÇÃO
                // --------------------------------------------

                if (
                    formMode === "create"
                ) {

                    const success =
                        await createCredential({
                            name:
                                formData.name.trim(),

                            domain:
                                formData.domain.trim(),

                            username:
                                formData.username.trim(),

                            password:
                                formData.password,
                        });


                    if (
                        success
                    ) {

                        closeForm();
                    }


                    return success;
                }


                // --------------------------------------------
                // EDIÇÃO
                // --------------------------------------------

                if (
                    !editingCredential
                ) {

                    setError(
                        "Não foi possível identificar a credencial em edição."
                    );

                    return false;
                }


                const hasNewPassword =
                    formData.password !== "";


                const success =
                    await updateCredential(
                        editingCredential.id,
                        {
                            domain:
                                formData.domain.trim(),

                            username:
                                formData.username.trim(),

                            password:
                                hasNewPassword
                                    ? formData.password
                                    : "",

                            keep_existing_password:
                                !hasNewPassword,
                        }
                    );


                if (
                    success
                ) {

                    closeForm();
                }


                return success;
            };


        // ====================================================
        // RETORNO
        // ====================================================

        return {
            formMode,
            formData,
            editingCredential,

            openCreateForm,
            openEditForm,
            updateField,
            closeForm,
            submitForm,
        };
    };

// ============================================================
// DUET CORE - VAULT - CREDENTIAL EDITING HOOK
// ============================================================
//
// Hook responsável exclusivamente pela edição de credenciais.
//
// Responsabilidade:
// - iniciar edição;
// - preparar campos existentes;
// - proteger valores secretos;
// - adicionar/remover/alterar campos;
// - validar edição;
// - executar PUT /vault/credentials/{credential_id};
// - cancelar edição.
//
// REGRA CRÍTICA DE SEGURANÇA:
//
// Um campo secreto existente entra no formulário com:
//
// value = ""
// keep_existing = true
//
// Portanto o segredo real NÃO precisa retornar ao frontend.
//
// Se o usuário preencher um novo valor:
//
// keep_existing = false
//
// e o backend poderá substituir o segredo.
//
// Essa semântica foi preservada do Vault original.
// ============================================================

import {
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    EditCredentialField,
    VaultCredential,
} from "../../types/vault";


// ============================================================
// PROPS
// ============================================================

interface UseVaultCredentialEditingProps {
    setError:
        (message: string) => void;

    setSuccessMessage:
        (message: string) => void;

    reloadCredentials:
        (folderId: number) => Promise<void>;

    closeCreationForm:
        () => void;
}


// ============================================================
// HOOK
// ============================================================

export function useVaultCredentialEditing({
    setError,
    setSuccessMessage,
    reloadCredentials,
    closeCreationForm,
}: UseVaultCredentialEditingProps) {

    const [
        editingCredential,
        setEditingCredential,
    ] = useState<VaultCredential | null>(
        null
    );


    const [
        editCredentialFields,
        setEditCredentialFields,
    ] = useState<EditCredentialField[]>([]);


    const [
        updatingCredential,
        setUpdatingCredential,
    ] = useState(false);


    // ========================================================
    // INICIAR EDIÇÃO
    // ========================================================

    const iniciarEdicaoCredencial =
        (
            credential:
                VaultCredential
        ) => {

            setEditingCredential(
                credential
            );


            setEditCredentialFields(
                credential.fields.map(
                    (field) => ({
                        id:
                            field.id,

                        name:
                            field.name,

                        value:
                            field.is_secret
                                ? ""
                                : field.value,

                        is_secret:
                            field.is_secret,

                        keep_existing:
                            field.is_secret,
                    })
                )
            );


            // Preserva o comportamento atual:
            // editar fecha o formulário de nova credencial.
            closeCreationForm();

            setError("");
            setSuccessMessage("");
        };


    // ========================================================
    // ATUALIZAR CAMPO
    // ========================================================

    const atualizarCampoEdicao =
        (
            index: number,
            propriedade:
                keyof EditCredentialField,
            valor:
                string | boolean
        ) => {

            setEditCredentialFields(
                (
                    camposAtuais
                ) =>
                    camposAtuais.map(
                        (
                            field,
                            campoIndex
                        ) => {

                            if (
                                campoIndex !==
                                index
                            ) {

                                return field;
                            }


                            const campoAtualizado:
                                EditCredentialField = {
                                    ...field,
                                    [propriedade]:
                                        valor,
                                };


                            // Se um novo valor for informado em um
                            // segredo existente, ele deixa de utilizar
                            // a instrução keep_existing.
                            if (
                                propriedade ===
                                    "value" &&
                                field.is_secret &&
                                typeof valor ===
                                    "string" &&
                                valor !== ""
                            ) {

                                campoAtualizado.keep_existing =
                                    false;
                            }


                            return campoAtualizado;
                        }
                    )
            );
        };


    // ========================================================
    // ADICIONAR CAMPO
    // ========================================================

    const adicionarCampoEdicao =
        () => {

            setEditCredentialFields(
                (
                    camposAtuais
                ) => [
                    ...camposAtuais,
                    {
                        name: "",
                        value: "",
                        is_secret: false,
                        keep_existing: false,
                    },
                ]
            );
        };


    // ========================================================
    // REMOVER CAMPO
    // ========================================================

    const removerCampoEdicao =
        (
            index: number
        ) => {

            setEditCredentialFields(
                (
                    camposAtuais
                ) =>
                    camposAtuais.filter(
                        (
                            _,
                            campoIndex
                        ) =>
                            campoIndex !==
                            index
                    )
            );
        };


    // ========================================================
    // CANCELAR
    // ========================================================

    const cancelarEdicaoCredencial =
        () => {

            setEditingCredential(null);
            setEditCredentialFields([]);
            setError("");
        };


    // ========================================================
    // SALVAR
    // ========================================================

    const salvarEdicaoCredencial =
        async (
            selectedFolderId:
                number | null
        ) => {

            if (!editingCredential) {
                return;
            }


            const camposValidos =
                editCredentialFields.filter(
                    (field) =>
                        field.name.trim() !==
                        ""
                );


            if (
                camposValidos.length ===
                0
            ) {

                setError(
                    "A credencial precisa possuir pelo menos um campo."
                );

                return;
            }


            for (
                const field
                of camposValidos
            ) {

                // Segredo existente preservado não precisa
                // receber valor novamente.
                if (
                    field.is_secret &&
                    field.keep_existing
                ) {

                    continue;
                }


                if (
                    field.value.trim() ===
                    ""
                ) {

                    setError(
                        `Preencha o valor do campo "${field.name}".`
                    );

                    return;
                }
            }


            try {

                setUpdatingCredential(true);
                setError("");


                const response =
                    await api.put(
                        `/vault/credentials/${editingCredential.id}`,
                        {
                            fields:
                                camposValidos.map(
                                    (field) => ({
                                        id:
                                            field.id,

                                        name:
                                            field.name.trim(),

                                        value:
                                            field.value,

                                        is_secret:
                                            field.is_secret,

                                        keep_existing:
                                            field.keep_existing ??
                                            false,
                                    })
                                ),
                        }
                    );


                if (
                    response.data?.status !==
                    "success"
                ) {

                    setError(
                        response.data?.message ||
                        "Não foi possível atualizar a credencial."
                    );

                    return;
                }


                setSuccessMessage(
                    `Credencial "${editingCredential.name}" alterada com sucesso.`
                );


                setEditingCredential(null);
                setEditCredentialFields([]);


                if (
                    selectedFolderId !==
                    null
                ) {

                    await reloadCredentials(
                        selectedFolderId
                    );
                }

            } catch (error: any) {

                console.error(
                    "Erro ao atualizar credencial:",
                    error
                );


                setError(
                    error?.response?.data?.message ||
                    error?.response?.data?.detail ||
                    "Erro ao atualizar a credencial."
                );

            } finally {

                setUpdatingCredential(false);
            }
        };


    return {
        editingCredential,
        editCredentialFields,
        updatingCredential,

        iniciarEdicaoCredencial,
        atualizarCampoEdicao,
        adicionarCampoEdicao,
        removerCampoEdicao,
        cancelarEdicaoCredencial,
        salvarEdicaoCredencial,
    };
}
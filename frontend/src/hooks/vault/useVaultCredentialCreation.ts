// ============================================================
// DUET CORE - VAULT - CREDENTIAL CREATION HOOK
// ============================================================
//
// Hook responsável pela criação de credenciais.
//
// Responsabilidade:
// - controlar abertura do formulário;
// - controlar nome;
// - controlar campos dinâmicos;
// - adicionar/remover/alterar campos;
// - validar a credencial;
// - executar POST /vault/credentials;
// - limpar/cancelar o formulário.
//
// IMPORTANTE:
// Uma credencial obrigatoriamente recebe o folder_id da
// pasta selecionada.
//
// A regra visual que impede criação em pasta raiz continua
// pertencendo à composição da interface.
// ============================================================

import {
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    NewCredentialField,
    VaultFolder,
} from "../../types/vault";


// ============================================================
// PROPS
// ============================================================

interface UseVaultCredentialCreationProps {
    setError:
        (message: string) => void;

    setSuccessMessage:
        (message: string) => void;

    reloadCredentials:
        (folderId: number) => Promise<void>;
}


// ============================================================
// CAMPO INICIAL
// ============================================================

function criarCampoInicial():
    NewCredentialField {

    return {
        name: "",
        value: "",
        is_secret: false,
    };
}


// ============================================================
// HOOK
// ============================================================

export function useVaultCredentialCreation({
    setError,
    setSuccessMessage,
    reloadCredentials,
}: UseVaultCredentialCreationProps) {

    const [
        showNewCredentialForm,
        setShowNewCredentialForm,
    ] = useState(false);


    const [
        newCredentialName,
        setNewCredentialName,
    ] = useState("");


    const [
        newCredentialFields,
        setNewCredentialFields,
    ] = useState<NewCredentialField[]>([
        criarCampoInicial(),
    ]);


    const [
        creatingCredential,
        setCreatingCredential,
    ] = useState(false);


    // ========================================================
    // ABRIR
    // ========================================================

    const abrirNovaCredencial =
        () => {

            setShowNewCredentialForm(true);
            setError("");
        };


    // ========================================================
    // FECHAR AO TROCAR DE PASTA
    // ========================================================

    const fecharNovaCredencial =
        () => {

            setShowNewCredentialForm(false);
        };


    // ========================================================
    // ADICIONAR CAMPO
    // ========================================================

    const adicionarCampo =
        () => {

            setNewCredentialFields(
                (
                    camposAtuais
                ) => [
                    ...camposAtuais,
                    criarCampoInicial(),
                ]
            );
        };


    // ========================================================
    // REMOVER CAMPO
    // ========================================================

    const removerCampo =
        (
            index: number
        ) => {

            setNewCredentialFields(
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
    // ALTERAR CAMPO
    // ========================================================

    const atualizarCampo =
        (
            index: number,
            propriedade:
                keyof NewCredentialField,
            valor:
                string | boolean
        ) => {

            setNewCredentialFields(
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


                            return {
                                ...field,
                                [propriedade]:
                                    valor,
                            };
                        }
                    )
            );
        };


    // ========================================================
    // CANCELAR
    // ========================================================

    const cancelarNovaCredencial =
        () => {

            setShowNewCredentialForm(false);
            setNewCredentialName("");

            setNewCredentialFields([
                criarCampoInicial(),
            ]);

            setError("");
        };


    // ========================================================
    // CRIAR CREDENCIAL
    // ========================================================

    const criarCredencial =
        async (
            selectedFolder:
                VaultFolder | null
        ) => {

            if (!selectedFolder) {

                setError(
                    "Selecione uma pasta antes de criar uma credencial."
                );

                return;
            }


            if (
                !newCredentialName.trim()
            ) {

                setError(
                    "Informe o nome da credencial."
                );

                return;
            }


            const camposValidos =
                newCredentialFields.filter(
                    (field) =>
                        field.name.trim() !==
                        ""
                );


            if (
                camposValidos.length ===
                0
            ) {

                setError(
                    "Adicione pelo menos um campo à credencial."
                );

                return;
            }


            const campoSemValor =
                camposValidos.some(
                    (field) =>
                        field.value.trim() ===
                        ""
                );


            if (campoSemValor) {

                setError(
                    "Preencha o valor de todos os campos."
                );

                return;
            }


            try {

                setCreatingCredential(true);
                setError("");
                setSuccessMessage("");


                const response =
                    await api.post(
                        "/vault/credentials",
                        {
                            name:
                                newCredentialName.trim(),

                            folder_id:
                                selectedFolder.id,

                            fields:
                                camposValidos.map(
                                    (field) => ({
                                        name:
                                            field.name.trim(),

                                        value:
                                            field.value,

                                        is_secret:
                                            field.is_secret,
                                    })
                                ),
                        }
                    );


                if (
                    response.data.status !==
                    "success"
                ) {

                    setError(
                        response.data.message ||
                        "Não foi possível criar a credencial."
                    );

                    return;
                }


                setSuccessMessage(
                    `Credencial "${newCredentialName.trim()}" criada com sucesso.`
                );


                setShowNewCredentialForm(false);
                setNewCredentialName("");

                setNewCredentialFields([
                    criarCampoInicial(),
                ]);


                await reloadCredentials(
                    selectedFolder.id
                );

            } catch (err: any) {

                console.error(
                    "Erro ao criar credencial:",
                    err
                );


                setError(
                    err.response?.data?.detail ||
                    err.response?.data?.message ||
                    "Não foi possível criar a credencial."
                );

            } finally {

                setCreatingCredential(false);
            }
        };


    return {
        showNewCredentialForm,

        newCredentialName,
        setNewCredentialName,

        newCredentialFields,
        creatingCredential,

        abrirNovaCredencial,
        fecharNovaCredencial,

        adicionarCampo,
        removerCampo,
        atualizarCampo,

        cancelarNovaCredencial,
        criarCredencial,
    };
}
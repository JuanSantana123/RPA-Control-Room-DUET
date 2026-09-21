// ============================================================
// DUET CORE - VAULT - CREDENTIALS DATA HOOK
// ============================================================
//
// Hook responsável pela lista de credenciais da pasta atual.
//
// Responsabilidade:
// - buscar credenciais;
// - filtrar pela pasta selecionada;
// - controlar loading;
// - excluir uma credencial;
// - limpar a lista quando necessário.
//
// Integrações:
// - GET    /vault/credentials
// - DELETE /vault/credentials/{credential_id}
//
// IMPORTANTE:
// O endpoint retorna as credenciais e o frontend mantém
// somente aquelas cujo folder_id corresponde à pasta atual.
// Esse comportamento existente foi preservado.
// ============================================================

import {
    useCallback,
    useState,
} from "react";

import api
    from "../../services/api";

import type {
    VaultCredential,
} from "../../types/vault";


// ============================================================
// PROPS
// ============================================================

interface UseVaultCredentialsProps {
    setError:
        (message: string) => void;

    setSuccessMessage:
        (message: string) => void;
}


// ============================================================
// HOOK
// ============================================================

export function useVaultCredentials({
    setError,
    setSuccessMessage,
}: UseVaultCredentialsProps) {

    const [
        credentials,
        setCredentials,
    ] = useState<VaultCredential[]>([]);


    const [
        loadingCredentials,
        setLoadingCredentials,
    ] = useState(false);


    // ========================================================
    // CARREGAR CREDENCIAIS
    // ========================================================

    const carregarCredenciais =
        useCallback(
            async (
                folderId: number
            ) => {

                try {

                    setLoadingCredentials(true);
                    setError("");


                    const response =
                        await api.get(
                            "/vault/credentials"
                        );


                    const todasCredenciais =
                        response.data.credentials ||
                        [];


                    const credenciaisDaPasta =
                        todasCredenciais.filter(
                            (
                                credential:
                                    VaultCredential
                            ) =>
                                credential.folder_id ===
                                folderId
                        );


                    setCredentials(
                        credenciaisDaPasta
                    );

                } catch (err) {

                    console.error(
                        "Erro ao buscar credenciais do Vault:",
                        err
                    );


                    setError(
                        "Não foi possível carregar as credenciais."
                    );

                } finally {

                    setLoadingCredentials(false);
                }
            },
            [
                setError,
            ]
        );


    // ========================================================
    // LIMPAR CREDENCIAIS
    // ========================================================

    const limparCredenciais =
        () => {

            setCredentials([]);
        };


    // ========================================================
    // EXCLUIR CREDENCIAL
    // ========================================================

    const excluirCredencial =
        async (
            credential: VaultCredential,
            selectedFolderId:
                number | null
        ) => {

            const confirmar =
                window.confirm(
                    `Deseja realmente excluir a credencial "${credential.name}"?`
                );


            if (!confirmar) {
                return;
            }


            try {

                setError("");
                setSuccessMessage("");


                const response =
                    await api.delete(
                        `/vault/credentials/${credential.id}`
                    );


                if (
                    response.data?.status !==
                    "success"
                ) {

                    setError(
                        response.data?.message ||
                        "Não foi possível excluir a credencial."
                    );

                    return;
                }


                setSuccessMessage(
                    `Credencial "${credential.name}" excluída com sucesso.`
                );


                if (
                    selectedFolderId !==
                    null
                ) {

                    await carregarCredenciais(
                        selectedFolderId
                    );
                }

            } catch (error: any) {

                console.error(
                    "Erro ao excluir credencial:",
                    error
                );


                setError(
                    error?.response?.data?.message ||
                    "Erro ao excluir a credencial."
                );
            }
        };


    return {
        credentials,
        loadingCredentials,

        carregarCredenciais,
        limparCredenciais,
        excluirCredencial,
    };
}
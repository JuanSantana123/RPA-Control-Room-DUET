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
    useRef,
    useState,
} from "react";

import api
    from "../../services/api";
import { getApiErrorMessage } from "../../utils/apiErrors";
import { useInteraction } from "../../context/useInteraction";

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

    const { confirm } = useInteraction();

    const [
        credentials,
        setCredentials,
    ] = useState<VaultCredential[]>([]);


    const [
        loadingCredentials,
        setLoadingCredentials,
    ] = useState(false);

    const [refreshingCredentials, setRefreshingCredentials] = useState(false);
    const [loadedFolderId, setLoadedFolderId] = useState<number | null>(null);
    const [lastUpdatedAt, setLastUpdatedAt] = useState<Date | null>(null);
    const requestSequence = useRef(0);


    // ========================================================
    // CARREGAR CREDENCIAIS
    // ========================================================

    const carregarCredenciais =
        useCallback(
            async (
                folderId: number
            ) => {

                const sequence = ++requestSequence.current;
                const isRefresh = loadedFolderId === folderId;

                try {

                    if (isRefresh) {
                        setRefreshingCredentials(true);
                    } else {
                        setCredentials([]);
                        setLoadedFolderId(null);
                        setLoadingCredentials(true);
                    }
                    setError("");


                    const response =
                        await api.get(
                            "/vault/credentials",
                            {
                                params: {
                                    folder_id: folderId,
                                },
                            }
                        );

                    if (sequence !== requestSequence.current) return;

                    const folderCredentials = Array.isArray(response.data?.credentials)
                        ? response.data.credentials.filter(
                            (credential: VaultCredential) => credential.folder_id === folderId,
                        )
                        : [];

                    setCredentials(folderCredentials);
                    setLoadedFolderId(folderId);
                    setLastUpdatedAt(new Date());

                } catch (err) {

                    if (sequence !== requestSequence.current) return;

                    console.error(
                        "Erro ao buscar credenciais do Vault:",
                        err
                    );


                    setError(
                        getApiErrorMessage(
                            err,
                            isRefresh
                                ? "Não foi possível atualizar as credenciais. Os dados anteriores foram preservados."
                                : "Não foi possível carregar as credenciais desta pasta.",
                        )
                    );

                } finally {
                    if (sequence === requestSequence.current) {
                        setLoadingCredentials(false);
                        setRefreshingCredentials(false);
                    }
                }
            },
            [
                loadedFolderId,
                setError,
            ]
        );


    // ========================================================
    // LIMPAR CREDENCIAIS
    // ========================================================

        const limparCredenciais =
        () => {

            requestSequence.current += 1;
            setCredentials([]);
            setLoadedFolderId(null);
            setLastUpdatedAt(null);
            setLoadingCredentials(false);
            setRefreshingCredentials(false);
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

            const confirmar = await confirm({
                title: `Excluir a credencial “${credential.name}”?`,
                description: "O segredo deixará de estar disponível para novas execuções autorizadas.",
                detail: "Robôs que dependem desta credencial poderão falhar. Revise os vínculos antes de continuar.",
                confirmLabel: "Excluir credencial",
                tone: "danger",
            });


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

            } catch (error) {

                console.error(
                    "Erro ao excluir credencial:",
                    error
                );


                setError(getApiErrorMessage(error, "Erro ao excluir a credencial."));
            }
        };


    return {
        credentials,
        loadingCredentials,
        refreshingCredentials,
        lastUpdatedAt,

        carregarCredenciais,
        limparCredenciais,
        excluirCredencial,
    };
}

// ============================================================
// DUET CORE - ROBOT STUDIO - CHECKOUT
// ============================================================
//
// Responsabilidade:
// - consultar o Checkout oficial do projeto;
// - realizar Checkout;
// - realizar Checkin;
// - realizar Force Release;
// - determinar se o workspace pode ser editado;
// - manter o OUTPUT compartilhado usado pelas operações.
//
// O OUTPUT permanece aqui nesta etapa porque as operações de
// Checkout escrevem nele e o Workspace precisa chamar
// carregarCheckout() ao receber HTTP 423.
//
// Isso evita dependência circular entre os hooks sem alterar
// nenhuma regra funcional existente.
//
// NÃO controla:
// - árvore do workspace;
// - Monaco;
// - Libraries;
// - metadados do AutomationProject.
// ============================================================

import {
    useEffect,
    useState,
} from "react";

import api from "../../services/api";

import type {
    ProjectCheckoutState,
} from "../../types/robotStudio";


interface UseRobotStudioCheckoutParams {
    projectId?: string;

    permissionsLoaded: boolean;
    canViewDevelopment: boolean;
    canEditWorkspace: boolean;
    canCheckout: boolean;
    canForceCheckoutRelease: boolean;

    // Recebemos somente a quantidade.
    // O Checkout precisa saber se existem alterações para
    // impedir Checkin, mas não precisa conhecer o Workspace.
    dirtyFilesCount: number;
}


// ============================================================
// HELPER - MENSAGEM DE ERRO
// ============================================================
//
// Mesma interpretação utilizada atualmente no RobotStudio.
// ============================================================

const getApiErrorMessage = (
    err: any,
    fallback: string
): string => {

    const detail =
        err?.response?.data?.detail;


    if (typeof detail === "string") {
        return detail;
    }


    if (
        detail &&
        typeof detail === "object" &&
        typeof detail.message === "string"
    ) {
        return detail.message;
    }


    const message =
        err?.response?.data?.message;


    if (typeof message === "string") {
        return message;
    }


    if (typeof err?.message === "string") {
        return err.message;
    }


    return fallback;
};


export function useRobotStudioCheckout({
    projectId,
    permissionsLoaded,
    canViewDevelopment,
    canEditWorkspace,
    canCheckout,
    canForceCheckoutRelease,
    dirtyFilesCount,
}: UseRobotStudioCheckoutParams) {

    // ========================================================
    // OUTPUT
    // ========================================================

    const [
        showOutput,
        setShowOutput,
    ] = useState(true);


    const [
        outputLines,
        setOutputLines,
    ] = useState<string[]>([
        "[DUET] Studio inicializado.",
        "[DUET] Workspace pronto para desenvolvimento.",
    ]);


    // ========================================================
    // ESTADO DO CHECKOUT
    // ========================================================

    const [
        checkoutState,
        setCheckoutState,
    ] =
        useState<ProjectCheckoutState>({
            checked_out: false,
            owns_checkout: false,
            checkout: null,
        });


    const [
        loadingCheckout,
        setLoadingCheckout,
    ] = useState(true);


    const [
        checkoutActionLoading,
        setCheckoutActionLoading,
    ] = useState(false);


    // ========================================================
    // ESTADOS DERIVADOS
    // ========================================================

    const ownsCheckout =
        checkoutState.owns_checkout;


    // Continua exigindo exatamente:
    //
    // 1. Development:edit
    // 2. Checkout pertencente ao usuário atual.
    const canWriteWorkspace =
        canEditWorkspace &&
        ownsCheckout;


    const workspaceReadOnlyMessage =
        !canEditWorkspace
            ? (
                "Seu usuário não possui permissão Development:edit."
            )
            : checkoutState.checked_out
                ? (
                    `Projeto em Checkout por ${
                        checkoutState.checkout
                            ?.user_name ||
                        "outro usuário"
                    }.`
                )
                : canCheckout
                    ? (
                        "Realize Checkout para editar este projeto."
                    )
                    : (
                        "Seu usuário não possui permissão Development:checkout."
                    );


    // ========================================================
    // CARREGAR CHECKOUT
    // ========================================================

    const carregarCheckout =
        async (
            registrarOutput = false
        ) => {

            if (
                !projectId ||
                !permissionsLoaded ||
                !canViewDevelopment
            ) {
                return;
            }


            try {

                setLoadingCheckout(
                    true
                );


                const response =
                    await api.get(
                        `/development/projects/${projectId}/checkout`
                    );


                const novoEstado:
                    ProjectCheckoutState = {

                    checked_out:
                        Boolean(
                            response.data
                                ?.checked_out
                        ),

                    owns_checkout:
                        Boolean(
                            response.data
                                ?.owns_checkout
                        ),

                    checkout:
                        response.data
                            ?.checkout ?? null,
                };


                setCheckoutState(
                    novoEstado
                );


                if (registrarOutput) {

                    if (
                        novoEstado
                            .owns_checkout
                    ) {

                        setOutputLines(
                            (current) => [
                                ...current,
                                "[DUET] Você possui o Checkout deste projeto.",
                            ]
                        );

                    } else if (
                        novoEstado
                            .checked_out
                    ) {

                        setOutputLines(
                            (current) => [
                                ...current,

                                `[DUET] Projeto em Checkout por ${
                                    novoEstado.checkout
                                        ?.user_name ||
                                    "outro usuário"
                                }.`,
                            ]
                        );

                    } else {

                        setOutputLines(
                            (current) => [
                                ...current,

                                "[DUET] Projeto aberto em modo somente leitura.",
                            ]
                        );
                    }
                }

            } catch (err: any) {

                console.error(
                    "Erro ao consultar Checkout:",
                    err
                );


                setCheckoutState({
                    checked_out: false,
                    owns_checkout: false,
                    checkout: null,
                });


                const mensagem =
                    getApiErrorMessage(
                        err,
                        "Não foi possível consultar o Checkout."
                    );


                setOutputLines(
                    (current) => [
                        ...current,
                        `[DUET] ERRO: ${mensagem}`,
                    ]
                );

            } finally {

                setLoadingCheckout(
                    false
                );
            }
        };


    // ========================================================
    // CONSULTA INICIAL
    // ========================================================

    useEffect(() => {

        if (
            !permissionsLoaded ||
            !canViewDevelopment
        ) {
            return;
        }


        carregarCheckout(
            true
        );

    }, [
        projectId,
        permissionsLoaded,
        canViewDevelopment,
    ]);


    // ========================================================
    // REALIZAR CHECKOUT
    // ========================================================

    const realizarCheckout =
        async () => {

            if (
                !projectId ||
                !canCheckout ||
                checkoutActionLoading
            ) {
                return;
            }


            try {

                setCheckoutActionLoading(
                    true
                );


                await api.post(
                    `/development/projects/${projectId}/checkout`
                );


                await carregarCheckout(
                    false
                );


                setOutputLines(
                    (current) => [
                        ...current,

                        "[DUET] Checkout realizado. Workspace liberado para edição.",
                    ]
                );

            } catch (err: any) {

                console.error(
                    "Erro ao realizar Checkout:",
                    err
                );


                // Outro usuário pode ter adquirido o Checkout
                // antes desta requisição.
                await carregarCheckout(
                    false
                );


                const mensagem =
                    getApiErrorMessage(
                        err,
                        "Não foi possível realizar o Checkout."
                    );


                setOutputLines(
                    (current) => [
                        ...current,
                        `[DUET] CHECKOUT: ${mensagem}`,
                    ]
                );

            } finally {

                setCheckoutActionLoading(
                    false
                );
            }
        };


    // ========================================================
    // REALIZAR CHECKIN
    // ========================================================

    const realizarCheckin =
        async () => {

            if (
                !projectId ||
                !canCheckout ||
                !ownsCheckout ||
                checkoutActionLoading
            ) {
                return;
            }


            // Mantém exatamente o bloqueio existente:
            // nenhum Checkin com arquivo não salvo.
            if (
                dirtyFilesCount > 0
            ) {

                setOutputLines(
                    (current) => [
                        ...current,

                        "[DUET] CHECKIN BLOQUEADO: salve as alterações antes de liberar o projeto.",
                    ]
                );

                return;
            }


            try {

                setCheckoutActionLoading(
                    true
                );


                await api.post(
                    `/development/projects/${projectId}/checkin`
                );


                await carregarCheckout(
                    false
                );


                setOutputLines(
                    (current) => [
                        ...current,

                        "[DUET] Checkin realizado. Projeto voltou para modo somente leitura.",
                    ]
                );

            } catch (err: any) {

                console.error(
                    "Erro ao realizar Checkin:",
                    err
                );


                await carregarCheckout(
                    false
                );


                const mensagem =
                    getApiErrorMessage(
                        err,
                        "Não foi possível realizar o Checkin."
                    );


                setOutputLines(
                    (current) => [
                        ...current,
                        `[DUET] CHECKIN: ${mensagem}`,
                    ]
                );

            } finally {

                setCheckoutActionLoading(
                    false
                );
            }
        };


    // ========================================================
    // FORCE RELEASE
    // ========================================================

    const realizarForceReleaseCheckout =
        async () => {

            if (
                !projectId ||
                !canForceCheckoutRelease ||
                !checkoutState.checked_out ||
                ownsCheckout ||
                checkoutActionLoading
            ) {
                return;
            }


            const checkoutOwner =
                checkoutState.checkout
                    ?.user_name ||
                "outro usuário";


            const confirmed =
                window.confirm(
                    `Forçar a liberação do Checkout de ${checkoutOwner}?\n\n` +
                    "O usuário perderá o bloqueio de edição deste projeto."
                );


            if (!confirmed) {
                return;
            }


            try {

                setCheckoutActionLoading(
                    true
                );


                await api.post(
                    `/development/projects/${projectId}/checkout/force-release`
                );


                await carregarCheckout(
                    false
                );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] Force Release realizado. Checkout de ${checkoutOwner} liberado.`,
                    ]
                );

            } catch (err: any) {

                console.error(
                    "Erro ao realizar Force Release:",
                    err
                );


                await carregarCheckout(
                    false
                );


                const mensagem =
                    getApiErrorMessage(
                        err,
                        "Não foi possível forçar a liberação do Checkout."
                    );


                setOutputLines(
                    (current) => [
                        ...current,

                        `[DUET] FORCE RELEASE: ${mensagem}`,
                    ]
                );

            } finally {

                setCheckoutActionLoading(
                    false
                );
            }
        };


    return {
        // Checkout.
        checkoutState,
        loadingCheckout,
        checkoutActionLoading,

        ownsCheckout,
        canWriteWorkspace,
        workspaceReadOnlyMessage,

        carregarCheckout,
        realizarCheckout,
        realizarCheckin,
        realizarForceReleaseCheckout,

        // OUTPUT compartilhado.
        showOutput,
        setShowOutput,
        outputLines,
        setOutputLines,
    };
}
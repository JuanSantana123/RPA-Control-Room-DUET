// ============================================================
// USE DEVELOPMENT CARD DETAILS
// ============================================================
//
// Responsabilidade:
//     Centraliza o estado e a orquestração do painel lateral
//     de detalhes de um card do Kanban de Desenvolvimento.
//
// O hook controla:
//     - projeto atualmente aberto;
//     - usuários disponíveis para responsáveis;
//     - comentários do projeto;
//     - responsável funcional;
//     - responsável técnico;
//     - data de início;
//     - data prevista;
//     - esforço estimado;
//     - novo comentário;
//     - carregamento;
//     - salvamento;
//     - inclusão de comentário;
//     - erro específico do painel.
//
// Integrações:
//     GET  /development/card-users
//     GET  /development/projects/{id}/comments
//     PATCH /development/projects/{id}/card-details
//     POST /development/projects/{id}/comments
//
// O hook recebe:
//     - permissão de edição;
//     - callback para atualizar o Kanban depois de alterações.
//
// Este arquivo NÃO deve:
//     - renderizar CardDetailsPanel;
//     - controlar drag-and-drop;
//     - movimentar cards;
//     - controlar Release;
//     - controlar execução;
//     - controlar Lixeira;
//     - controlar navegação da página.
//
// CardDetailsPanel continua sendo exclusivamente visual.
// ============================================================

import {
    useRef,
    useState,
} from "react";


import api
    from "../../services/api";


import {
    getApiErrorMessage,
} from "../../utils/apiErrors";


import type {
    CardComment,
    CardUser,
    DevelopmentProject,
} from "../../types/development";


// ============================================================
// PARÂMETROS
// ============================================================

interface UseDevelopmentCardDetailsParams {

    // Permissão Development:edit já calculada pela página.
    canEditDevelopment:
        boolean;


    // Depois de salvar planejamento ou adicionar comentário,
    // o board precisa ser recarregado para refletir:
    //
    // - responsáveis;
    // - datas;
    // - esforço;
    // - contador de comentários.
    onRefreshKanban:
        () => Promise<void>;
}


// ============================================================
// RETORNO
// ============================================================

interface UseDevelopmentCardDetailsResult {

    // Projeto atualmente aberto no painel.
    selectedCardProject:
        DevelopmentProject | null;


    // Dados auxiliares carregados do backend.
    cardUsers:
        CardUser[];

    cardComments:
        CardComment[];


    // Campos editáveis.
    cardFunctionalResponsibleId:
        string;

    cardTechnicalResponsibleId:
        string;

    cardStartDate:
        string;

    cardDueDate:
        string;

    cardEffortHours:
        string;

    newCardComment:
        string;


    // Estados operacionais.
    loadingCardDetails:
        boolean;

    savingCardDetails:
        boolean;

    addingCardComment:
        boolean;

    cardDetailsError:
        string;


    // Alterações dos campos.
    setCardFunctionalResponsibleId:
        (value: string) => void;

    setCardTechnicalResponsibleId:
        (value: string) => void;

    setCardStartDate:
        (value: string) => void;

    setCardDueDate:
        (value: string) => void;

    setCardEffortHours:
        (value: string) => void;

    setNewCardComment:
        (value: string) => void;


    // Ações do painel.
    openCardDetails:
        (
            project: DevelopmentProject
        ) => Promise<void>;

    closeCardDetails:
        () => void;

    saveCardDetails:
        () => Promise<void>;

    addCardComment:
        () => Promise<void>;
}


// ============================================================
// HOOK
// ============================================================

function useDevelopmentCardDetails({
    canEditDevelopment,
    onRefreshKanban,
}: UseDevelopmentCardDetailsParams): UseDevelopmentCardDetailsResult {

    // ========================================================
    // ESTADOS
    // ========================================================

    const [
        selectedCardProject,
        setSelectedCardProject,
    ] =
        useState<DevelopmentProject | null>(
            null
        );


    const [
        cardUsers,
        setCardUsers,
    ] =
        useState<CardUser[]>([]);


    const [
        cardComments,
        setCardComments,
    ] =
        useState<CardComment[]>([]);


    // IDs permanecem como string porque são ligados
    // diretamente aos elementos <select>.
    const [
        cardFunctionalResponsibleId,
        setCardFunctionalResponsibleId,
    ] =
        useState("");


    const [
        cardTechnicalResponsibleId,
        setCardTechnicalResponsibleId,
    ] =
        useState("");


    const [
        cardStartDate,
        setCardStartDate,
    ] =
        useState("");


    const [
        cardDueDate,
        setCardDueDate,
    ] =
        useState("");


    // String permite manter o input vazio.
    const [
        cardEffortHours,
        setCardEffortHours,
    ] =
        useState("");


    const [
        newCardComment,
        setNewCardComment,
    ] =
        useState("");


    const [
        loadingCardDetails,
        setLoadingCardDetails,
    ] =
        useState(false);


    const [
        savingCardDetails,
        setSavingCardDetails,
    ] =
        useState(false);


    const [
        addingCardComment,
        setAddingCardComment,
    ] =
        useState(false);


    const [
        cardDetailsError,
        setCardDetailsError,
    ] =
        useState("");


    // ========================================================
    // CONTROLE DE RESPOSTAS ASSÍNCRONAS
    // ========================================================
    //
    // Cada abertura recebe um identificador.
    //
    // Se o usuário fechar o painel ou abrir outro projeto
    // antes do GET anterior terminar, aquela resposta antiga
    // não poderá atualizar o painel atual.
    // ========================================================

    const cardDetailsLoadId =
        useRef(0);


    // ========================================================
    // ABRIR DETALHES
    // ========================================================

    const openCardDetails = async (
        project: DevelopmentProject
    ) => {

        const loadId =
            ++cardDetailsLoadId.current;


        // Abre imediatamente usando os dados que já vieram
        // do Workflow/Kanban.
        setSelectedCardProject(
            project
        );


        setCardFunctionalResponsibleId(
            project.functional_responsible_id !== null
                ? String(
                    project.functional_responsible_id
                )
                : ""
        );


        setCardTechnicalResponsibleId(
            project.technical_responsible_id !== null
                ? String(
                    project.technical_responsible_id
                )
                : ""
        );


        setCardStartDate(
            project.start_date || ""
        );


        setCardDueDate(
            project.due_date || ""
        );


        setCardEffortHours(
            project.effort_hours !== null
                ? String(
                    project.effort_hours
                )
                : ""
        );


        setNewCardComment("");
        setCardComments([]);
        setCardUsers([]);
        setCardDetailsError("");
        setLoadingCardDetails(true);


        try {

            // Usuários e comentários são independentes.
            // Os dois requests continuam paralelos.
            const [
                usersResponse,
                commentsResponse,
            ] =
                await Promise.all([
                    api.get(
                        "/development/card-users"
                    ),

                    api.get(
                        `/development/projects/${project.id}/comments`
                    ),
                ]);


            // O painel pode ter sido fechado ou trocado
            // enquanto os requests estavam em andamento.
            if (
                loadId !==
                cardDetailsLoadId.current
            ) {
                return;
            }


            setCardUsers(
                usersResponse.data?.users || []
            );


            setCardComments(
                commentsResponse.data?.comments || []
            );

        } catch (err: any) {

            if (
                loadId !==
                cardDetailsLoadId.current
            ) {
                return;
            }


            console.error(
                "Erro ao carregar detalhes do card:",
                err
            );


            setCardDetailsError(
                getApiErrorMessage(
                    err,
                    "Não foi possível carregar os detalhes do card."
                )
            );

        } finally {

            if (
                loadId ===
                cardDetailsLoadId.current
            ) {

                setLoadingCardDetails(
                    false
                );
            }
        }
    };


    // ========================================================
    // FECHAR DETALHES
    // ========================================================

    const closeCardDetails = () => {

        // Mantém a proteção existente contra fechamento
        // enquanto uma gravação está em andamento.
        if (
            savingCardDetails ||
            addingCardComment
        ) {
            return;
        }


        // Invalida GETs anteriores ainda em andamento.
        ++cardDetailsLoadId.current;


        setSelectedCardProject(
            null
        );


        setCardUsers([]);
        setCardComments([]);
        setCardDetailsError("");
        setNewCardComment("");
    };


    // ========================================================
    // SALVAR PLANEJAMENTO
    // ========================================================

    const saveCardDetails = async () => {

        if (
            !selectedCardProject ||
            !canEditDevelopment ||
            savingCardDetails
        ) {
            return;
        }


        // Aceita:
        //
        // 16.5
        // 16,5
        //
        // O backend recebe número ou null.
        const normalizedEffort =
            cardEffortHours
                .trim()
                .replace(",", ".");


        const effortValue =
            normalizedEffort === ""
                ? null
                : Number(
                    normalizedEffort
                );


        if (
            effortValue !== null &&
            (
                !Number.isFinite(
                    effortValue
                ) ||
                effortValue < 0
            )
        ) {

            setCardDetailsError(
                "Informe uma quantidade de horas válida."
            );

            return;
        }


        try {

            setSavingCardDetails(
                true
            );


            setCardDetailsError("");


            const response =
                await api.patch(
                    `/development/projects/${selectedCardProject.id}/card-details`,
                    {
                        functional_responsible_id:
                            cardFunctionalResponsibleId
                                ? Number(
                                    cardFunctionalResponsibleId
                                )
                                : null,

                        technical_responsible_id:
                            cardTechnicalResponsibleId
                                ? Number(
                                    cardTechnicalResponsibleId
                                )
                                : null,

                        start_date:
                            cardStartDate || null,

                        due_date:
                            cardDueDate || null,

                        effort_hours:
                            effortValue,
                    }
                );


            const updatedProject:
                DevelopmentProject | undefined =
                    response.data?.project;


            if (updatedProject) {

                // Checkout possui fluxo independente.
                //
                // O PATCH de planejamento pode não devolvê-lo,
                // portanto preservamos o Checkout que o board
                // já possuía.
                setSelectedCardProject(
                    (current) =>
                        current
                            ? {
                                ...current,
                                ...updatedProject,

                                checkout:
                                    current.checkout,
                            }
                            : updatedProject
                );


                // Sincroniza os inputs com qualquer
                // normalização realizada pelo backend.
                setCardFunctionalResponsibleId(
                    updatedProject.functional_responsible_id !== null
                        ? String(
                            updatedProject.functional_responsible_id
                        )
                        : ""
                );


                setCardTechnicalResponsibleId(
                    updatedProject.technical_responsible_id !== null
                        ? String(
                            updatedProject.technical_responsible_id
                        )
                        : ""
                );


                setCardStartDate(
                    updatedProject.start_date || ""
                );


                setCardDueDate(
                    updatedProject.due_date || ""
                );


                setCardEffortHours(
                    updatedProject.effort_hours !== null
                        ? String(
                            updatedProject.effort_hours
                        )
                        : ""
                );
            }


            // Atualiza também o resumo apresentado no Kanban.
            await onRefreshKanban();

        } catch (err: any) {

            console.error(
                "Erro ao salvar detalhes do card:",
                err
            );


            setCardDetailsError(
                getApiErrorMessage(
                    err,
                    "Não foi possível salvar os detalhes do card."
                )
            );

        } finally {

            setSavingCardDetails(
                false
            );
        }
    };


    // ========================================================
    // ADICIONAR COMENTÁRIO
    // ========================================================

    const addCardComment = async () => {

        if (
            !selectedCardProject ||
            !canEditDevelopment ||
            addingCardComment
        ) {
            return;
        }


        const content =
            newCardComment.trim();


        if (!content) {
            return;
        }


        try {

            setAddingCardComment(
                true
            );


            setCardDetailsError("");


            const response =
                await api.post(
                    `/development/projects/${selectedCardProject.id}/comments`,
                    {
                        content,
                    }
                );


            const createdComment:
                CardComment | undefined =
                    response.data?.comment;


            if (createdComment) {

                setCardComments(
                    (current) => [
                        ...current,
                        createdComment,
                    ]
                );


                // Atualiza imediatamente o contador dentro
                // do projeto atualmente aberto.
                setSelectedCardProject(
                    (current) =>
                        current
                            ? {
                                ...current,

                                comments_count:
                                    (
                                        current.comments_count ||
                                        0
                                    ) + 1,
                            }
                            : current
                );
            }


            setNewCardComment("");


            // Atualiza o contador apresentado no card do Kanban.
            await onRefreshKanban();

        } catch (err: any) {

            console.error(
                "Erro ao adicionar comentário:",
                err
            );


            setCardDetailsError(
                getApiErrorMessage(
                    err,
                    "Não foi possível adicionar o comentário."
                )
            );

        } finally {

            setAddingCardComment(
                false
            );
        }
    };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        selectedCardProject,
        cardUsers,
        cardComments,

        cardFunctionalResponsibleId,
        cardTechnicalResponsibleId,
        cardStartDate,
        cardDueDate,
        cardEffortHours,
        newCardComment,

        loadingCardDetails,
        savingCardDetails,
        addingCardComment,
        cardDetailsError,

        setCardFunctionalResponsibleId,
        setCardTechnicalResponsibleId,
        setCardStartDate,
        setCardDueDate,
        setCardEffortHours,
        setNewCardComment,

        openCardDetails,
        closeCardDetails,
        saveCardDetails,
        addCardComment,
    };
}


export default useDevelopmentCardDetails;
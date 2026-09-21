// ============================================================
// USE DEVELOPMENT RELEASE
// ============================================================
//
// Responsabilidade:
//     Centraliza todo o fluxo operacional de Release de um
//     AutomationProject.
//
// O hook controla:
//     - projeto preparado para publicação;
//     - confirmação digitada pelo usuário;
//     - preview retornado pelo backend;
//     - pasta de destino;
//     - criação opcional de nova pasta;
//     - nome definitivo do Robot;
//     - versões de Libraries existentes;
//     - seleção de novos pacotes como Libraries;
//     - loading da prévia;
//     - publicação em andamento;
//     - erro específico do Release;
//     - proteção contra respostas assíncronas antigas.
//
// Integrações:
//     GET  /development/projects/{id}/release/preview
//     POST /development/projects/{id}/publish
//
// A página fornece:
//     - permissão efetiva de publicação;
//     - callback para remover da lista ativa o projeto publicado;
//     - callback para atualizar o Kanban;
//     - callback para exibir a mensagem global de sucesso;
//     - callback para limpar erro global antes da publicação.
//
// Este arquivo NÃO deve:
//     - renderizar PublishModal;
//     - controlar Kanban visual;
//     - controlar drag-and-drop;
//     - controlar execução;
//     - controlar Lixeira;
//     - controlar Card Details;
//     - navegar para o Studio.
//
// O PublishModal permanece exclusivamente visual.
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
    DevelopmentProject,
    ReleasePreview,
} from "../../types/development";


// ============================================================
// TIPOS INTERNOS
// ============================================================

interface NewReleaseLibrary {

    // Nome definitivo da Library que será publicada.
    name:
        string;


    // Versão inicial escolhida no Release.
    version:
        string;
}


// ============================================================
// PARÂMETROS
// ============================================================

interface UseDevelopmentReleaseParams {

    // Permissão Development:publish já calculada pela página.
    canPublishDevelopment:
        boolean;


    // Remove da lista ativa o AutomationProject que acabou
    // de ser publicado.
    onProjectPublished:
        (
            project: DevelopmentProject
        ) => void;


    // Atualiza o Workflow depois que o Release for concluído.
    onRefreshKanban:
        () => Promise<void>;


    // Exibe feedback global de sucesso no toolbar.
    onSuccess:
        (
            message: string
        ) => void;


    // Permite limpar/alterar o erro geral da página sem fazer
    // o hook conhecer a implementação visual desse feedback.
    onGlobalError:
        (
            message: string
        ) => void;
}


// ============================================================
// RETORNO
// ============================================================

interface UseDevelopmentReleaseResult {

    // Projeto atualmente preparado para publicação.
    projectToPublish:
        DevelopmentProject | null;


    // Confirmação digitada pelo usuário.
    publishConfirmation:
        string;


    // ID do projeto cuja publicação está em andamento.
    publishingProjectId:
        number | null;


    // Erro específico apresentado dentro do PublishModal.
    publishError:
        string;


    // Preview oficial devolvido pelo backend.
    releasePreview:
        ReleasePreview | null;


    // Loading do GET de preview.
    loadingRelease:
        boolean;


    // Dados de destino do Robot.
    releaseFolderId:
        string;

    newReleaseFolder:
        string;

    releaseRobotName:
        string;


    // Versões escolhidas para Libraries existentes modificadas.
    releaseLibraryVersions:
        Record<number, string>;


    // Pacotes próprios escolhidos para virar novas Libraries.
    newReleaseLibraries:
        Record<string, NewReleaseLibrary>;


    // Alterações simples utilizadas pelo PublishModal.
    setPublishConfirmation:
        (value: string) => void;

    setReleaseFolderId:
        (value: string) => void;

    setNewReleaseFolder:
        (value: string) => void;

    setReleaseRobotName:
        (value: string) => void;


    // Ações específicas das Libraries.
    changeLibraryVersion:
        (
            libraryId: number,
            version: string
        ) => void;

    toggleNewLibrary:
        (
            namespace: string,
            checked: boolean
        ) => void;

    changeNewLibraryName:
        (
            namespace: string,
            name: string
        ) => void;

    changeNewLibraryVersion:
        (
            namespace: string,
            version: string
        ) => void;


    // Fluxo principal.
    openPublishConfirmation:
        (
            project: DevelopmentProject
        ) => Promise<void>;

    closePublishConfirmation:
        () => void;

    publishProject:
        () => Promise<void>;
}


// ============================================================
// HOOK
// ============================================================

function useDevelopmentRelease({
    canPublishDevelopment,
    onProjectPublished,
    onRefreshKanban,
    onSuccess,
    onGlobalError,
}: UseDevelopmentReleaseParams): UseDevelopmentReleaseResult {

    // ========================================================
    // ESTADOS
    // ========================================================

    const [
        projectToPublish,
        setProjectToPublish,
    ] =
        useState<DevelopmentProject | null>(
            null
        );


    const [
        publishConfirmation,
        setPublishConfirmation,
    ] =
        useState("");


    const [
        publishingProjectId,
        setPublishingProjectId,
    ] =
        useState<number | null>(
            null
        );


    const [
        publishError,
        setPublishError,
    ] =
        useState("");


    const [
        releasePreview,
        setReleasePreview,
    ] =
        useState<ReleasePreview | null>(
            null
        );


    const [
        loadingRelease,
        setLoadingRelease,
    ] =
        useState(false);


    const [
        releaseFolderId,
        setReleaseFolderId,
    ] =
        useState("");


    const [
        newReleaseFolder,
        setNewReleaseFolder,
    ] =
        useState("");


    const [
        releaseRobotName,
        setReleaseRobotName,
    ] =
        useState("");


    const [
        releaseLibraryVersions,
        setReleaseLibraryVersions,
    ] =
        useState<Record<number, string>>(
            {}
        );


    const [
        newReleaseLibraries,
        setNewReleaseLibraries,
    ] =
        useState<
            Record<
                string,
                NewReleaseLibrary
            >
        >(
            {}
        );


    // ========================================================
    // PROTEÇÃO CONTRA RESPOSTAS ANTIGAS
    // ========================================================
    //
    // Cada abertura do modal recebe um identificador.
    //
    // Fechar o modal ou abrir outro projeto invalida qualquer
    // GET de preview anterior que ainda esteja em andamento.
    // ========================================================

    const releaseLoadId =
        useRef(0);


    // ========================================================
    // LIBRARY EXISTENTE - ALTERAR VERSÃO
    // ========================================================

    const changeLibraryVersion = (
        libraryId: number,
        version: string
    ) => {

        setReleaseLibraryVersions(
            (current) => ({
                ...current,

                [libraryId]:
                    version,
            })
        );
    };


    // ========================================================
    // NOVA LIBRARY - SELECIONAR / REMOVER
    // ========================================================

    const toggleNewLibrary = (
        namespace: string,
        checked: boolean
    ) => {

        setNewReleaseLibraries(
            (current) => {

                // Mantém atualização imutável do estado.
                const next = {
                    ...current,
                };


                if (checked) {

                    // Mantém exatamente a regra atual:
                    // uma nova Library começa em 1.0.0.
                    next[namespace] = {
                        name:
                            namespace,

                        version:
                            "1.0.0",
                    };

                } else {

                    delete next[
                        namespace
                    ];
                }


                return next;
            }
        );
    };


    // ========================================================
    // NOVA LIBRARY - ALTERAR NOME
    // ========================================================

    const changeNewLibraryName = (
        namespace: string,
        name: string
    ) => {

        setNewReleaseLibraries(
            (current) => ({
                ...current,

                [namespace]: {
                    ...current[
                        namespace
                    ],

                    name,
                },
            })
        );
    };


    // ========================================================
    // NOVA LIBRARY - ALTERAR VERSÃO
    // ========================================================

    const changeNewLibraryVersion = (
        namespace: string,
        version: string
    ) => {

        setNewReleaseLibraries(
            (current) => ({
                ...current,

                [namespace]: {
                    ...current[
                        namespace
                    ],

                    version,
                },
            })
        );
    };


    // ========================================================
    // ABRIR CONFIRMAÇÃO / CARREGAR PREVIEW
    // ========================================================

    const openPublishConfirmation = async (
        project: DevelopmentProject
    ) => {

        if (!canPublishDevelopment) {
            return;
        }


        const loadId =
            ++releaseLoadId.current;


        setPublishError("");
        setPublishConfirmation("");

        setProjectToPublish(
            project
        );

        setReleasePreview(
            null
        );

        setReleaseFolderId("");
        setNewReleaseFolder("");


        // O título da demanda NÃO define o nome do Robot.
        //
        // Para Robot novo, o usuário escolherá o nome
        // definitivo durante o primeiro Release.
        setReleaseRobotName("");


        setReleaseLibraryVersions({});
        setNewReleaseLibraries({});

        setLoadingRelease(
            true
        );


        try {

            const response =
                await api.get(
                    `/development/projects/${project.id}/release/preview`
                );


            // Ignora resposta pertencente a modal antigo.
            if (
                loadId !==
                releaseLoadId.current
            ) {
                return;
            }


            const preview:
                ReleasePreview =
                    response.data;


            setReleasePreview(
                preview
            );


            setReleaseFolderId(
                preview.robot?.folder_id == null
                    ? ""
                    : String(
                        preview.robot.folder_id
                    )
            );


            // Robot existente mantém automaticamente seu
            // nome atual.
            //
            // Robot novo permanece vazio para que o nome
            // de Produção seja explicitamente informado.
            setReleaseRobotName(
                preview.robot?.name || ""
            );


            // Apenas Libraries existentes modificadas
            // precisam de escolha de nova versão.
            setReleaseLibraryVersions(
                Object.fromEntries(
                    preview.dependencies
                        .filter(
                            (item) =>
                                item.modified
                        )
                        .map(
                            (item) => [
                                item.library_id,
                                item.suggested_version,
                            ]
                        )
                )
            );

        } catch (err: any) {

            if (
                loadId !==
                releaseLoadId.current
            ) {
                return;
            }


            setPublishError(
                getApiErrorMessage(
                    err,
                    "Não foi possível preparar o Release."
                )
            );

        } finally {

            if (
                loadId ===
                releaseLoadId.current
            ) {

                setLoadingRelease(
                    false
                );
            }
        }
    };


    // ========================================================
    // FECHAR MODAL
    // ========================================================

    const closePublishConfirmation = () => {

        // Não permite fechar durante o POST de publicação.
        if (
            publishingProjectId !== null
        ) {
            return;
        }


        // Invalida qualquer preview ainda em andamento.
        ++releaseLoadId.current;


        setReleasePreview(
            null
        );


        setProjectToPublish(
            null
        );


        setPublishConfirmation("");
        setPublishError("");
    };


    // ========================================================
    // PUBLICAR PROJETO
    // ========================================================

    const publishProject = async () => {

        if (
            !canPublishDevelopment ||
            !projectToPublish ||
            !releasePreview ||
            loadingRelease ||
            publishingProjectId !== null
        ) {
            return;
        }


        // Mantém a confirmação forte já existente:
        // deve ser digitado exatamente o título da demanda.
        if (
            publishConfirmation !==
            projectToPublish.name
        ) {
            return;
        }


        try {

            setPublishingProjectId(
                projectToPublish.id
            );


            setPublishError("");


            // Limpa o feedback de erro geral da página antes
            // de iniciar uma nova publicação.
            onGlobalError(
                ""
            );


            const response =
                await api.post(
                    `/development/projects/${projectToPublish.id}/publish`,
                    {
                        confirmation_name:
                            publishConfirmation,

                        preview_token:
                            releasePreview.preview_token,

                        folder_id:
                            releaseFolderId
                                ? Number(
                                    releaseFolderId
                                )
                                : null,

                        new_folder_path:
                            releasePreview.robot
                                ? ""
                                : newReleaseFolder.trim(),

                        robot_name:
                            releaseRobotName.trim(),

                        library_versions:
                            releaseLibraryVersions,

                        new_libraries:
                            Object.entries(
                                newReleaseLibraries
                            ).map(
                                ([
                                    import_name,
                                    values,
                                ]) => ({
                                    import_name,
                                    ...values,
                                })
                            ),
                    }
                );


            // ====================================================
            // FEEDBACK DE SUCESSO
            // ====================================================

            onSuccess(
                `Release publicado: ${response.data.release.robot_name} — versão ${response.data.release.version}.`
            );


            const publishedProject:
                DevelopmentProject | undefined =
                    response.data?.project;


            if (publishedProject) {

                // A página continua dona da lista oficial
                // de AutomationProjects ativos.
                onProjectPublished(
                    publishedProject
                );
            }


            // Fecha o estado lógico do modal somente depois
            // da confirmação do backend.
            setProjectToPublish(
                null
            );


            setPublishConfirmation("");
            setPublishError("");


            // Atualiza o Workflow para refletir a publicação.
            await onRefreshKanban();

        } catch (err: any) {

            console.error(
                "Erro ao publicar projeto:",
                err
            );


            setPublishError(
                getApiErrorMessage(
                    err,
                    "Não foi possível publicar o projeto."
                )
            );

        } finally {

            setPublishingProjectId(
                null
            );
        }
    };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        projectToPublish,
        publishConfirmation,
        publishingProjectId,
        publishError,

        releasePreview,
        loadingRelease,

        releaseFolderId,
        newReleaseFolder,
        releaseRobotName,

        releaseLibraryVersions,
        newReleaseLibraries,

        setPublishConfirmation,
        setReleaseFolderId,
        setNewReleaseFolder,
        setReleaseRobotName,

        changeLibraryVersion,
        toggleNewLibrary,
        changeNewLibraryName,
        changeNewLibraryVersion,

        openPublishConfirmation,
        closePublishConfirmation,
        publishProject,
    };
}


export default useDevelopmentRelease;
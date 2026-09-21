// ============================================================
// USE DEVELOPMENT PROJECT CREATION
// ============================================================
//
// Responsabilidade:
//     Centraliza todo o fluxo operacional de criação de um
//     AutomationProject na área de Desenvolvimento.
//
// O hook controla:
//     - abertura/fechamento do formulário;
//     - modo de origem: Novo Robô ou Robô existente;
//     - Robot de Produção selecionado;
//     - estrutura de pastas de Produção;
//     - Robots disponíveis;
//     - pasta atualmente navegada;
//     - título da demanda;
//     - descrição da demanda;
//     - carregamento da estrutura de Produção;
//     - criação do AutomationProject;
//     - limpeza do formulário após criação/cancelamento.
//
// Integrações:
//     GET  /development/release/robots
//     POST /development/projects
//
// A página fornece:
//     - permissão efetiva de criação;
//     - callback executado quando o backend confirma o projeto;
//     - callback para atualização opcional do Kanban;
//     - callback para feedback global de erro.
//
// Este arquivo NÃO deve:
//     - renderizar CreateProjectForm;
//     - controlar a lista visual de projetos;
//     - controlar Kanban;
//     - controlar Release;
//     - controlar execução;
//     - controlar Lixeira;
//     - navegar para o Studio.
//
// CreateProjectForm permanece exclusivamente visual.
// ============================================================

import {
    useEffect,
    useState,
} from "react";


import api
    from "../../services/api";


import {
    getApiErrorMessage,
} from "../../utils/apiErrors";


import type {
    DevelopmentProject,
    OriginRobot,
    OriginRobotFolder,
    ProjectOriginMode,
} from "../../types/development";


// ============================================================
// PARÂMETROS
// ============================================================

interface UseDevelopmentProjectCreationParams {

    // Permissão Development:create calculada pela página.
    canCreateDevelopment:
        boolean;


    // Informa se a página está atualmente no Kanban.
    //
    // Mantemos essa informação como boolean para o hook não
    // precisar conhecer DevelopmentViewMode.
    isKanbanView:
        boolean;


    // Chamado somente depois que o backend confirmar
    // a criação do AutomationProject.
    onProjectCreated:
        (
            project: DevelopmentProject
        ) => void;


    // Atualiza o Workflow quando o projeto for criado
    // enquanto o usuário estiver visualizando o Kanban.
    onRefreshKanban:
        () => Promise<void>;


    // Feedback global permanece pertencendo à página.
    onError:
        (
            message: string
        ) => void;
}


// ============================================================
// RETORNO
// ============================================================

interface UseDevelopmentProjectCreationResult {

    // Controle visual do formulário.
    showCreateForm:
        boolean;


    // Origem da automação.
    projectOriginMode:
        ProjectOriginMode;

    baseRobotId:
        string;


    // Estrutura de Produção.
    originFolders:
        OriginRobotFolder[];

    originRobots:
        OriginRobot[];

    selectedOriginFolderId:
        number | null;

    originRobotsError:
        string;


    // Dados da demanda.
    newProjectName:
        string;

    newProjectDescription:
        string;


    // Estado operacional do POST.
    creatingProject:
        boolean;


    // Setters utilizados diretamente pelo formulário visual.
    setProjectOriginMode:
        (value: ProjectOriginMode) => void;

    setBaseRobotId:
        (value: string) => void;

    setSelectedOriginFolderId:
        (value: number | null) => void;

    setNewProjectName:
        (value: string) => void;

    setNewProjectDescription:
        (value: string) => void;


    // Ações públicas.
    openCreateForm:
        () => void;

    closeCreateForm:
        () => void;

    createProject:
        () => Promise<void>;
}


// ============================================================
// HOOK
// ============================================================

function useDevelopmentProjectCreation({
    canCreateDevelopment,
    isKanbanView,
    onProjectCreated,
    onRefreshKanban,
    onError,
}: UseDevelopmentProjectCreationParams): UseDevelopmentProjectCreationResult {

    // ========================================================
    // ESTADOS - FORMULÁRIO
    // ========================================================

    const [
        showCreateForm,
        setShowCreateForm,
    ] =
        useState(false);


    const [
        projectOriginMode,
        setProjectOriginMode,
    ] =
        useState<ProjectOriginMode>(
            "new"
        );


    // String facilita o uso direto no <select>.
    const [
        baseRobotId,
        setBaseRobotId,
    ] =
        useState("");


    // ========================================================
    // ESTADOS - ESTRUTURA DE PRODUÇÃO
    // ========================================================

    const [
        originFolders,
        setOriginFolders,
    ] =
        useState<OriginRobotFolder[]>([]);


    const [
        originRobots,
        setOriginRobots,
    ] =
        useState<OriginRobot[]>([]);


    // null representa a raiz de Robôs.
    const [
        selectedOriginFolderId,
        setSelectedOriginFolderId,
    ] =
        useState<number | null>(
            null
        );


    const [
        originRobotsError,
        setOriginRobotsError,
    ] =
        useState("");


    // ========================================================
    // ESTADOS - DADOS DA DEMANDA
    // ========================================================

    const [
        newProjectName,
        setNewProjectName,
    ] =
        useState("");


    const [
        newProjectDescription,
        setNewProjectDescription,
    ] =
        useState("");


    const [
        creatingProject,
        setCreatingProject,
    ] =
        useState(false);


    // ========================================================
    // LIMPEZA DO FORMULÁRIO
    // ========================================================
    //
    // Centraliza a mesma limpeza que hoje está distribuída
    // entre:
    //
    // - abertura;
    // - cancelamento;
    // - criação concluída.
    //
    // Não altera dados globais da página.
    // ========================================================

    const resetCreateForm = () => {

        setProjectOriginMode(
            "new"
        );


        setBaseRobotId(
            ""
        );


        setSelectedOriginFolderId(
            null
        );


        setNewProjectName(
            ""
        );


        setNewProjectDescription(
            ""
        );


        setOriginFolders(
            []
        );


        setOriginRobots(
            []
        );


        setOriginRobotsError(
            ""
        );
    };


    // ========================================================
    // ABRIR FORMULÁRIO
    // ========================================================

    const openCreateForm = () => {

        if (!canCreateDevelopment) {
            return;
        }


        // Toda nova abertura começa em estado limpo.
        resetCreateForm();


        setShowCreateForm(
            true
        );
    };


    // ========================================================
    // FECHAR / CANCELAR FORMULÁRIO
    // ========================================================

    const closeCreateForm = () => {

        // Evita desmontar o formulário enquanto o POST
        // de criação estiver em andamento.
        if (creatingProject) {
            return;
        }


        setShowCreateForm(
            false
        );


        resetCreateForm();
    };


    // ========================================================
    // CARREGAR ESTRUTURA DE ROBÔS DE PRODUÇÃO
    // ========================================================
    //
    // O effect depende exclusivamente da abertura do formulário.
    //
    // O boolean "active" mantém a proteção já existente:
    // se o formulário for fechado antes do GET terminar,
    // aquela resposta não altera mais os estados.
    // ========================================================

    useEffect(() => {

        if (!showCreateForm) {
            return;
        }


        let active =
            true;


        // Mantém a abertura sempre no modo Novo Robô.
        setProjectOriginMode(
            "new"
        );


        setBaseRobotId(
            ""
        );


        setSelectedOriginFolderId(
            null
        );


        setOriginFolders(
            []
        );


        setOriginRobots(
            []
        );


        setOriginRobotsError(
            ""
        );


        api
            .get(
                "/development/release/robots"
            )
            .then((response) => {

                if (!active) {
                    return;
                }


                setOriginFolders(
                    response.data?.folders || []
                );


                setOriginRobots(
                    response.data?.robots || []
                );
            })
            .catch((err: any) => {

                if (!active) {
                    return;
                }


                setOriginRobotsError(
                    getApiErrorMessage(
                        err,
                        "Não foi possível carregar a estrutura de Robôs de Produção."
                    )
                );
            });


        // Cleanup lógico:
        // respostas posteriores serão ignoradas.
        return () => {

            active =
                false;
        };

    }, [showCreateForm]);


    // ========================================================
    // CRIAR AUTOMATION PROJECT
    // ========================================================

    const createProject = async () => {

        if (!canCreateDevelopment) {
            return;
        }


        const name =
            newProjectName.trim();


        // Mantém exatamente as validações atuais:
        //
        // - título obrigatório;
        // - bloqueia duplo POST;
        // - Robot obrigatório quando origem = existing.
        if (
            !name ||
            creatingProject ||
            (
                projectOriginMode === "existing" &&
                !baseRobotId
            )
        ) {
            return;
        }


        try {

            setCreatingProject(
                true
            );


            onError(
                ""
            );


            const response =
                await api.post(
                    "/development/projects",
                    {
                        // Título da demanda.
                        name,


                        // Descrição continua opcional.
                        description:
                            newProjectDescription
                                .trim() ||
                            null,


                        // Nesta arquitetura o projeto continua
                        // nascendo na raiz de Desenvolvimento.
                        folder_id:
                            null,


                        // Novo Robô:
                        //     null
                        //
                        // Robô existente:
                        //     ID do Robot de Produção selecionado.
                        base_robot_id:
                            projectOriginMode ===
                            "existing"
                                ? Number(
                                    baseRobotId
                                )
                                : null,
                    }
                );


            const project:
                DevelopmentProject | undefined =
                    response.data?.project;


            if (!project) {

                throw new Error(
                    "O backend não retornou o projeto criado."
                );
            }


            // Development.tsx continua dono da lista oficial.
            onProjectCreated(
                project
            );


            // Mantém o comportamento atual:
            // só recarrega o board se o usuário estiver
            // visualizando o Kanban naquele momento.
            if (isKanbanView) {

                await onRefreshKanban();
            }


            // Somente limpa e fecha depois da confirmação
            // de sucesso do backend.
            resetCreateForm();


            setShowCreateForm(
                false
            );

        } catch (err: any) {

            console.error(
                "Erro ao criar projeto de Desenvolvimento:",
                err
            );


            onError(
                getApiErrorMessage(
                    err,
                    "Não foi possível criar o projeto."
                )
            );

        } finally {

            setCreatingProject(
                false
            );
        }
    };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        showCreateForm,

        projectOriginMode,
        baseRobotId,

        originFolders,
        originRobots,
        selectedOriginFolderId,
        originRobotsError,

        newProjectName,
        newProjectDescription,

        creatingProject,

        setProjectOriginMode,
        setBaseRobotId,
        setSelectedOriginFolderId,
        setNewProjectName,
        setNewProjectDescription,

        openCreateForm,
        closeCreateForm,
        createProject,
    };
}


export default useDevelopmentProjectCreation;
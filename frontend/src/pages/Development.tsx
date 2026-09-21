
    // ============================================================
    // MÓDULOS - DEVELOPMENT
    // ============================================================
    //
    // Os contratos de dados, utilitários de data/hora e tratamento
    // de erros foram extraídos desta página para módulos próprios.
    //
    // Development.tsx continua responsável pela orquestração da
    // página, mas deixa de concentrar responsabilidades que podem
    // ser reutilizadas por componentes e hooks.
    // ============================================================


    // Tipos compartilhados pela área de Desenvolvimento.
    import type {
    DevelopmentProject,
    DevelopmentViewMode,
    ProjectMenuState,
    } from "../types/development";



    // Hook responsável exclusivamente pelos dados derivados
    // da pesquisa da área de Desenvolvimento.
    //
    // A página continua sendo dona dos arrays originais;
    // o hook devolve somente as versões filtradas.
    import useDevelopmentFilters
        from "../hooks/development/useDevelopmentFilters";


    // ============================================================
    // EXECUÇÃO DE PROJETOS DE DESENVOLVIMENTO
    // ============================================================
    //
    // Centraliza:
    //     - seleção do projeto;
    //     - carregamento dos Agents;
    //     - seleção do Agent;
    //     - envio da execução;
    //     - estados e feedback do modal.
    //
    // Development.tsx apenas conecta esse fluxo aos componentes.
    import useDevelopmentExecution
        from "../hooks/development/useDevelopmentExecution";


    // ============================================================
    // LIXEIRA DE PROJETOS DE DESENVOLVIMENTO
    // ============================================================
    //
    // Centraliza:
    //     - carregamento da Lixeira;
    //     - restauração;
    //     - exclusão permanente;
    //     - estados operacionais dessas ações.
    //
    // A navegação visual para entrar/sair da Lixeira continua
    // sendo responsabilidade do Development.tsx.
    import useDevelopmentTrash
        from "../hooks/development/useDevelopmentTrash";

    // ============================================================
    // DETALHES DOS CARDS DO KANBAN
    // ============================================================
    //
    // Centraliza:
    //     - responsáveis;
    //     - datas;
    //     - esforço estimado;
    //     - comentários;
    //     - carregamento e persistência do painel.
    //
    // CardDetailsPanel permanece exclusivamente visual.
    // Development.tsx fornece apenas a permissão e a atualização
    // do Kanban necessária depois de uma alteração.
    import useDevelopmentCardDetails
        from "../hooks/development/useDevelopmentCardDetails";


    // ============================================================
    // RELEASE / PUBLICAÇÃO
    // ============================================================
    //
    // Centraliza:
    //     - preview do Release;
    //     - destino do Robot;
    //     - versões das Libraries;
    //     - novas Libraries;
    //     - confirmação;
    //     - publicação;
    //     - estados operacionais do modal.
    //
    // Development.tsx permanece responsável apenas por conectar
    // o fluxo de Release ao Kanban, à lista de projetos e ao
    // feedback geral da página.
    import useDevelopmentRelease
        from "../hooks/development/useDevelopmentRelease";


    // ============================================================
    // CRIAÇÃO DE AUTOMATION PROJECT
    // ============================================================
    //
    // Centraliza:
    //     - abertura e fechamento do formulário;
    //     - origem Novo Robô / Robô existente;
    //     - estrutura de Robôs de Produção;
    //     - dados da demanda;
    //     - criação do AutomationProject;
    //     - limpeza do formulário.
    //
    // Development.tsx continua sendo dono da lista oficial
    // de projetos e do Workflow.
    import useDevelopmentProjectCreation
        from "../hooks/development/useDevelopmentProjectCreation";


    // ============================================================
    // WORKFLOW / KANBAN
    // ============================================================
    //
    // Centraliza:
    //     - carregamento do board;
    //     - stages do Workflow;
    //     - movimentação entre stages;
    //     - drag-and-drop;
    //     - estados operacionais de movimentação.
    //
    // Development.tsx continua responsável pela navegação visual
    // entre Projetos, Kanban e Lixeira.
    import useDevelopmentKanban
        from "../hooks/development/useDevelopmentKanban";


    // ============================================================
    // AÇÕES DOS PROJETOS ATIVOS
    // ============================================================
    //
    // Centraliza operações de domínio executadas sobre projetos
    // ativos, começando pelo soft delete.
    //
    // Development.tsx continua responsável pela coleção oficial
    // de projetos e pelo estado visual do menu de opções.
    import useDevelopmentProjectActions
        from "../hooks/development/useDevelopmentProjectActions";

    // ============================================================
    // DADOS E INICIALIZAÇÃO DE DEVELOPMENT
    // ============================================================
    //
    // Centraliza:
    //     - permissões efetivas;
    //     - carregamento inicial;
    //     - projetos ativos;
    //     - loading;
    //     - erro global de carregamento;
    //     - atualização da coleção de projetos.
    //
    // Development.tsx passa a consumir esses dados e permanece
    // responsável pela composição/orquestração da interface.
    import useDevelopmentData
        from "../hooks/development/useDevelopmentData";
    // Painel lateral responsável pela visualização e edição dos
    // detalhes de planejamento e comentários do card do Kanban.
    //
    // O componente permanece exclusivamente visual.
    //
    // Estados, carregamento e persistência dos detalhes pertencem
    // ao hook useDevelopmentCardDetails. Development.tsx apenas
    // conecta o painel ao restante da página.
    import CardDetailsPanel
        from "../components/development/kanban/CardDetailsPanel";



    // Quadro completo do Workflow / Kanban.
    //
    // A renderização das colunas e dos estados visuais do quadro
    // agora pertence a KanbanBoard.tsx.
    //
    // Carregamento, movimentação e drag-and-drop pertencem
    // ao hook useDevelopmentKanban.
    //
    // Development.tsx apenas conecta o board aos demais
    // domínios da página, como Release e Card Details.
    import KanbanBoard
        from "../components/development/kanban/KanbanBoard";

    // Modal responsável exclusivamente pela interface de execução
    // de um AutomationProject em um Agent.
    //
    // Carregamento dos Agents, seleção e execução pertencem
    // ao hook useDevelopmentExecution.
    //
    // Development.tsx apenas conecta o modal às permissões
    // e aos demais elementos da página.
    import ExecutionModal
        from "../components/development/modals/ExecutionModal";

    // Modal responsável pela interface completa de Release.
    //
    // Preview, configuração e publicação do Release pertencem
    // ao hook useDevelopmentRelease.
    //
    // Development.tsx conecta o resultado à lista de projetos,
    // ao Kanban e ao feedback geral da página.
    import PublishModal
        from "../components/development/modals/PublishModal";

    // Formulário responsável pela interface de criação de projetos.
    //
    // Origem, estrutura de Produção e criação efetiva do
    // AutomationProject pertencem ao hook
    // useDevelopmentProjectCreation.
    //
    // Development.tsx apenas conecta o formulário à coleção
    // oficial de projetos e ao Workflow.
    import CreateProjectForm
        from "../components/development/projects/CreateProjectForm";

    // Grade responsável pela visualização dos projetos ativos.
    //
    // O componente permanece visual.
    //
    // Development.tsx conecta a grade à navegação do Studio,
    // ao menu visual e aos hooks responsáveis pelas operações
    // dos AutomationProjects.
    import ProjectGrid
        from "../components/development/projects/ProjectGrid";

    // Cabeçalho, navegação, feedback e pesquisa da área
    // principal de projetos de Desenvolvimento.
    //
    // Estados e ações continuam sendo controlados pela página.
    import DevelopmentProjectToolbar
        from "../components/development/projects/DevelopmentProjectToolbar";

    // Menu flutuante responsável pelas ações disponíveis
    // sobre um projeto da lista de Desenvolvimento.
    // O posicionamento e a abertura do menu permanecem como
    // estado visual do Development.tsx.
    //
    // A operação de soft delete pertence ao hook
    // useDevelopmentProjectActions.
    import ProjectOptionsMenu
        from "../components/development/projects/ProjectOptionsMenu";

    // Grade responsável exclusivamente pela visualização
    // dos AutomationProjects presentes na Lixeira.
    //
    // O componente permanece exclusivamente visual.
    //
    // Carregamento, restauração e exclusão permanente pertencem
    // ao hook useDevelopmentTrash.
    //
    // Development.tsx controla somente a navegação para a Lixeira
    // e sua integração com a coleção principal.
    import TrashProjectGrid
        from "../components/development/trash/TrashProjectGrid";


    import {
        Code2,
    } from "lucide-react";

    import {
        useState,

        type MouseEvent,
    } from "react";

    import {
        useNavigate,
    } from "react-router-dom";


    // ============================================================
    // PÁGINA - DESENVOLVIMENTO
    // ============================================================

    function Development() {

        const navigate = useNavigate();


        // ========================================================
        // ESTADOS
        // ========================================================


        // Texto usado para filtrar projetos.
        const [search, setSearch] =
            useState("");


        // Mensagem geral de sucesso da área de Desenvolvimento.
        //
        // Diferente de executionError, este estado não pertence
        // exclusivamente ao fluxo de execução.
        //
        // Pode ser utilizado por operações concluídas pela página,
        // como a publicação de um Release.
        const [successMessage, setSuccessMessage] =
            useState("");


        // ========================================================
        // DADOS / INICIALIZAÇÃO
        // ========================================================
        //
        // A fonte oficial dos projetos ativos, permissões,
        // carregamento e erro estrutural da área passa a ser:
        //
        // hooks/development/useDevelopmentData.ts
        //
        // Os demais hooks recebem esses dados por composição,
        // sem conhecer como /auth/me ou /development/projects
        // são carregados.
        // ========================================================

        const {
            projects,
            setProjects,

            loading,

            error,
            setError,

            permissions,
            permissionsLoaded,

            loadProjects,
        } = useDevelopmentData();
        // Permissões utilizadas nesta página.
        const canViewDevelopment =
            permissions.includes("Development:view");

        const canCreateDevelopment =
            permissions.includes("Development:create");

        const canDeleteDevelopment =
            permissions.includes("Development:delete");

        const canViewTrash =
            permissions.includes("Development:trash_view");

        const canRestoreDevelopment =
            permissions.includes("Development:restore");

        const canPermanentDeleteDevelopment =
            permissions.includes("Development:permanent_delete");

        const canMoveDevelopmentStage =
            permissions.includes("Development:move_stage");

        

        const canPublishDevelopment =
        permissions.includes("Development:publish");


        // Permissão utilizada pelos metadados do Kanban:
        //
        // - responsáveis;
        // - datas;
        // - esforço;
        // - comentários.
        const canEditDevelopment =
            permissions.includes("Development:edit");


        // Para executar também continua sendo necessária
        // a permissão específica de execução.
        const canExecuteDevelopment =
            canEditDevelopment &&
            permissions.includes("Executions:execute");


        // Controla qual menu de três pontos está atualmente aberto.
        //
        // null:
        //     nenhum menu aberto.
        const [projectMenu, setProjectMenu] =
            useState<ProjectMenuState | null>(
                null
            );




        // EXECUÇÃO DE DESENVOLVIMENTO
        // ========================================================
        //
        // Todo o estado e a orquestração específica de execução
        // pertencem agora a:
        //
        // hooks/development/useDevelopmentExecution.ts
        //
        // A página mantém somente a conexão entre:
        //     - permissões;
        //     - ProjectGrid;
        //     - ExecutionModal;
        //     - feedback do toolbar.
        // ========================================================

        const {
            projectToExecute,
            executionAgents,
            selectedExecutionAgentId,
            loadingExecutionAgents,
            executingProjectId,
            executionError,
            executionMessage,

            openExecutionModal,
            closeExecutionModal,
            changeExecutionAgent,
            executeDevelopmentProject,
        } = useDevelopmentExecution({
            canExecuteDevelopment,
        });


        // ========================================================
        // ESTADOS - VISUALIZAÇÃO / KANBAN
        // ========================================================

        const [viewMode, setViewMode] =
            useState<DevelopmentViewMode>(
                "projects"
            );


        // ========================================================
        // ESTADOS - LIXEIRA
        // ========================================================

        // false:
        //     mostra os projetos ativos.
        //
        // true:
        //     mostra os projetos que estão na Lixeira.
        const [showTrash, setShowTrash] =
            useState(false);


        // ========================================================
        // OPERAÇÕES DA LIXEIRA
        // ========================================================
        //
        // Persistência e estados operacionais da Lixeira agora
        // pertencem a useDevelopmentTrash.
        //
        // Development.tsx continua dono de:
        //     - showTrash;
        //     - navegação entre as visualizações;
        //     - search;
        //     - lista oficial de projetos ativos.
        // ========================================================

        const {
            trashProjects,
            loadingTrash,
            restoringProjectId,
            permanentlyDeletingProjectId,

            loadTrash,
            restoreProject,
            permanentlyDeleteProject,
        } = useDevelopmentTrash({

            canViewTrash,
            canRestoreDevelopment,
            canPermanentDeleteDevelopment,


            // Quando um projeto é restaurado, o hook devolve
            // o objeto confirmado pelo backend.
            //
            // A lista principal continua pertencendo à página.
            onProjectRestored: (restoredProject) => {

                setProjects((current) => [
                    restoredProject,

                    ...current.filter(
                        (item) =>
                            item.id !== restoredProject.id
                    ),
                ]);
            },


            // Os erros da Lixeira continuam aparecendo no mesmo
            // feedback global utilizado atualmente pela página.
            onError: (message) => {

                setError(
                    message
                );
            },
        });
        
        





        // ========================================================
        // AÇÕES DOS PROJETOS ATIVOS
        // ========================================================
        //
        // Operações de domínio sobre AutomationProjects ativos
        // pertencem agora a:
        //
        // hooks/development/useDevelopmentProjectActions.ts
        //
        // Development.tsx continua responsável por:
        //     - coleção oficial `projects`;
        //     - feedback global;
        //     - estado visual do menu de opções.
        // ========================================================

        const {
            deletingProjectId,
            deleteProject,
        } = useDevelopmentProjectActions({

            canDeleteDevelopment,


            // O hook informa somente que o backend confirmou
            // o soft delete.
            //
            // A coleção oficial continua pertencendo à página.
            onProjectDeleted: (deletedProject) => {

                setProjects((current) =>
                    current.filter(
                        (item) =>
                            item.id !== deletedProject.id
                    )
                );
            },


            // O menu é responsabilidade visual do container.
            //
            // Assim que a exclusão for confirmada pelo usuário,
            // fechamos o ProjectOptionsMenu.
            onBeforeDelete: () => {

                setProjectMenu(
                    null
                );
            },


            // Mantemos o mesmo feedback global já utilizado
            // pelas demais operações da página.
            onError: (message) => {

                setError(
                    message
                );
            },
        });
 

        // ========================================================
        // WORKFLOW / KANBAN
        // ========================================================
        //
        // O estado operacional e as ações específicas do Workflow
        // pertencem agora a:
        //
        // hooks/development/useDevelopmentKanban.ts
        //
        // Development.tsx continua responsável por:
        //     - navegação entre as visualizações;
        //     - lista oficial de AutomationProjects;
        //     - pesquisa;
        //     - conexão do Kanban com Release e Card Details.
        // ========================================================

        const {
            kanbanStages,
            loadingKanban,
            movingProjectId,

            draggedProjectId,
            draggedSourceStageCode,
            dragOverStageId,

            setDragOverStageId,

            loadKanban,

            handleKanbanDragStart,
            handleKanbanDragEnd,
            handleKanbanDrop,
        } = useDevelopmentKanban({

            canViewDevelopment,
            canMoveDevelopmentStage,


            // A lista oficial da visualização de Projetos continua
            // pertencendo ao Development.tsx.
            //
            // Quando o PATCH devolver o projeto atualizado,
            // substituímos somente aquele AutomationProject.
            onProjectMoved: (movedProject) => {

                setProjects((current) =>
                    current.map(
                        (item) =>
                            item.id === movedProject.id
                                ? movedProject
                                : item
                    )
                );
            },


            // O feedback HTTP continua centralizado na página.
            onError: (message) => {

                setError(
                    message
                );
            },
        });


        // ========================================================
        // CRIAÇÃO DE AUTOMATION PROJECT
        // ========================================================
        //
        // Todo o estado e a orquestração específicos da criação
        // pertencem agora a:
        //
        // hooks/development/useDevelopmentProjectCreation.ts
        //
        // Development.tsx continua responsável por:
        //     - lista oficial de projetos ativos;
        //     - Workflow / Kanban;
        //     - feedback global da página.
        // ========================================================

        const {
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
        } = useDevelopmentProjectCreation({

            canCreateDevelopment,


            // O hook recebe apenas a informação necessária para
            // decidir se o Workflow precisa ser atualizado.
            isKanbanView:
                viewMode === "kanban",


            // Development.tsx continua dono da coleção oficial
            // de AutomationProjects ativos.
            onProjectCreated: (project) => {

                setProjects((current) => [
                    project,

                    ...current.filter(
                        (item) =>
                            item.id !== project.id
                    ),
                ]);
            },


            // Depois da criação, o hook de criação solicita
            // atualização ao domínio responsável pelo Workflow.
            onRefreshKanban:
                loadKanban,


            // Feedback geral continua pertencendo à página.
            onError: (message) => {

                setError(
                    message
                );
            },
        });

        // ========================================================
        // DETALHES DOS CARDS DO KANBAN
        // ========================================================
        //
        // Estados, carregamento e persistência do painel foram
        // isolados em useDevelopmentCardDetails.
        //
        // A página fornece somente:
        //     - a permissão efetiva de edição;
        //     - a atualização oficial do Kanban.
        //
        // Isso mantém o hook independente da implementação interna
        // do board e evita duplicação da lógica de atualização.
        // ========================================================

        const {
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
        } = useDevelopmentCardDetails({
            canEditDevelopment,

            // Alterações de planejamento podem refletir nos cards,
            // então solicitamos nova leitura do board.
            onRefreshKanban:
                loadKanban,
        });




        // ========================================================
        // RELEASE / PUBLICAÇÃO
        // ========================================================
        //
        // Todo o estado e a orquestração específica do Release
        // pertencem agora a:
        //
        // hooks/development/useDevelopmentRelease.ts
        //
        // Development.tsx permanece responsável por:
        //     - lista oficial de projetos ativos;
        //     - atualização oficial do Kanban;
        //     - feedback geral da página.
        //
        // O PublishModal recebe apenas os dados e callbacks
        // devolvidos pelo hook.
        // ========================================================

        const {
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
        } = useDevelopmentRelease({

            canPublishDevelopment,


            // A lista oficial de AutomationProjects continua
            // pertencendo ao Development.tsx.
            //
            // Depois do Release, removemos apenas o projeto
            // confirmado pelo backend como publicado.
            onProjectPublished: (publishedProject) => {

                setProjects((current) =>
                    current.filter(
                        (item) =>
                            item.id !==
                            publishedProject.id
                    )
                );
            },

            // Depois da publicação, o domínio de Release solicita
            // atualização ao hook responsável pelo Workflow.
            onRefreshKanban:
                loadKanban,


            // Feedback positivo geral continua pertencendo
            // à página e aparece no toolbar.
            onSuccess: (message) => {

                setSuccessMessage(
                    message
                );
            },


            // O erro global também permanece sendo estado
            // da página.
            onGlobalError: (message) => {

                setError(
                    message
                );
            },
        });


        // ========================================================
        // FILTROS DERIVADOS DA PESQUISA
        // ========================================================
        //
        // Toda a lógica de filtragem foi isolada no hook:
        //
        // hooks/development/useDevelopmentFilters.ts
        //
        // Development.tsx continua sendo responsável pelos
        // estados originais:
        //     - search;
        //     - projects;
        //     - kanbanStages;
        //     - trashProjects.
        //
        // O hook devolve somente dados derivados.
        // ========================================================

        const {
            filteredProjects,
            filteredKanbanStages,
            filteredKanbanProjectCount,
            filteredTrashProjects,
        } = useDevelopmentFilters({
            search,
            projects,
            kanbanStages,
            trashProjects,
        });


        // ========================================================
        // ABRIR PROJETO NO DUET STUDIO
        // ========================================================

        const openProject = (
            project: DevelopmentProject
        ) => {

            if (!canViewDevelopment) {
                return;
            }

            navigate(
                `/development/${project.id}/studio`,
                {
                    state: {
                        projectName: project.name,
                    },
                }
            );
        };


        // ========================================================
        // MENU DE OPÇÕES DO PROJETO
        // ========================================================
        //
        // Controla somente a abertura, fechamento e posição
        // do menu pertencente ao projeto.
        //
        // A renderização visual agora pertence ao componente
        // ProjectOptionsMenu.tsx.
        // ========================================================

        const toggleProjectMenu = (
            event: MouseEvent<HTMLButtonElement>,
            projectId: number
        ) => {

            // Evita que o clique nos três pontos seja propagado
            // para outros elementos do card.
            event.stopPropagation();


            // Usuários sem permissão de exclusão não podem
            // abrir o menu de opções.
            if (!canDeleteDevelopment) {
                return;
            }


            // Se o menu do mesmo projeto já estiver aberto,
            // clicar novamente fecha o menu.
            if (
                projectMenu?.projectId ===
                projectId
            ) {

                setProjectMenu(
                    null
                );

                return;
            }


            // Posição real do botão de três pontos na viewport.
            const rect =
                event
                    .currentTarget
                    .getBoundingClientRect();


            // Deve continuar igual à largura utilizada dentro
            // de ProjectOptionsMenu.tsx.
            const menuWidth =
                190;


            // Evita que o menu ultrapasse a lateral direita
            // da janela.
            const left =
                Math.max(
                    12,
                    Math.min(
                        window.innerWidth -
                            menuWidth -
                            12,

                        rect.right -
                            menuWidth
                    )
                );


            // Guarda o projeto e a posição visual do menu.
            setProjectMenu({
                projectId,

                top:
                    rect.bottom + 6,

                left,
            });
        };

        
        // ========================================================
        // ABRIR LIXEIRA
        // ========================================================

        const abrirLixeira = async () => {

            if (!canViewTrash) {
                return;
            }

            // Fecha elementos da visualização principal.
            setProjectMenu(
                null
            );

            // Fecha e limpa qualquer criação que estivesse aberta
            // antes de entrar na Lixeira.
            closeCreateForm();

            // A pesquisa é zerada porque agora estamos entrando
            // em outro conjunto de projetos.
            setSearch("");

            setViewMode(
                "projects"
            );

            setShowTrash(
                true
            );


            // A navegação continua na página.
            //
            // O carregamento dos dados da Lixeira agora é delegado
            // ao hook responsável por esse domínio.
            await loadTrash();
        };


        // ========================================================
        // VOLTAR PARA PROJETOS ATIVOS
        // ========================================================

        const voltarProjetos = async () => {

            setSearch("");

            setError("");

            setViewMode(
                "projects"
            );

            setShowTrash(
                false
            );


            // Atualiza novamente a coleção oficial de projetos ativos.
            //
            // O acesso ao backend pertence agora ao hook
            // useDevelopmentData.
            await loadProjects();
        };


        // ========================================================
        // ALTERNAR VISUALIZAÇÃO
        // ========================================================

        const mostrarListaProjetos = () => {

            setProjectMenu(
                null
            );

            setError("");
            setSearch("");
            setShowTrash(false);

            setViewMode(
                "projects"
            );
        };


        const mostrarKanban = async () => {

            if (!canViewDevelopment) {
                return;
            }

            setProjectMenu(
                null
            );

            setError("");
            setSearch("");
            // O Kanban não mantém formulário de criação aberto.
            closeCreateForm();
            setShowTrash(false);

            setViewMode(
                "kanban"
            );

            // A navegação continua pertencendo à página.
            // O carregamento dos dados pertence ao hook do Workflow.
            await loadKanban();
        };


        


    // ========================================================
    // STATUS VISUAL
    // ========================================================
    //
    // Converte o estado técnico do AutomationProject em uma
    // descrição amigável utilizada nos cards da interface.
    //
    // Esta função continua dentro de Development.tsx por enquanto
    // porque ainda está diretamente ligada à apresentação da página.
    // ========================================================

        // ========================================================
        // INTERFACE
        // ========================================================

        return (
            <div className="page-container development-page">

                {/* =================================================
                    CABEÇALHO
                ================================================= */}

                <div className="page-heading">
                    <div>
                        <div className="page-eyebrow">
                            AUTOMATION DEVELOPMENT
                        </div>

                        <h1>
                            Desenvolvimento
                        </h1>

                        <p>
                            Crie, edite e teste automações antes de publicá-las
                            para execução em produção.
                        </p>
                    </div>

                    <div className="page-heading-icon">
                        <Code2
                            size={24}
                            strokeWidth={1.7}
                        />
                    </div>
                </div>


                {/* =================================================
                    BARRA DE AÇÕES
                ================================================= */}

                {permissionsLoaded && !canViewDevelopment && (
                    <div className="alert alert-error">
                        Você não possui a permissão Development:view.
                    </div>
                )}

                {(!permissionsLoaded || canViewDevelopment) && (
                <section className="content-panel">

                    

                    {/* =============================================
                            CABEÇALHO / NAVEGAÇÃO / PESQUISA
                        ============================================= */}

                        <DevelopmentProjectToolbar

                            // ========================================================
                            // VISUALIZAÇÃO
                            // ========================================================

                            viewMode={
                                viewMode
                            }

                            showTrash={
                                showTrash
                            }


                            // ========================================================
                            // PERMISSÕES
                            // ========================================================

                            canViewTrash={
                                canViewTrash
                            }

                            canCreateDevelopment={
                                canCreateDevelopment
                            }


                            // ========================================================
                            // FEEDBACK
                            // ========================================================

                            error={
                                error
                            }

                            // Prioriza o feedback específico da execução.
                            // Quando não houver execução recente, utiliza o feedback
                            // geral produzido por outras operações da página.
                            executionMessage={
                                executionMessage ||
                                successMessage
                            }


                            // ========================================================
                            // PESQUISA
                            // ========================================================

                            search={
                                search
                            }

                            onSearchChange={
                                setSearch
                            }


                            // ========================================================
                            // CONTADORES
                            // ========================================================

                            projectCount={
                                projects.length
                            }

                            trashProjectCount={
                                trashProjects.length
                            }

                            kanbanProjectCount={
                                filteredKanbanProjectCount
                            }


                            // ========================================================
                            // NAVEGAÇÃO
                            // ========================================================

                            onShowProjects={
                                mostrarListaProjetos
                            }

                            onShowKanban={
                                mostrarKanban
                            }

                            onOpenTrash={
                                abrirLixeira
                            }

                            onBackFromTrash={
                                voltarProjetos
                            }


                            // ========================================================
                            // NOVO PROJETO
                            // ========================================================

                            // O hook passa a controlar a abertura e a
                            // inicialização limpa do formulário.
                            onCreateProject={
                                openCreateForm
                            }
                        />
                    {/* =============================================
                        FORMULÁRIO - NOVO PROJETO
                    ============================================= */}

                    {!showTrash &&
                        canCreateDevelopment &&
                        showCreateForm && (

                        <CreateProjectForm

                            // ====================================================
                            // ORIGEM DO PROJETO
                            // ====================================================

                            originMode={
                                projectOriginMode
                            }

                            baseRobotId={
                                baseRobotId
                            }

                            folders={
                                originFolders
                            }

                            robots={
                                originRobots
                            }

                            selectedFolderId={
                                selectedOriginFolderId
                            }

                            robotsError={
                                originRobotsError
                            }


                            // ====================================================
                            // DADOS DA DEMANDA
                            // ====================================================

                            projectName={
                                newProjectName
                            }

                            projectDescription={
                                newProjectDescription
                            }


                            // ====================================================
                            // ESTADO OPERACIONAL
                            // ====================================================

                            creating={
                                creatingProject
                            }


                            // ====================================================
                            // ALTERAÇÃO DA ORIGEM
                            // ====================================================

                            onOriginModeChange={
                                setProjectOriginMode
                            }

                            onBaseRobotChange={
                                setBaseRobotId
                            }

                            onSelectedFolderChange={
                                setSelectedOriginFolderId
                            }


                            // ====================================================
                            // DADOS DA DEMANDA
                            // ====================================================

                            onProjectNameChange={
                                setNewProjectName
                            }

                            onProjectDescriptionChange={
                                setNewProjectDescription
                            }


                            // ====================================================
                            // CANCELAR
                            // ====================================================
                            // ====================================================

                            // Fecha e limpa integralmente o estado de criação.
                            onCancel={
                                closeCreateForm
                            }


                            // ====================================================
                            // CRIAR
                            // ====================================================
                            //
                            // A criação e a persistência pertencem ao hook
                            // useDevelopmentProjectCreation.
                            // ====================================================

                            onCreate={
                                createProject
                            }
                        />
                    )}


                    {/* =============================================
                        LIXEIRA
                    ============================================= */}

                    {showTrash && (

                        <TrashProjectGrid

                            // ====================================================
                            // PROJETOS
                            // ====================================================
                            //
                            // A filtragem pela pesquisa continua sendo feita
                            // pelo Development.tsx.
                            // ====================================================

                            projects={
                                filteredTrashProjects
                            }


                            // Quantidade sem o filtro da pesquisa.
                            //
                            // O componente usa esse valor para diferenciar:
                            //
                            // - Lixeira realmente vazia;
                            // - pesquisa sem resultados.
                            totalProjectCount={
                                trashProjects.length
                            }


                            // ====================================================
                            // ESTADO DE CARREGAMENTO
                            // ====================================================

                            loading={
                                loadingTrash
                            }


                            // ====================================================
                            // PERMISSÕES
                            // ====================================================

                            canRestore={
                                canRestoreDevelopment
                            }

                            canPermanentDelete={
                                canPermanentDeleteDevelopment
                            }


                            // ====================================================
                            // OPERAÇÕES EM ANDAMENTO
                            // ====================================================

                            restoringProjectId={
                                restoringProjectId
                            }

                            permanentlyDeletingProjectId={
                                permanentlyDeletingProjectId
                            }


                            // ====================================================
                            // AÇÕES
                            // ====================================================
                            //
                            // As funções continuam no Development.tsx porque elas
                            // executam chamadas HTTP e alteram o estado global.
                            // ====================================================

                            onRestore={
                                restoreProject
                            }

                            onPermanentDelete={
                                permanentlyDeleteProject
                            }
                        />
                    )}
                    
                    {/* =============================================
                            PROJETOS ATIVOS
                        ============================================= */}

                        {!showTrash &&
                            viewMode === "projects" && (

                            <ProjectGrid

                                // ====================================================
                                // PROJETOS
                                // ====================================================
                                //
                                // A pesquisa continua sendo aplicada pelo
                                // Development.tsx.
                                // ====================================================

                                projects={
                                    filteredProjects
                                }


                                // Quantidade real antes do filtro.
                                //
                                // Permite ao componente diferenciar:
                                //
                                // - nenhum projeto criado;
                                // - pesquisa sem resultado.
                                totalProjectCount={
                                    projects.length
                                }


                                // ====================================================
                                // CARREGAMENTO
                                // ====================================================

                                loading={
                                    loading
                                }


                                // ====================================================
                                // PERMISSÕES
                                // ====================================================

                                canDelete={
                                    canDeleteDevelopment
                                }

                                canExecute={
                                    canExecuteDevelopment
                                }


                                // ====================================================
                                // MENU DE OPÇÕES
                                // ====================================================

                                openMenuProjectId={
                                    projectMenu?.projectId ??
                                    null
                                }


                                // ====================================================
                                // EXECUÇÃO
                                // ====================================================

                                executingProjectId={
                                    executingProjectId
                                }


                                // ====================================================
                                // MENU
                                // ====================================================
                                //
                                // O cálculo de posição e o Portal continuam sendo
                                // responsabilidade do Development.tsx.
                                // ====================================================

                                onToggleMenu={
                                    toggleProjectMenu
                                }


                                // ====================================================
                                // STUDIO
                                // ====================================================

                                onOpenStudio={
                                    openProject
                                }


                                // ====================================================
                                // EXECUÇÃO
                                // ====================================================

                                onExecute={
                                    openExecutionModal
                                }
                            />
                        )}
                

                    {/* =============================================
                        KANBAN / WORKFLOW
                    ============================================= */}

                    {!showTrash &&
                        viewMode === "kanban" && (

                        <KanbanBoard

                            // ====================================================
                            // DADOS DO WORKFLOW
                            // ====================================================

                            stages={
                                kanbanStages
                            }

                            filteredStages={
                                filteredKanbanStages
                            }

                            search={
                                search
                            }


                            // ====================================================
                            // CARREGAMENTO
                            // ====================================================

                            loading={
                                loadingKanban
                            }


                            // ====================================================
                            // DRAG-AND-DROP
                            // ====================================================

                            dragOverStageId={
                                dragOverStageId
                            }

                            draggedSourceStageCode={
                                draggedSourceStageCode
                            }

                            movingProjectId={
                                movingProjectId
                            }

                            draggedProjectId={
                                draggedProjectId
                            }


                            // ====================================================
                            // PERMISSÕES
                            // ====================================================

                            canMoveDevelopmentStage={
                                canMoveDevelopmentStage
                            }

                            canPublishDevelopment={
                                canPublishDevelopment
                            }


                            // ====================================================
                            // RELEASE
                            // ====================================================

                            publishingProjectId={
                                publishingProjectId
                            }


                            // ====================================================
                            // EVENTOS DAS COLUNAS
                            // ====================================================

                            onDragOverStage={
                                setDragOverStageId
                            }

                            onDrop={
                                handleKanbanDrop
                            }


                            // ====================================================
                            // EVENTOS DOS CARDS
                            // ====================================================

                            onCardDragStart={
                                handleKanbanDragStart
                            }

                            onCardDragEnd={
                                handleKanbanDragEnd
                            }


                            // ====================================================
                            // AÇÕES DOS CARDS
                            // ====================================================

                            onOpenDetails={
                                openCardDetails
                            }

                            onOpenStudio={
                                openProject
                            }

                            onPublish={
                                openPublishConfirmation
                            }
                        />
                    )}

                </section>
                )}
                

                {/* =========================================================
                    MENU DE OPÇÕES DO PROJETO
                ========================================================= */}

                <ProjectOptionsMenu

                    // Estado atual do menu:
                    // projectId + posição top/left.
                    menu={
                        projectMenu
                    }


                    // Permissão efetiva para exclusão.
                    canDelete={
                        canDeleteDevelopment
                    }


                    // Projeto que está sendo excluído neste momento.
                    deletingProjectId={
                        deletingProjectId
                    }


                    // Fecha o menu.
                    onClose={() => {

                        setProjectMenu(
                            null
                        );
                    }}


                    // O componente visual devolve somente o ID.
                    //
                    // Development.tsx continua responsável por localizar
                    // o projeto completo e executar deleteProject().
                    onDelete={(projectId) => {

                        const project =
                            projects.find(
                                (item) =>
                                    item.id ===
                                    projectId
                            );


                        if (!project) {
                            return;
                        }


                        void deleteProject(
                            project
                        );
                    }}
                />


                {/* =========================================================
                    PAINEL LATERAL - DETALHES DO CARD
                ========================================================= */}

                {/* 
                        O conteúdo visual pertence ao CardDetailsPanel.

                        Estados, carregamento e persistência pertencem ao
                        useDevelopmentCardDetails. A página apenas conecta
                        o painel ao Kanban.
                */}
                <CardDetailsPanel

                    // Projeto atualmente selecionado.
                    project={
                        selectedCardProject
                    }

                    // Dados carregados para o painel.
                    users={
                        cardUsers
                    }

                    comments={
                        cardComments
                    }


                    // Planejamento.
                    functionalResponsibleId={
                        cardFunctionalResponsibleId
                    }

                    technicalResponsibleId={
                        cardTechnicalResponsibleId
                    }

                    startDate={
                        cardStartDate
                    }

                    dueDate={
                        cardDueDate
                    }

                    effortHours={
                        cardEffortHours
                    }


                    // Novo comentário.
                    newComment={
                        newCardComment
                    }


                    // Estados operacionais.
                    loading={
                        loadingCardDetails
                    }

                    saving={
                        savingCardDetails
                    }

                    addingComment={
                        addingCardComment
                    }

                    error={
                        cardDetailsError
                    }

                    canEdit={
                        canEditDevelopment
                    }


                    // Atualização dos campos.
                    onFunctionalResponsibleChange={
                        setCardFunctionalResponsibleId
                    }

                    onTechnicalResponsibleChange={
                        setCardTechnicalResponsibleId
                    }

                    onStartDateChange={
                        setCardStartDate
                    }

                    onDueDateChange={
                        setCardDueDate
                    }

                    onEffortHoursChange={
                        setCardEffortHours
                    }

                    onNewCommentChange={
                        setNewCardComment
                    }


                    // Ações executadas pelo Development.tsx.
                    onClose={
                        closeCardDetails
                    }

                    onSave={
                        saveCardDetails
                    }

                    onAddComment={
                        addCardComment
                    }
                />
                {/* =========================================================
                    MODAL - EXECUTAR PROJETO DE DESENVOLVIMENTO
                ========================================================= */}

                <ExecutionModal

                    // Projeto selecionado para execução.
                    // null mantém o modal fechado.
                    project={
                        projectToExecute
                    }


                    // A mesma permissão utilizada anteriormente pelo JSX
                    // embutido no Development.tsx.
                    canExecute={
                        canExecuteDevelopment
                    }


                    // Agents retornados pelo endpoint de execução.
                    agents={
                        executionAgents
                    }


                    // Agent atualmente selecionado.
                    selectedAgentId={
                        selectedExecutionAgentId
                    }


                    // Estados operacionais.
                    loadingAgents={
                        loadingExecutionAgents
                    }

                    executingProjectId={
                        executingProjectId
                    }


                    // Erro exibido exclusivamente dentro do modal.
                    error={
                        executionError
                    }


                    // ========================================================
                    // ALTERAÇÃO DO AGENT
                    // ========================================================

                    // Alteração do Agent e limpeza de eventual erro
                    // agora pertencem ao hook de execução.
                    onAgentChange={
                        changeExecutionAgent
                    }


                    // ========================================================
                    // AÇÕES
                    // ========================================================

                    onClose={
                        closeExecutionModal
                    }

                    onExecute={
                        executeDevelopmentProject
                    }
                />
                
                {/* =========================================================
                        MODAL - RELEASE / PUBLICAÇÃO
                    ========================================================= */}

                    <PublishModal

                        // Projeto atualmente preparado para publicação.
                        project={
                            projectToPublish
                        }


                        // Permissão efetiva do usuário autenticado.
                        canPublish={
                            canPublishDevelopment
                        }


                        // ========================================================
                        // PRÉVIA DO RELEASE
                        // ========================================================

                        preview={
                            releasePreview
                        }

                        loading={
                            loadingRelease
                        }

                        publishingProjectId={
                            publishingProjectId
                        }


                        // ========================================================
                        // DESTINO DO ROBOT
                        // ========================================================

                        releaseFolderId={
                            releaseFolderId
                        }

                        newReleaseFolder={
                            newReleaseFolder
                        }

                        releaseRobotName={
                            releaseRobotName
                        }


                        // ========================================================
                        // LIBRARIES
                        // ========================================================

                        releaseLibraryVersions={
                            releaseLibraryVersions
                        }

                        newReleaseLibraries={
                            newReleaseLibraries
                        }


                        // ========================================================
                        // CONFIRMAÇÃO / ERRO
                        // ========================================================

                        confirmation={
                            publishConfirmation
                        }

                        error={
                            publishError
                        }


                        // ========================================================
                        // DESTINO DO ROBOT
                        // ========================================================

                        onReleaseFolderChange={
                            setReleaseFolderId
                        }

                        onNewReleaseFolderChange={
                            setNewReleaseFolder
                        }

                        onReleaseRobotNameChange={
                            setReleaseRobotName
                        }


                        // ========================================================
                        // VERSÃO DE LIBRARY EXISTENTE
                        // ========================================================

                        // Alteração da versão de uma Library existente
                        // é controlada pelo domínio de Release.
                        onLibraryVersionChange={
                            changeLibraryVersion
                        }


                        // ========================================================
                        // NOVA LIBRARY - SELECIONAR / REMOVER
                        // ========================================================

                        // Seleciona ou remove um pacote próprio da lista
                        // de novas Libraries do Release.
                        onNewLibraryToggle={
                            toggleNewLibrary
                        }


                        // ========================================================
                        // NOVA LIBRARY - NOME
                        // ========================================================

                        // Atualiza o nome definitivo da nova Library.
                        onNewLibraryNameChange={
                            changeNewLibraryName
                        }


                        // ========================================================
                        // NOVA LIBRARY - VERSÃO
                        // ========================================================

                        // Atualiza a versão escolhida para a nova Library.
                        onNewLibraryVersionChange={
                            changeNewLibraryVersion
                        }


                        // ========================================================
                        // CONFIRMAÇÃO
                        // ========================================================

                        onConfirmationChange={
                            setPublishConfirmation
                        }


                        // ========================================================
                        // AÇÕES
                        // ========================================================

                        onClose={
                            closePublishConfirmation
                        }

                        onPublish={
                            publishProject
                        }
                    />

            </div>
        );
    }


    export default Development;

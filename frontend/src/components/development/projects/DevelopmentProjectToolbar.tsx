// ============================================================
// DEVELOPMENT PROJECT TOOLBAR
// ============================================================
//
// Responsabilidade:
//     Renderiza o cabeçalho e a barra de navegação da área
//     principal de Desenvolvimento do DUET CORE.
//
// Este componente apresenta:
//     - título contextual da visualização atual;
//     - descrição contextual;
//     - alternância entre Projetos e Kanban;
//     - acesso à Lixeira;
//     - botão de Nova pasta;
//     - botão de Novo projeto;
//     - campo de pesquisa;
//     - contador contextual de registros.
//
// Arquitetura:
//     Este componente é exclusivamente visual.
//
// Este arquivo NÃO deve:
//     - carregar projetos;
//     - carregar o Kanban;
//     - carregar a Lixeira;
//     - alterar rotas;
//     - criar projetos;
//     - chamar APIs;
//     - controlar permissões por conta própria.
//
// Development.tsx continua responsável por:
//     - permissões;
//     - estados;
//     - alternância real das visualizações;
//     - carregamento do Kanban;
//     - carregamento da Lixeira;
//     - abertura do formulário de criação;
//     - valor e filtragem da pesquisa.
//
// DevelopmentProjectToolbar.tsx apenas recebe esses dados
// e encaminha as ações através de callbacks.
// ============================================================

import {
    ArrowLeft,
    Columns3,
    Folder,
    LayoutGrid,
    Plus,
    Trash2,
} from "lucide-react";
import FeedbackBanner from "../../ui/FeedbackBanner";
import { Button } from "../../ui/Button";
import SearchField from "../../ui/SearchField";


import type {
    DevelopmentViewMode,
} from "../../../types/development";


// ============================================================
// PROPS
// ============================================================

interface DevelopmentProjectToolbarProps {

    // ========================================================
    // VISUALIZAÇÃO
    // ========================================================

    // Visualização principal atualmente selecionada.
    viewMode:
        DevelopmentViewMode;


    // true:
    //     usuário está visualizando a Lixeira.
    //
    // false:
    //     usuário está na área de projetos ativos.
    showTrash:
        boolean;

    creationOpen:
        boolean;


    // ========================================================
    // PERMISSÕES
    // ========================================================

    canViewTrash:
        boolean;


    canCreateDevelopment:
        boolean;


    // ========================================================
    // FEEDBACK DA PÁGINA
    // ========================================================

    // Erro global das operações de Desenvolvimento.
    error:
        string;


    // Confirmação apresentada depois que uma execução
    // é aceita ou colocada na fila pelo Control Room.
    executionMessage:
        string;

    // ========================================================
    // PESQUISA
    // ========================================================

    search:
        string;


    onSearchChange:
        (
            value: string
        ) => void;


    // ========================================================
    // CONTADORES
    // ========================================================

    // Quantidade total de projetos ativos.
    projectCount:
        number;


    // Quantidade total de projetos presentes na Lixeira.
    trashProjectCount:
        number;


    // Quantidade atualmente visível no Kanban após pesquisa.
    kanbanProjectCount:
        number;


    // ========================================================
    // NAVEGAÇÃO / AÇÕES
    // ========================================================

    onShowProjects:
        () => void;


    onShowKanban:
        () => void | Promise<void>;


    onOpenTrash:
        () => void | Promise<void>;


    onBackFromTrash:
        () => void | Promise<void>;


    onCreateProject:
        () => void;
}


// ============================================================
// COMPONENTE
// ============================================================

function DevelopmentProjectToolbar({
    viewMode,
    showTrash,
    creationOpen,

    canViewTrash,
    canCreateDevelopment,

    error,
    executionMessage,

    search,
    onSearchChange,

    projectCount,
    trashProjectCount,
    kanbanProjectCount,

    onShowProjects,
    onShowKanban,
    onOpenTrash,
    onBackFromTrash,
    onCreateProject,
}: DevelopmentProjectToolbarProps) {

    // ========================================================
    // TÍTULO DA ÁREA
    // ========================================================

    const title =
        showTrash
            ? "Lixeira de projetos"
            : (
                viewMode === "kanban"
                    ? "Workflow de desenvolvimento"
                    : "Projetos de automação"
            );


    // ========================================================
    // DESCRIÇÃO DA ÁREA
    // ========================================================

    const description =
        showTrash
            ? "Projetos removidos que ainda podem ser restaurados."
            : (
                viewMode === "kanban"
                    ? "Acompanhe e mova os projetos entre as etapas oficiais do desenvolvimento."
                    : "Workspaces editáveis usados para desenvolvimento e testes."
            );


    // ========================================================
    // PLACEHOLDER DA PESQUISA
    // ========================================================

    const searchPlaceholder =
        showTrash
            ? "Pesquisar na Lixeira..."
            : (
                viewMode === "kanban"
                    ? "Pesquisar no Kanban..."
                    : "Pesquisar projetos..."
            );


    // ========================================================
    // CONTADOR
    // ========================================================

    const count =
        showTrash
            ? trashProjectCount
            : (
                viewMode === "kanban"
                    ? kanbanProjectCount
                    : projectCount
            );


    const countLabel =
        showTrash
            ? "na lixeira"
            : (
                viewMode === "kanban"
                    ? "no quadro"
                    : "projetos"
            );


    // ========================================================
    // RENDERIZAÇÃO
    // ========================================================

    return (
        <>
            {/* =================================================
                CABEÇALHO DO PAINEL
            ================================================= */}

            <div className="content-panel-header ui-panel-header">

                {/* =============================================
                    IDENTIFICAÇÃO DA ÁREA
                ============================================= */}

                <div className="section-heading-group ui-panel-header__identity">

                    <div className="section-icon ui-panel-header__icon">

                        <Folder
                            size={18}
                            strokeWidth={1.8}
                        />

                    </div>


                    <div>

                        <h2>
                            {title}
                        </h2>


                        <p>
                            {description}
                        </p>

                    </div>

                </div>


                {/* =============================================
                    AÇÕES
                ============================================= */}

                <div className="panel-header-meta development-toolbar-actions ui-panel-header__actions">

                    {showTrash ? (

                        // =========================================
                        // LIXEIRA
                        // =========================================

                        <Button
                            onClick={() => {
                                void onBackFromTrash();
                            }}
                        >

                            <ArrowLeft
                                size={15}
                                strokeWidth={1.9}
                            />

                            Voltar aos projetos

                        </Button>

                    ) : (

                        // =========================================
                        // PROJETOS ATIVOS
                        // =========================================

                        <>
                            {/* =================================
                                SELETOR PROJETOS / KANBAN
                            ================================= */}

                            <div className="development-view-switcher" role="group" aria-label="Visualização do desenvolvimento">

                                <button
                                    type="button"
                                    aria-pressed={viewMode === "projects"}

                                    onClick={
                                        onShowProjects
                                    }

                                >
                                    <span className="development-view-switcher__icon"><LayoutGrid size={15} strokeWidth={1.9} aria-hidden="true" /></span>
                                    <span>Projetos</span>
                                    <small>{projectCount}</small>
                                </button>


                                <button
                                    type="button"
                                    aria-pressed={viewMode === "kanban"}

                                    onClick={() => {
                                        void onShowKanban();
                                    }}

                                >
                                    <span className="development-view-switcher__icon"><Columns3 size={15} strokeWidth={1.9} aria-hidden="true" /></span>
                                    <span>Kanban</span>
                                    <small>{kanbanProjectCount}</small>
                                </button>

                                {canViewTrash && (
                                    <button
                                        type="button"
                                        aria-pressed="false"
                                        onClick={() => void onOpenTrash()}
                                    >
                                        <span className="development-view-switcher__icon"><Trash2 size={15} strokeWidth={1.9} aria-hidden="true" /></span>
                                        <span>Lixeira</span>
                                        <small>{trashProjectCount}</small>
                                    </button>
                                )}

                            </div>


                            {/* =================================
                                NOVO PROJETO
                            ================================= */}

                            {canCreateDevelopment && (

                                <Button
                                    variant="primary"
                                    onClick={
                                        onCreateProject
                                    }
                                >

                                    <Plus
                                        size={15}
                                        strokeWidth={2}
                                    />

                                    Novo projeto

                                </Button>
                            )}

                        </>
                    )}

                </div>

            </div>


            {/* =================================================
                FEEDBACK DA PÁGINA
            ================================================= */}

            {error && (
                <FeedbackBanner
                    tone="error"
                    title="A operação de desenvolvimento não foi concluída"
                    message={error}
                    hint="Seu trabalho local foi preservado. Revise os dados, permissões e tente novamente."
                />
            )}


            {executionMessage && (
                <FeedbackBanner
                    tone="success"
                    title="Operação confirmada pelo Control Room"
                    message={executionMessage}
                />
            )}


            {/* =================================================
                PESQUISA
            ================================================= */}

            {!creationOpen && <div className="development-toolbar-search">
                <SearchField
                    label={searchPlaceholder}
                    containerClassName="development-toolbar-search__field"
                    value={search}
                    placeholder={searchPlaceholder}
                    onValueChange={onSearchChange}
                />


                {/* =============================================
                    CONTADOR
                ============================================= */}

                <div className="panel-header-meta development-count">
                    <span className="panel-count">
                        {count}
                    </span>

                    <span className="panel-count-label">
                        {countLabel}
                    </span>
                </div>

            </div>}
        </>
    );
}


export default DevelopmentProjectToolbar;

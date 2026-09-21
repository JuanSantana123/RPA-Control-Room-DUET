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
    Folder,
    FolderPlus,
    Plus,
    Search,
    Trash2,
} from "lucide-react";


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

            <div className="content-panel-header">

                {/* =============================================
                    IDENTIFICAÇÃO DA ÁREA
                ============================================= */}

                <div className="section-heading-group">

                    <div className="section-icon">

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

                <div className="panel-header-meta">

                    {showTrash ? (

                        // =========================================
                        // LIXEIRA
                        // =========================================

                        <button
                            type="button"
                            className="secondary-button"

                            onClick={() => {
                                void onBackFromTrash();
                            }}
                        >

                            <ArrowLeft
                                size={15}
                                strokeWidth={1.9}
                            />

                            Voltar aos projetos

                        </button>

                    ) : (

                        // =========================================
                        // PROJETOS ATIVOS
                        // =========================================

                        <>
                            {/* =================================
                                SELETOR PROJETOS / KANBAN
                            ================================= */}

                            <div
                                style={{
                                    display:
                                        "flex",

                                    alignItems:
                                        "center",

                                    gap:
                                        4,

                                    padding:
                                        3,

                                    border:
                                        "1px solid var(--border-color, #dfe3ea)",

                                    borderRadius:
                                        8,
                                }}
                            >

                                <button
                                    type="button"

                                    onClick={
                                        onShowProjects
                                    }

                                    style={{
                                        minHeight:
                                            30,

                                        padding:
                                            "5px 10px",

                                        border:
                                            "none",

                                        borderRadius:
                                            6,

                                        background:
                                            viewMode === "projects"
                                                ? "var(--surface-hover, rgba(100, 116, 139, 0.14))"
                                                : "transparent",

                                        color:
                                            "inherit",

                                        fontSize:
                                            12,

                                        fontWeight:
                                            700,

                                        cursor:
                                            "pointer",
                                    }}
                                >
                                    Projetos
                                </button>


                                <button
                                    type="button"

                                    onClick={() => {
                                        void onShowKanban();
                                    }}

                                    style={{
                                        minHeight:
                                            30,

                                        padding:
                                            "5px 10px",

                                        border:
                                            "none",

                                        borderRadius:
                                            6,

                                        background:
                                            viewMode === "kanban"
                                                ? "var(--surface-hover, rgba(100, 116, 139, 0.14))"
                                                : "transparent",

                                        color:
                                            "inherit",

                                        fontSize:
                                            12,

                                        fontWeight:
                                            700,

                                        cursor:
                                            "pointer",
                                    }}
                                >
                                    Kanban
                                </button>

                            </div>


                            {/* =================================
                                LIXEIRA
                            ================================= */}

                            {canViewTrash && (

                                <button
                                    type="button"
                                    className="secondary-button"

                                    onClick={() => {
                                        void onOpenTrash();
                                    }}
                                >

                                    <Trash2
                                        size={15}
                                        strokeWidth={1.9}
                                    />

                                    Lixeira

                                </button>
                            )}


                            {/* =================================
                                NOVA PASTA
                            =================================
                                
                                Mantém exatamente o estado atual:
                                botão visível, porém desabilitado.
                            ================================= */}

                            {canCreateDevelopment && (

                                <button
                                    type="button"
                                    className="secondary-button"

                                    disabled

                                    title={
                                        "Pastas serão ligadas ao backend na próxima etapa."
                                    }
                                >

                                    <FolderPlus
                                        size={15}
                                        strokeWidth={1.9}
                                    />

                                    Nova pasta

                                </button>
                            )}


                            {/* =================================
                                NOVO PROJETO
                            ================================= */}

                            {canCreateDevelopment && (

                                <button
                                    type="button"
                                    className="primary-button"

                                    onClick={
                                        onCreateProject
                                    }
                                >

                                    <Plus
                                        size={15}
                                        strokeWidth={2}
                                    />

                                    Novo projeto

                                </button>
                            )}

                        </>
                    )}

                </div>

            </div>


            {/* =================================================
                FEEDBACK DA PÁGINA
            ================================================= */}

            {error && (

                <div className="alert alert-error">
                    {error}
                </div>
            )}


            {executionMessage && (

                <div
                    role="status"

                    style={{
                        marginBottom:
                            16,

                        padding:
                            "10px 12px",

                        border:
                            "1px solid rgba(22, 163, 74, 0.28)",

                        borderRadius:
                            8,

                        background:
                            "rgba(22, 163, 74, 0.08)",

                        fontSize:
                            13,

                        lineHeight:
                            1.45,
                    }}
                >
                    {executionMessage}
                </div>
            )}


            {/* =================================================
                PESQUISA
            ================================================= */}

            <div
                style={{
                    display:
                        "flex",

                    alignItems:
                        "center",

                    gap:
                        10,

                    marginBottom:
                        18,
                }}
            >

                <div
                    style={{
                        flex:
                            1,

                        position:
                            "relative",
                    }}
                >

                    <Search
                        size={16}
                        strokeWidth={1.8}

                        style={{
                            position:
                                "absolute",

                            left:
                                12,

                            top:
                                "50%",

                            transform:
                                "translateY(-50%)",

                            opacity:
                                0.65,

                            pointerEvents:
                                "none",
                        }}
                    />


                    <input
                        type="text"

                        value={
                            search
                        }

                        placeholder={
                            searchPlaceholder
                        }

                        onChange={(event) => {

                            onSearchChange(
                                event.target.value
                            );
                        }}

                        style={{
                            width:
                                "100%",

                            boxSizing:
                                "border-box",

                            paddingLeft:
                                38,
                        }}
                    />

                </div>


                {/* =============================================
                    CONTADOR
                ============================================= */}

                <span className="panel-count">
                    {count}
                </span>


                <span className="panel-count-label">
                    {countLabel}
                </span>

            </div>
        </>
    );
}


export default DevelopmentProjectToolbar;
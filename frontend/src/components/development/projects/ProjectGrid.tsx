// ============================================================
// PROJECT GRID
// ============================================================
//
// Responsabilidade:
//     Renderiza a visualização em grade dos AutomationProjects
//     ativos da área de Desenvolvimento do DUET CORE.
//
// Este componente apresenta:
//     - estado de carregamento;
//     - estado vazio;
//     - ausência de resultados da pesquisa;
//     - cards dos projetos;
//     - status amigável do projeto;
//     - acesso ao DUET Studio;
//     - execução em Agent;
//     - botão de opções do projeto.
//
// Arquitetura:
//     Este componente é exclusivamente visual.
//
// Este arquivo NÃO deve:
//     - consultar projetos;
//     - excluir projetos;
//     - executar projetos diretamente;
//     - navegar diretamente pelo React Router;
//     - abrir menus através de regra própria;
//     - realizar chamadas HTTP.
//
// Development.tsx continua responsável por:
//     - carregar projetos;
//     - aplicar a pesquisa;
//     - permissões;
//     - abrir o Studio;
//     - preparar execução;
//     - controlar o menu de opções;
//     - operações de exclusão.
//
// ProjectGrid.tsx:
//     - recebe os projetos já filtrados;
//     - apresenta os cards;
//     - encaminha as interações através de callbacks.
// ============================================================

import {
    Code2,
    MoreVertical,
    Play,
} from "lucide-react";


import type {
    MouseEvent,
} from "react";


import type {
    DevelopmentProject,
} from "../../../types/development";


// ============================================================
// PROPS
// ============================================================

interface ProjectGridProps {

    // Projetos atualmente visíveis.
    //
    // A pesquisa continua sendo realizada pelo componente pai.
    projects:
        DevelopmentProject[];


    // Quantidade total de projetos antes do filtro de pesquisa.
    //
    // Permite diferenciar:
    //
    // 0:
    //     nenhum projeto foi criado.
    //
    // > 0 com projects.length === 0:
    //     pesquisa sem resultado.
    totalProjectCount:
        number;


    // Carregamento inicial dos projetos.
    loading:
        boolean;


    // ========================================================
    // PERMISSÕES
    // ========================================================

    canDelete:
        boolean;


    canExecute:
        boolean;


    // ========================================================
    // MENU
    // ========================================================

    // Projeto cujo menu de três pontos está atualmente aberto.
    //
    // null:
    //     nenhum menu aberto.
    openMenuProjectId:
        number | null;


    // ========================================================
    // EXECUÇÃO
    // ========================================================

    // Enquanto qualquer projeto estiver iniciando uma execução,
    // os demais botões de execução permanecem bloqueados,
    // preservando o comportamento atual.
    executingProjectId:
        number | null;


    // ========================================================
    // CALLBACKS
    // ========================================================

    onToggleMenu: (
        event: MouseEvent<HTMLButtonElement>,
        projectId: number
    ) => void;


    onOpenStudio:
        (
            project: DevelopmentProject
        ) => void;


    onExecute:
        (
            project: DevelopmentProject
        ) => void | Promise<void>;
}


// ============================================================
// LABEL VISUAL DE STATUS
// ============================================================
//
// Esta função é puramente de apresentação.
//
// Ela foi movida para este componente porque o texto é usado
// exclusivamente pelos cards da lista de projetos.
// ============================================================

const getStatusLabel = (
    project: DevelopmentProject
): string => {

    // Projeto alterado a partir de uma versão existente.
    if (
        project.status ===
        "modified"
    ) {

        return "Alterações em desenvolvimento";
    }


    // Projeto que já possui publicação registrada.
    if (
        project.status ===
        "published"
    ) {

        return project.base_version
            ? `Base: v${project.base_version}`
            : "Publicado";
    }


    // Projeto ainda sem publicação.
    return "Não publicado";
};


// ============================================================
// COMPONENTE
// ============================================================

function ProjectGrid({
    projects,
    totalProjectCount,

    loading,

    canDelete,
    canExecute,

    openMenuProjectId,

    executingProjectId,

    onToggleMenu,
    onOpenStudio,
    onExecute,
}: ProjectGridProps) {

    // ========================================================
    // CARREGAMENTO
    // ========================================================

    if (loading) {

        return (

            <div className="panel-empty-state">

                <div className="panel-empty-icon">

                    <Code2
                        size={24}
                        strokeWidth={1.6}
                    />

                </div>


                <h3>
                    Carregando projetos...
                </h3>


                <p>
                    Buscando os projetos no Control Room.
                </p>

            </div>
        );
    }


    // ========================================================
    // SEM PROJETOS / SEM RESULTADO NA PESQUISA
    // ========================================================

    if (
        projects.length === 0
    ) {

        const projectListIsEmpty =
            totalProjectCount === 0;


        return (

            <div className="panel-empty-state">

                <div className="panel-empty-icon">

                    <Code2
                        size={24}
                        strokeWidth={1.6}
                    />

                </div>


                <h3>

                    {projectListIsEmpty
                        ? "Nenhum projeto em desenvolvimento"
                        : "Nenhum projeto encontrado"}

                </h3>


                <p>

                    {projectListIsEmpty
                        ? "Crie um projeto para começar a desenvolver uma nova automação."
                        : "Tente pesquisar por outro nome ou descrição."}

                </p>

            </div>
        );
    }


    // ========================================================
    // GRADE DE PROJETOS
    // ========================================================

    return (

        <div className="robots-grid">

            {projects.map(
                (project) => (

                    <article
                        key={
                            project.id
                        }

                        className="robot-card"
                    >

                        {/* =========================================
                            TOPO
                        ========================================= */}

                        <div className="robot-card-top">

                            <div className="robot-card-icon">

                                <Code2
                                    size={20}
                                    strokeWidth={1.7}
                                />

                            </div>


                            {/* =====================================
                                MENU DE OPÇÕES
                            ===================================== */}

                            {canDelete && (

                                <button
                                    type="button"

                                    className="robot-card-menu"

                                    // O posicionamento e abertura efetiva
                                    // do menu continuam no Development.tsx.
                                    onClick={(event) => {

                                        onToggleMenu(
                                            event,
                                            project.id
                                        );
                                    }}

                                    title="Opções do projeto"

                                    aria-label={
                                        `Opções do projeto ${project.name}`
                                    }

                                    aria-haspopup="menu"

                                    aria-expanded={
                                        openMenuProjectId ===
                                        project.id
                                    }
                                >

                                    <MoreVertical
                                        size={17}
                                        strokeWidth={1.8}
                                    />

                                </button>
                            )}

                        </div>


                        {/* =========================================
                            DADOS
                        ========================================= */}

                        <div className="robot-card-body">

                            <h3>
                                {project.name}
                            </h3>


                            <p className="robot-filename">

                                {project.description ||
                                    "Projeto de automação DUET CORE"}

                            </p>


                            {/* =====================================
                                ORIGEM DO PROJETO
                            ===================================== */}

                            <div className="robot-card-meta">

                                <span>
                                    {project.base_robot_id
                                        ? "Robô de origem"
                                        : "Origem"}
                                </span>


                                <strong>
                                    {project.base_robot_id
                                        ? (
                                            project.base_robot_name ||
                                            `Robot #${project.base_robot_id}`
                                        )
                                        : "Novo projeto"}
                                </strong>

                            </div>


                            {/* =====================================
                                STATUS
                            ===================================== */}

                            <div className="robot-card-meta">

                                <span>
                                    Status
                                </span>


                                <strong>
                                    {getStatusLabel(
                                        project
                                    )}
                                </strong>

                            </div>

                        </div>


                        {/* =========================================
                            AÇÕES
                        ========================================= */}

                        <div className="robot-card-actions">

                            {/* =====================================
                                STUDIO
                            ===================================== */}

                            <button
                                type="button"

                                className="primary-button"

                                onClick={() => {

                                    onOpenStudio(
                                        project
                                    );
                                }}
                            >

                                <Code2
                                    size={15}
                                    strokeWidth={1.9}
                                />

                                Abrir no Studio

                            </button>


                            {/* =====================================
                                EXECUÇÃO
                            ===================================== */}

                            {canExecute && (

                                <button
                                    type="button"

                                    className="secondary-button"

                                    disabled={
                                        executingProjectId !==
                                        null
                                    }

                                    onClick={() => {

                                        onExecute(
                                            project
                                        );
                                    }}
                                >

                                    <Play
                                        size={15}
                                        strokeWidth={1.9}
                                    />

                                    Executar

                                </button>
                            )}

                        </div>

                    </article>
                )
            )}

        </div>
    );
}


export default ProjectGrid;
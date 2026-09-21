// ============================================================
// TRASH PROJECT GRID
// ============================================================
//
// Responsabilidade:
//     Renderiza a visualização dos AutomationProjects presentes
//     na Lixeira da área de Desenvolvimento do DUET CORE.
//
// Este componente apresenta:
//     - estado de carregamento da Lixeira;
//     - estado vazio;
//     - resultado vazio após pesquisa;
//     - cards dos projetos removidos;
//     - usuário responsável pela exclusão;
//     - data da exclusão;
//     - ação de restaurar;
//     - ação de excluir permanentemente.
//
// Arquitetura:
//     Este componente é exclusivamente visual.
//
// Ele NÃO deve:
//     - consultar a Lixeira;
//     - restaurar projetos diretamente;
//     - excluir projetos diretamente;
//     - executar chamadas HTTP;
//     - alterar listas globais;
//     - controlar permissões.
//
// Development.tsx continua responsável por:
//     - GET /development/projects/trash;
//     - POST de restauração;
//     - DELETE permanente;
//     - permissões;
//     - estados operacionais.
//
// TrashProjectGrid.tsx:
//     - recebe dados por props;
//     - apresenta os cards;
//     - encaminha ações ao componente pai.
// ============================================================

import {
    RotateCcw,
    Trash2,
} from "lucide-react";


import type {
    DevelopmentProject,
} from "../../../types/development";


import {
    formatDeletedAt,
} from "../../../utils/dateTime";


// ============================================================
// PROPS
// ============================================================

interface TrashProjectGridProps {

    // Projetos atualmente visíveis.
    //
    // Essa lista já chega filtrada pelo Development.tsx
    // quando existe uma pesquisa ativa.
    projects:
        DevelopmentProject[];


    // Quantidade total de projetos presentes na Lixeira antes
    // da aplicação da pesquisa.
    //
    // Permite diferenciar:
    //
    // 0:
    //     Lixeira realmente vazia.
    //
    // > 0 com projects.length === 0:
    //     pesquisa sem resultados.
    totalProjectCount:
        number;


    // Consulta da Lixeira ainda em andamento.
    loading:
        boolean;


    // ========================================================
    // PERMISSÕES
    // ========================================================

    canRestore:
        boolean;


    canPermanentDelete:
        boolean;


    // ========================================================
    // ESTADOS OPERACIONAIS
    // ========================================================

    // Projeto que está sendo restaurado.
    restoringProjectId:
        number | null;


    // Projeto que está sendo apagado definitivamente.
    permanentlyDeletingProjectId:
        number | null;


    // ========================================================
    // AÇÕES
    // ========================================================

    onRestore:
        (
            project: DevelopmentProject
        ) => void | Promise<void>;


    onPermanentDelete:
        (
            project: DevelopmentProject
        ) => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function TrashProjectGrid({
    projects,
    totalProjectCount,

    loading,

    canRestore,
    canPermanentDelete,

    restoringProjectId,
    permanentlyDeletingProjectId,

    onRestore,
    onPermanentDelete,
}: TrashProjectGridProps) {

    // ========================================================
    // CARREGANDO
    // ========================================================

    if (loading) {

        return (

            <div className="panel-empty-state">

                <div className="panel-empty-icon">

                    <Trash2
                        size={24}
                        strokeWidth={1.6}
                    />

                </div>


                <h3>
                    Carregando Lixeira...
                </h3>


                <p>
                    Buscando projetos removidos no Control Room.
                </p>

            </div>
        );
    }


    // ========================================================
    // LIXEIRA VAZIA / PESQUISA SEM RESULTADO
    // ========================================================

    if (
        projects.length === 0
    ) {

        const trashIsEmpty =
            totalProjectCount === 0;


        return (

            <div className="panel-empty-state">

                <div className="panel-empty-icon">

                    <Trash2
                        size={24}
                        strokeWidth={1.6}
                    />

                </div>


                <h3>

                    {trashIsEmpty
                        ? "A Lixeira está vazia"
                        : "Nenhum projeto encontrado"}

                </h3>


                <p>

                    {trashIsEmpty
                        ? "Projetos excluídos aparecerão aqui antes da remoção permanente."
                        : "Tente pesquisar por outro nome ou descrição."}

                </p>

            </div>
        );
    }


    // ========================================================
    // PROJETOS DA LIXEIRA
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

                                <Trash2
                                    size={20}
                                    strokeWidth={1.7}
                                />

                            </div>

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
                                USUÁRIO QUE EXCLUIU
                            ===================================== */}

                            <div className="robot-card-meta">

                                <span>
                                    Excluído por
                                </span>


                                <strong>

                                    {project.deleted_by_name ||
                                        (
                                            project.deleted_by
                                                ? `Usuário #${project.deleted_by}`
                                                : "Não registrado"
                                        )}

                                </strong>

                            </div>


                            {/* =====================================
                                DATA DA EXCLUSÃO
                            ===================================== */}

                            <div className="robot-card-meta">

                                <span>
                                    Data da exclusão
                                </span>


                                <strong>

                                    {formatDeletedAt(
                                        project.deleted_at
                                    )}

                                </strong>

                            </div>

                        </div>


                        {/* =========================================
                            AÇÕES
                        ========================================= */}

                        {(
                            canRestore ||
                            canPermanentDelete
                        ) && (

                            <div className="robot-card-actions">

                                {/* =================================
                                    RESTAURAR
                                ================================= */}

                                {canRestore && (

                                    <button
                                        type="button"

                                        className="primary-button"

                                        disabled={
                                            restoringProjectId ===
                                                project.id ||
                                            permanentlyDeletingProjectId !==
                                                null
                                        }

                                        onClick={() => {

                                            onRestore(
                                                project
                                            );
                                        }}
                                    >

                                        <RotateCcw
                                            size={15}
                                            strokeWidth={1.9}
                                        />


                                        {restoringProjectId ===
                                            project.id
                                            ? "Restaurando..."
                                            : "Restaurar"}

                                    </button>
                                )}


                                {/* =================================
                                    EXCLUIR PERMANENTEMENTE
                                ================================= */}

                                {canPermanentDelete && (

                                    <button
                                        type="button"

                                        className="secondary-button"

                                        disabled={
                                            permanentlyDeletingProjectId ===
                                                project.id ||
                                            restoringProjectId !==
                                                null
                                        }

                                        onClick={() => {

                                            onPermanentDelete(
                                                project
                                            );
                                        }}

                                        style={{
                                            color:
                                                "#dc2626",
                                        }}
                                    >

                                        <Trash2
                                            size={15}
                                            strokeWidth={1.9}
                                        />


                                        {permanentlyDeletingProjectId ===
                                            project.id
                                            ? "Excluindo..."
                                            : "Excluir permanentemente"}

                                    </button>
                                )}

                            </div>
                        )}

                    </article>
                )
            )}

        </div>
    );
}


export default TrashProjectGrid;
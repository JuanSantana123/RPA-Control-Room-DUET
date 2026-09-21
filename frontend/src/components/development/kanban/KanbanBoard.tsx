// ============================================================
// KANBAN BOARD
// ============================================================
//
// Responsabilidade:
//     Renderiza o quadro completo de Workflow da área de
//     Desenvolvimento do DUET CORE.
//
// Este componente apresenta:
//     - estado de carregamento do Workflow;
//     - estado de Workflow não configurado;
//     - container horizontal do Kanban;
//     - todas as colunas do Workflow;
//     - encaminhamento dos eventos de drag-and-drop;
//     - encaminhamento das ações dos cards.
//
// Arquitetura:
//     Este componente é exclusivamente visual.
//
// Este arquivo NÃO deve:
//     - carregar o Workflow;
//     - persistir movimentações;
//     - publicar projetos;
//     - abrir APIs diretamente;
//     - alterar projetos no banco;
//     - controlar permissões por conta própria.
//
// Development.tsx continua responsável por:
//     - GET /development/workflow/board;
//     - estado das etapas;
//     - pesquisa;
//     - drag-and-drop;
//     - movimentação entre etapas;
//     - abertura de detalhes;
//     - abertura do Studio;
//     - preparação do Release.
//
// KanbanBoard.tsx:
//     - recebe todos os dados por props;
//     - apresenta o quadro;
//     - distribui os dados para KanbanColumn;
//     - encaminha eventos ao componente pai.
// ============================================================

import {
    Code2,
} from "lucide-react";


import type {
    DragEvent,
} from "react";


import type {
    DevelopmentProject,
    DevelopmentStage,
} from "../../../types/development";


import KanbanColumn
    from "./KanbanColumn";


// ============================================================
// PROPS
// ============================================================

interface KanbanBoardProps {

    // ========================================================
    // DADOS DO WORKFLOW
    // ========================================================

    // Todas as etapas ativas retornadas pelo backend.
    //
    // É utilizada para identificar se o Workflow realmente
    // não possui nenhuma configuração.
    stages:
        DevelopmentStage[];


    // Etapas já filtradas pela pesquisa.
    //
    // A filtragem continua sendo responsabilidade
    // do Development.tsx.
    filteredStages:
        DevelopmentStage[];


    // Texto de pesquisa atual.
    //
    // KanbanColumn utiliza esse valor para distinguir uma
    // coluna realmente vazia de uma coluna sem resultados
    // por causa da pesquisa.
    search:
        string;


    // ========================================================
    // CARREGAMENTO
    // ========================================================

    loading:
        boolean;


    // ========================================================
    // DRAG-AND-DROP
    // ========================================================

    dragOverStageId:
        number | null;


    draggedSourceStageCode:
        string | null;


    movingProjectId:
        number | null;


    draggedProjectId:
        number | null;


    // ========================================================
    // PERMISSÕES
    // ========================================================

    canMoveDevelopmentStage:
        boolean;


    canPublishDevelopment:
        boolean;


    // ========================================================
    // RELEASE
    // ========================================================

    // Projeto cuja publicação está sendo executada.
    //
    // Enquanto preenchido, as colunas podem impedir uma
    // segunda publicação simultânea.
    publishingProjectId:
        number | null;


    // ========================================================
    // EVENTOS DAS COLUNAS
    // ========================================================

    onDragOverStage:
        (
            stageId: number | null
        ) => void;


    onDrop:
        (
            event: DragEvent<HTMLElement>,
            targetStage: DevelopmentStage
        ) => void | Promise<void>;


    // ========================================================
    // EVENTOS DOS CARDS
    // ========================================================

    onCardDragStart:
        (
            event: DragEvent<HTMLElement>,
            project: DevelopmentProject,
            stage: DevelopmentStage
        ) => void;


    onCardDragEnd:
        () => void;


    // ========================================================
    // AÇÕES DOS CARDS
    // ========================================================

    onOpenDetails:
        (
            project: DevelopmentProject
        ) => void | Promise<void>;


    onOpenStudio:
        (
            project: DevelopmentProject
        ) => void;


    onPublish:
        (
            project: DevelopmentProject
        ) => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function KanbanBoard({
    stages,
    filteredStages,
    search,

    loading,

    dragOverStageId,
    draggedSourceStageCode,
    movingProjectId,
    draggedProjectId,

    canMoveDevelopmentStage,
    canPublishDevelopment,

    publishingProjectId,

    onDragOverStage,
    onDrop,

    onCardDragStart,
    onCardDragEnd,

    onOpenDetails,
    onOpenStudio,
    onPublish,
}: KanbanBoardProps) {

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
                    Carregando Kanban...
                </h3>


                <p>
                    Buscando o Workflow oficial no Control Room.
                </p>

            </div>
        );
    }


    // ========================================================
    // WORKFLOW NÃO CONFIGURADO
    // ========================================================

    if (
        stages.length === 0
    ) {

        return (

            <div className="panel-empty-state">

                <div className="panel-empty-icon">

                    <Code2
                        size={24}
                        strokeWidth={1.6}
                    />

                </div>


                <h3>
                    Workflow não configurado
                </h3>


                <p>
                    Nenhum estágio ativo foi retornado pelo Control Room.
                </p>

            </div>
        );
    }


    // ========================================================
    // QUADRO KANBAN
    // ========================================================

    return (

        <div
            style={{
                width:
                    "100%",

                overflowX:
                    "auto",

                paddingBottom:
                    12,
            }}
        >

            <div
                style={{
                    display:
                        "flex",

                    alignItems:
                        "stretch",

                    gap:
                        14,

                    minWidth:
                        "max-content",
                }}
            >

                {/* =================================================
                    COLUNAS DO KANBAN
                ================================================= */}

                {filteredStages.map(
                    (stage) => (

                        <KanbanColumn
                            key={
                                stage.id
                            }


                            // =========================================
                            // ETAPA
                            // =========================================

                            stage={
                                stage
                            }


                            // Permite que a coluna diferencie:
                            //
                            // - coluna realmente sem projetos;
                            // - pesquisa sem resultados.
                            search={
                                search
                            }


                            // =========================================
                            // DRAG-AND-DROP - ESTADO
                            // =========================================

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


                            // =========================================
                            // PERMISSÕES
                            // =========================================

                            canMoveDevelopmentStage={
                                canMoveDevelopmentStage
                            }

                            canPublishDevelopment={
                                canPublishDevelopment
                            }


                            // =========================================
                            // RELEASE
                            // =========================================

                            publishingProjectId={
                                publishingProjectId
                            }


                            // =========================================
                            // EVENTOS DA COLUNA
                            // =========================================

                            onDragOverStage={
                                onDragOverStage
                            }

                            onDrop={
                                onDrop
                            }


                            // =========================================
                            // EVENTOS DOS CARDS
                            // =========================================

                            onCardDragStart={
                                onCardDragStart
                            }

                            onCardDragEnd={
                                onCardDragEnd
                            }


                            // =========================================
                            // AÇÕES DOS CARDS
                            // =========================================

                            onOpenDetails={
                                onOpenDetails
                            }

                            onOpenStudio={
                                onOpenStudio
                            }

                            onPublish={
                                onPublish
                            }
                        />
                    )
                )}

            </div>

        </div>
    );
}


export default KanbanBoard;
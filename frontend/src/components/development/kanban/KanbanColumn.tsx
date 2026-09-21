// ============================================================
// KANBAN COLUMN
// ============================================================
//
// Responsabilidade:
//     Renderiza uma coluna individual do Workflow / Kanban
//     da área de Desenvolvimento do DUET CORE.
//
// Este componente apresenta:
//     - nome da etapa;
//     - quantidade de projetos;
//     - estado de leitura/publicação protegida;
//     - área visual de drop;
//     - mensagem de coluna vazia;
//     - cards pertencentes à etapa.
//
// Também participa do drag-and-drop entre etapas.
//
// Arquitetura:
//     A coluna recebe todos os dados e callbacks necessários
//     através de props.
//
// Este arquivo NÃO deve:
//     - realizar chamadas HTTP;
//     - carregar o Workflow;
//     - persistir mudança de estágio;
//     - controlar o estado global do Kanban;
//     - conhecer endpoints do backend.
//
// Development.tsx continua responsável pelas regras de
// movimentação e persistência.
//
// KanbanColumn.tsx controla somente a apresentação da coluna
// e encaminha os eventos para o componente pai.
//
// Estrutura:
//
//     Development.tsx
//         ↓
//     KanbanColumn.tsx
//         ↓
//     KanbanCard.tsx
//
// Objetivo arquitetural:
//     Isolar a estrutura visual e os eventos de uma coluna do
//     Kanban, reduzindo significativamente o JSX concentrado
//     dentro de Development.tsx.
// ============================================================

import type {
    DragEvent,
} from "react";


import KanbanCard
    from "./KanbanCard";


import type {
    DevelopmentProject,
    DevelopmentStage,
} from "../../../types/development";


// ============================================================
// PROPS
// ============================================================

interface KanbanColumnProps {

    // Etapa representada por esta coluna.
    stage: DevelopmentStage;


    // Texto atualmente utilizado no filtro do Kanban.
    //
    // É utilizado para diferenciar:
    //
    // "Nenhum projeto nesta etapa."
    //
    // de:
    //
    // "Nenhum projeto encontrado nesta etapa."
    search: string;


    // ========================================================
    // DRAG-AND-DROP - ESTADO GLOBAL
    // ========================================================

    // Coluna atualmente destacada como destino.
    dragOverStageId: number | null;


    // Código da etapa de origem do projeto arrastado.
    //
    // É utilizado principalmente para impedir movimentações
    // originadas da etapa PUBLISHED.
    draggedSourceStageCode: string | null;


    // Projeto atualmente sendo persistido em outra etapa.
    movingProjectId: number | null;


    // Projeto atualmente sendo arrastado.
    draggedProjectId: number | null;


    // ========================================================
    // PERMISSÕES
    // ========================================================

    canMoveDevelopmentStage: boolean;

    canPublishDevelopment: boolean;


    // ========================================================
    // PUBLICAÇÃO
    // ========================================================

    // null:
    //     nenhum Release sendo publicado.
    //
    // number:
    //     ID do projeto cujo Release está em andamento.
    publishingProjectId: number | null;


    // ========================================================
    // EVENTOS DA COLUNA
    // ========================================================

    // Informa ao componente pai qual coluna está atualmente
    // sob o cursor durante o drag.
    onDragOverStage:
        (stageId: number) => void;


    // Solicita ao Development.tsx a movimentação efetiva
    // do projeto para esta etapa.
    onDrop: (
        event: DragEvent<HTMLElement>,
        stage: DevelopmentStage
    ) => void;


    // ========================================================
    // EVENTOS DOS CARDS
    // ========================================================

    onCardDragStart: (
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
        (project: DevelopmentProject) => void;


    onOpenStudio:
        (project: DevelopmentProject) => void;


    onPublish:
        (project: DevelopmentProject) => void;
}


// ============================================================
// COMPONENTE
// ============================================================

function KanbanColumn({
    stage,

    search,

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
}: KanbanColumnProps) {

    // ========================================================
    // ESTADO DA ETAPA
    // ========================================================

    // A etapa PUBLISHED representa uma versão protegida.
    //
    // Projetos desta etapa não podem ser utilizados como
    // origem nem destino de drag-and-drop.
    const publishedStage =
        stage.code ===
        "PUBLISHED";


    // Define se esta coluna deve receber o destaque visual
    // de destino do drag-and-drop.
    const isDropTarget =
        dragOverStageId ===
            stage.id &&
        !publishedStage &&
        draggedSourceStageCode !==
            "PUBLISHED";


    // ========================================================
    // INTERFACE
    // ========================================================

    return (

        <section

            // ====================================================
            // DRAG OVER
            // ====================================================
            //
            // Apenas etapas editáveis podem se tornar destino.
            // ====================================================

            onDragOver={(event) => {

                if (
                    !canMoveDevelopmentStage ||
                    publishedStage ||
                    draggedSourceStageCode ===
                        "PUBLISHED"
                ) {
                    return;
                }


                // Necessário para permitir o evento onDrop
                // no navegador.
                event.preventDefault();


                event.dataTransfer.dropEffect =
                    "move";


                onDragOverStage(
                    stage.id
                );
            }}


            // ====================================================
            // DROP
            // ====================================================

            onDrop={(event) => {

                onDrop(
                    event,
                    stage
                );
            }}


            // ====================================================
            // VISUAL DA COLUNA
            // ====================================================

            style={{
                width:
                    286,

                minWidth:
                    286,

                flex:
                    "0 0 286px",

                display:
                    "flex",

                flexDirection:
                    "column",

                maxHeight:
                    "calc(100vh - 335px)",

                minHeight:
                    300,

                padding:
                    12,


                // Destaca visualmente a coluna quando ela
                // é um destino válido do projeto arrastado.
                border:
                    isDropTarget
                        ? "1px solid var(--accent-color, #2563eb)"
                        : "1px solid var(--border-color, #dfe3ea)",


                borderRadius:
                    10,


                background:
                    isDropTarget
                        ? "var(--surface-hover, rgba(37, 99, 235, 0.06))"
                        : "var(--surface-color, #ffffff)",


                boxSizing:
                    "border-box",
            }}
        >

            {/* =================================================
                CABEÇALHO DA COLUNA
            ================================================= */}

            <div
                style={{
                    display:
                        "flex",

                    alignItems:
                        "center",

                    justifyContent:
                        "space-between",

                    gap:
                        10,

                    marginBottom:
                        10,

                    paddingBottom:
                        10,

                    borderBottom:
                        "1px solid var(--border-color, #dfe3ea)",
                }}
            >

                {/* =============================================
                    NOME / DESCRIÇÃO
                ============================================= */}

                <div
                    style={{
                        minWidth:
                            0,
                    }}
                >

                    <div
                        style={{
                            fontSize:
                                13,

                            fontWeight:
                                800,

                            lineHeight:
                                1.3,
                        }}
                    >
                        {stage.name}
                    </div>


                    <div
                        style={{
                            marginTop:
                                3,

                            fontSize:
                                11,

                            opacity:
                                0.6,
                        }}
                    >

                        {publishedStage
                            ? "Publicação protegida"
                            : (
                                canMoveDevelopmentStage
                                    ? "Arraste projetos para esta etapa"
                                    : "Somente leitura"
                            )}

                    </div>

                </div>


                {/* =============================================
                    CONTADOR
                ============================================= */}

                <span

                    // Quando há pesquisa ativa mostramos no tooltip
                    // a relação entre quantidade visível e total.
                    title={
                        search.trim()
                            ? `${stage.projects.length} visíveis de ${stage.total_projects}`
                            : `${stage.total_projects} projetos`
                    }

                    style={{
                        display:
                            "inline-flex",

                        alignItems:
                            "center",

                        justifyContent:
                            "center",

                        minWidth:
                            28,

                        height:
                            24,

                        padding:
                            "0 7px",

                        borderRadius:
                            999,

                        background:
                            "var(--surface-hover, rgba(100, 116, 139, 0.12))",

                        fontSize:
                            11,

                        fontWeight:
                            800,

                        boxSizing:
                            "border-box",
                    }}
                >

                    {search.trim()
                        ? `${stage.projects.length}/${stage.total_projects}`
                        : stage.total_projects}

                </span>

            </div>


            {/* =================================================
                CARDS DA COLUNA
            ================================================= */}

            <div
                style={{
                    flex:
                        1,

                    minHeight:
                        120,

                    overflowY:
                        "auto",

                    paddingRight:
                        3,

                    display:
                        "flex",

                    flexDirection:
                        "column",

                    gap:
                        9,
                }}
            >

                {/* =============================================
                    COLUNA VAZIA
                ============================================= */}

                {stage.projects.length ===
                0 ? (

                    <div
                        style={{
                            minHeight:
                                92,

                            display:
                                "flex",

                            alignItems:
                                "center",

                            justifyContent:
                                "center",

                            padding:
                                16,

                            border:
                                "1px dashed var(--border-color, #dfe3ea)",

                            borderRadius:
                                8,

                            textAlign:
                                "center",

                            fontSize:
                                12,

                            opacity:
                                0.58,

                            boxSizing:
                                "border-box",
                        }}
                    >

                        {search.trim()
                            ? "Nenhum projeto encontrado nesta etapa."
                            : "Nenhum projeto nesta etapa."}

                    </div>

                ) : (

                    // =========================================
                    // CARDS
                    // =========================================
                    //
                    // Cada AutomationProject passa a ser
                    // renderizado pelo componente KanbanCard.
                    // =========================================

                    stage.projects.map(
                        (project) => (

                            <KanbanCard
                                key={
                                    project.id
                                }


                                // Projeto e etapa.
                                project={
                                    project
                                }

                                stage={
                                    stage
                                }


                                // Estado de movimentação.
                                movingProjectId={
                                    movingProjectId
                                }

                                draggedProjectId={
                                    draggedProjectId
                                }


                                // Permissões.
                                canMoveDevelopmentStage={
                                    canMoveDevelopmentStage
                                }

                                canPublishDevelopment={
                                    canPublishDevelopment
                                }


                                // Release atualmente em andamento.
                                publishingProjectId={
                                    publishingProjectId
                                }


                                // Drag-and-drop.
                                onDragStart={
                                    onCardDragStart
                                }

                                onDragEnd={
                                    onCardDragEnd
                                }


                                // Ações do card.
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
                    )
                )}

            </div>

        </section>
    );
}


export default KanbanColumn;
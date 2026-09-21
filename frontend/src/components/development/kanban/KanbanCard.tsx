// ============================================================
// KANBAN CARD
// ============================================================
//
// Responsabilidade:
//     Renderiza um AutomationProject individual dentro de uma
//     coluna do Workflow / Kanban de Desenvolvimento.
//
// Este componente apresenta:
//     - título e ID da demanda;
//     - Checkout atual;
//     - responsáveis funcional e técnico;
//     - período planejado;
//     - esforço estimado;
//     - quantidade de comentários;
//     - estágio atual;
//     - ações de detalhes, Studio e publicação.
//
// Também participa do drag-and-drop do Kanban.
//
// Arquitetura:
//     O componente recebe projeto, estágio, permissões e ações
//     através de props.
//
// Este arquivo NÃO deve:
//     - realizar chamadas HTTP;
//     - carregar o Workflow;
//     - alterar diretamente estados globais da página;
//     - conhecer endpoints do backend;
//     - controlar outras colunas do Kanban.
//
// As regras de movimentação, abertura e publicação continuam
// sendo orquestradas por Development.tsx nesta etapa.
//
// Objetivo:
//     Retirar a representação visual de cada card do arquivo
//     principal e permitir reutilização e manutenção isoladas.
// ============================================================

import type {
    DragEvent,
} from "react";


import type {
    DevelopmentProject,
    DevelopmentStage,
} from "../../../types/development";


import {
    formatCardDate,
    parseApiDateTime,
} from "../../../utils/dateTime";


// ============================================================
// PROPS
// ============================================================

interface KanbanCardProps {

    // Projeto representado pelo card.
    project: DevelopmentProject;

    // Estágio em que o projeto se encontra.
    stage: DevelopmentStage;


    // ========================================================
    // ESTADO DO DRAG-AND-DROP
    // ========================================================

    // Projeto atualmente sendo persistido em outro estágio.
    movingProjectId: number | null;

    // Projeto atualmente sendo arrastado.
    draggedProjectId: number | null;


    // ========================================================
    // PERMISSÕES / ESTADO DE PUBLICAÇÃO
    // ========================================================

    canMoveDevelopmentStage: boolean;

    canPublishDevelopment: boolean;

    // null:
    //     nenhuma publicação em andamento.
    publishingProjectId: number | null;


    // ========================================================
    // DRAG-AND-DROP
    // ========================================================

    onDragStart: (
        event: DragEvent<HTMLElement>,
        project: DevelopmentProject,
        stage: DevelopmentStage
    ) => void;

    onDragEnd:
        () => void;


    // ========================================================
    // AÇÕES
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

function KanbanCard({
    project,
    stage,

    movingProjectId,
    draggedProjectId,

    canMoveDevelopmentStage,
    canPublishDevelopment,

    publishingProjectId,

    onDragStart,
    onDragEnd,

    onOpenDetails,
    onOpenStudio,
    onPublish,
}: KanbanCardProps) {

    // ========================================================
    // ESTADOS VISUAIS DO CARD
    // ========================================================

    const moving =
        movingProjectId ===
        project.id;


    const dragging =
        draggedProjectId ===
        project.id;


    // Projetos da coluna PUBLISHED são somente leitura e
    // não participam do drag-and-drop.
    const publishedStage =
        stage.code ===
        "PUBLISHED";


    const draggable =
        canMoveDevelopmentStage &&
        !publishedStage &&
        movingProjectId === null;


    // ========================================================
    // INTERFACE
    // ========================================================

    return (

        <article
            draggable={
                draggable
            }

            onDragStart={(
                event
            ) => {
                onDragStart(
                    event,
                    project,
                    stage
                );
            }}

            onDragEnd={
                onDragEnd
            }

            style={{
                padding: 12,

                border:
                    "1px solid var(--border-color, #dfe3ea)",

                borderRadius:
                    8,

                background:
                    "var(--surface-color, #ffffff)",

                boxShadow:
                    dragging
                        ? "0 8px 20px rgba(15, 23, 42, 0.12)"
                        : "0 1px 2px rgba(15, 23, 42, 0.05)",

                opacity:
                    moving
                        ? 0.55
                        : (
                            dragging
                                ? 0.72
                                : 1
                        ),

                cursor:
                    draggable
                        ? "grab"
                        : "default",

                boxSizing:
                    "border-box",
            }}
        >

            {/* =============================================
                TÍTULO
            ============================================= */}

            <div
                style={{
                    display: "flex",

                    alignItems:
                        "flex-start",

                    justifyContent:
                        "space-between",

                    gap: 8,
                }}
            >

                <h3
                    style={{
                        margin: 0,

                        minWidth: 0,

                        fontSize: 13,

                        lineHeight:
                            1.35,

                        overflowWrap:
                            "anywhere",
                    }}
                >
                    {project.name}
                </h3>


                <span
                    style={{
                        flexShrink: 0,

                        fontSize: 10,

                        opacity: 0.5,
                    }}
                >
                    #{project.id}
                </span>

            </div>


            {/* =============================================
                CHECKOUT ATUAL
            ============================================= */}

            {project.checkout && (

                <div
                    style={{
                        display:
                            "flex",

                        alignItems:
                            "center",

                        gap: 7,

                        marginTop:
                            9,

                        padding:
                            "7px 9px",

                        border:
                            "1px solid rgba(217, 119, 6, 0.22)",

                        borderRadius:
                            7,

                        background:
                            "rgba(217, 119, 6, 0.07)",

                        fontSize:
                            10,

                        lineHeight:
                            1.35,
                    }}

                    title={
                        project.checkout.checked_out_at
                            ? `Checkout realizado em ${
                                parseApiDateTime(
                                    project.checkout.checked_out_at
                                )?.toLocaleString(
                                    "pt-BR"
                                ) || "Data não disponível"
                            }`
                            : undefined
                    }
                >

                    {/* Cadeado simples para indicar edição exclusiva. */}
                    <span
                        aria-hidden="true"

                        style={{
                            flexShrink: 0,
                        }}
                    >
                        🔒
                    </span>


                    <div
                        style={{
                            minWidth: 0,
                        }}
                    >

                        <div
                            style={{
                                fontWeight:
                                    750,

                                overflow:
                                    "hidden",

                                textOverflow:
                                    "ellipsis",

                                whiteSpace:
                                    "nowrap",
                            }}
                        >
                            Em edição por{" "}
                            {project.checkout.user_name ||
                                `Usuário #${project.checkout.user_id}`}
                        </div>


                        {project.checkout.checked_out_at && (

                            <div
                                style={{
                                    marginTop:
                                        1,

                                    opacity:
                                        0.62,
                                }}
                            >
                                desde{" "}
                                {parseApiDateTime(
                                    project.checkout.checked_out_at
                                )?.toLocaleString(
                                    "pt-BR",
                                    {
                                        day:
                                            "2-digit",

                                        month:
                                            "2-digit",

                                        hour:
                                            "2-digit",

                                        minute:
                                            "2-digit",
                                    }
                                ) || "Data não disponível"}
                            </div>
                        )}

                    </div>

                </div>
            )}


            {/* =============================================
                RESUMO DO PLANEJAMENTO
            ============================================= */}

            {(
                project.functional_responsible_name ||
                project.technical_responsible_name ||
                project.start_date ||
                project.due_date ||
                project.effort_hours != null ||
                (project.comments_count || 0) > 0
            ) && (

                <div
                    style={{
                        marginTop:
                            9,

                        paddingTop:
                            9,

                        borderTop:
                            "1px solid var(--border-color, #e5e7eb)",

                        display:
                            "grid",

                        gap:
                            5,

                        fontSize:
                            10,

                        lineHeight:
                            1.35,
                    }}
                >

                    {/* =====================================
                        RESPONSÁVEIS
                    ===================================== */}

                    {(
                        project.functional_responsible_name ||
                        project.technical_responsible_name
                    ) && (

                        <div
                            style={{
                                display:
                                    "grid",

                                gridTemplateColumns:
                                    "1fr 1fr",

                                gap:
                                    8,
                            }}
                        >

                            <div
                                style={{
                                    minWidth:
                                        0,
                                }}
                            >

                                <span
                                    style={{
                                        opacity:
                                            0.52,

                                        fontWeight:
                                            700,
                                    }}
                                >
                                    FUNC.
                                </span>{" "}

                                <strong>
                                    {project.functional_responsible_name ||
                                        "—"}
                                </strong>

                            </div>


                            <div
                                style={{
                                    minWidth:
                                        0,
                                }}
                            >

                                <span
                                    style={{
                                        opacity:
                                            0.52,

                                        fontWeight:
                                            700,
                                    }}
                                >
                                    TÉC.
                                </span>{" "}

                                <strong>
                                    {project.technical_responsible_name ||
                                        "—"}
                                </strong>

                            </div>

                        </div>
                    )}


                    {/* =====================================
                        PRAZO / ESFORÇO / COMENTÁRIOS
                    ===================================== */}

                    <div
                        style={{
                            display:
                                "flex",

                            flexWrap:
                                "wrap",

                            alignItems:
                                "center",

                            gap:
                                "4px 9px",

                            opacity:
                                0.72,
                        }}
                    >

                        {(
                            project.start_date ||
                            project.due_date
                        ) && (

                            <span>
                                {formatCardDate(
                                    project.start_date
                                )}

                                {" → "}

                                {formatCardDate(
                                    project.due_date
                                )}
                            </span>
                        )}


                        {project.effort_hours != null && (

                            <span>
                                ⏱{" "}
                                {project.effort_hours}h
                            </span>
                        )}


                        <span>
                            💬{" "}
                            {project.comments_count || 0}
                        </span>

                    </div>

                </div>
            )}


            {/* =============================================
                ESTÁGIO
            ============================================= */}

            <div
                style={{
                    display:
                        "flex",

                    alignItems:
                        "center",

                    justifyContent:
                        "space-between",

                    gap:
                        8,

                    marginTop:
                        10,
                }}
            >

                <span
                    style={{
                        minWidth:
                            0,

                        padding:
                            "3px 7px",

                        borderRadius:
                            999,

                        background:
                            "var(--surface-hover, rgba(100, 116, 139, 0.12))",

                        fontSize:
                            10,

                        fontWeight:
                            700,

                        whiteSpace:
                            "nowrap",

                        overflow:
                            "hidden",

                        textOverflow:
                            "ellipsis",
                    }}
                >
                    {moving
                        ? "Movendo..."
                        : stage.name}
                </span>


                {publishedStage && (

                    <span
                        style={{
                            flexShrink:
                                0,

                            fontSize:
                                10,

                            fontWeight:
                                800,

                            opacity:
                                0.65,
                        }}
                    >
                        BLOQUEADO
                    </span>
                )}

            </div>


            {/* =============================================
                AÇÕES
            ============================================= */}

            <div
                style={{
                    display:
                        "flex",

                    alignItems:
                        "center",

                    gap:
                        7,

                    marginTop:
                        11,
                }}
            >

                {/* Detalhes do planejamento e comentários. */}
                <button
                    type="button"

                    className="secondary-button"

                    disabled={
                        moving
                    }

                    onClick={() => {
                        onOpenDetails(
                            project
                        );
                    }}

                    style={{
                        flex: 1,

                        minWidth: 0,

                        minHeight:
                            32,

                        padding:
                            "6px 9px",

                        fontSize:
                            11,
                    }}
                >
                    Detalhes
                </button>


                {/* Abre o workspace no DUET Studio. */}
                <button
                    type="button"

                    className="secondary-button"

                    disabled={
                        moving
                    }

                    onClick={() => {
                        onOpenStudio(
                            project
                        );
                    }}

                    style={{
                        flex: 1,

                        minWidth: 0,

                        minHeight:
                            32,

                        padding:
                            "6px 9px",

                        fontSize:
                            11,
                    }}
                >
                    Abrir Studio
                </button>


                {/* Publicação somente a partir da etapa APPROVED. */}
                {stage.code ===
                    "APPROVED" &&
                    canPublishDevelopment && (

                    <button
                        type="button"

                        className="primary-button"

                        disabled={
                            moving ||
                            publishingProjectId !==
                                null
                        }

                        onClick={() => {
                            onPublish(
                                project
                            );
                        }}

                        style={{
                            flex: 1,

                            minWidth: 0,

                            minHeight:
                                32,

                            padding:
                                "6px 9px",

                            fontSize:
                                11,
                        }}
                    >
                        Publicar
                    </button>
                )}

            </div>

        </article>
    );
}


export default KanbanCard;
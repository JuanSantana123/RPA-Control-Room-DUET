// ============================================================
// CARD DETAILS PANEL
// ============================================================
//
// Responsabilidade:
//     Renderiza o painel lateral de detalhes de uma demanda do
//     Kanban da área de Desenvolvimento do DUET CORE.
//
// Este componente apresenta:
//     - responsável funcional;
//     - responsável técnico;
//     - data de início;
//     - previsão de conclusão;
//     - esforço estimado em horas;
//     - histórico de comentários;
//     - inclusão de novos comentários.
//
// Arquitetura:
//     Este componente é exclusivamente VISUAL.
//
// Ele recebe dados, estados e ações através de props.
//
// Este arquivo NÃO deve:
//     - realizar chamadas HTTP diretamente;
//     - conhecer endpoints do FastAPI;
//     - controlar o Kanban inteiro;
//     - implementar regras de Release;
//     - implementar regras de Checkout.
//
// As chamadas HTTP ficarão na camada services/hooks.
// A página Development.tsx continuará responsável apenas por
// orquestrar os módulos enquanto a refatoração estiver em curso.
//
// Integração:
//     Development.tsx
//         ↓
//     CardDetailsPanel.tsx
//         ↓
//     callbacks recebidos por props
//
// Objetivo:
//     Isolar uma das maiores áreas visuais do Development.tsx,
//     reduzindo acoplamento e facilitando evolução futura.
// ============================================================

import {
    createPortal,
} from "react-dom";


import type {
    CardComment,
    CardUser,
    DevelopmentProject,
} from "../../../types/development";


import {
    parseApiDateTime,
} from "../../../utils/dateTime";


// ============================================================
// PROPS
// ============================================================

interface CardDetailsPanelProps {

    // Projeto atualmente aberto.
    project: DevelopmentProject | null;


    // Usuários disponíveis para responsabilidade.
    users: CardUser[];


    // Comentários já carregados.
    comments: CardComment[];


    // ========================================================
    // CAMPOS DO PLANEJAMENTO
    // ========================================================

    functionalResponsibleId: string;

    technicalResponsibleId: string;

    startDate: string;

    dueDate: string;

    effortHours: string;


    // ========================================================
    // NOVO COMENTÁRIO
    // ========================================================

    newComment: string;


    // ========================================================
    // ESTADOS OPERACIONAIS
    // ========================================================

    loading: boolean;

    saving: boolean;

    addingComment: boolean;


    // Mensagem de erro específica do painel.
    error: string;


    // Define se o usuário possui Development:edit.
    canEdit: boolean;


    // ========================================================
    // ALTERAÇÃO DOS CAMPOS
    // ========================================================

    onFunctionalResponsibleChange:
        (value: string) => void;

    onTechnicalResponsibleChange:
        (value: string) => void;

    onStartDateChange:
        (value: string) => void;

    onDueDateChange:
        (value: string) => void;

    onEffortHoursChange:
        (value: string) => void;

    onNewCommentChange:
        (value: string) => void;


    // ========================================================
    // AÇÕES
    // ========================================================

    onClose:
        () => void;

    onSave:
        () => void | Promise<void>;

    onAddComment:
        () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function CardDetailsPanel({
    project,
    users,
    comments,

    functionalResponsibleId,
    technicalResponsibleId,

    startDate,
    dueDate,
    effortHours,

    newComment,

    loading,
    saving,
    addingComment,

    error,
    canEdit,

    onFunctionalResponsibleChange,
    onTechnicalResponsibleChange,

    onStartDateChange,
    onDueDateChange,
    onEffortHoursChange,

    onNewCommentChange,

    onClose,
    onSave,
    onAddComment,
}: CardDetailsPanelProps) {

    // Sem projeto selecionado não existe painel para renderizar.
    if (!project) {
        return null;
    }


    // O painel continua sendo renderizado em document.body
    // para não sofrer cortes por overflow ou z-index da página.
    return createPortal(

        <div
            role="presentation"

            onMouseDown={() => {
                onClose();
            }}

            style={{
                position: "fixed",
                inset: 0,
                zIndex: 10000,

                display: "flex",
                justifyContent: "flex-end",

                background:
                    "rgba(15, 23, 42, 0.42)",
            }}
        >

            <aside
                role="dialog"

                aria-modal="true"

                aria-labelledby="card-details-title"

                onMouseDown={(event) => {
                    event.stopPropagation();
                }}

                style={{
                    width:
                        "min(680px, 100%)",

                    height:
                        "100%",

                    display:
                        "flex",

                    flexDirection:
                        "column",

                    background:
                        "var(--surface-color, #ffffff)",

                    borderLeft:
                        "1px solid var(--border-color, #dfe3ea)",

                    boxShadow:
                        "-20px 0 60px rgba(15, 23, 42, 0.18)",

                    overflow:
                        "hidden",
                }}
            >

                {/* =============================================
                    CABEÇALHO
                ============================================= */}

                <div
                    style={{
                        padding:
                            "20px 22px 17px",

                        borderBottom:
                            "1px solid var(--border-color, #e5e7eb)",

                        display:
                            "flex",

                        alignItems:
                            "flex-start",

                        justifyContent:
                            "space-between",

                        gap: 18,
                    }}
                >

                    <div
                        style={{
                            minWidth: 0,
                        }}
                    >

                        <div
                            style={{
                                marginBottom: 5,

                                fontSize: 10,

                                fontWeight: 800,

                                letterSpacing:
                                    "0.09em",

                                opacity: 0.5,
                            }}
                        >
                            DETALHES DA DEMANDA
                        </div>


                        <h2
                            id="card-details-title"

                            style={{
                                margin: 0,

                                fontSize: 20,

                                lineHeight: 1.25,

                                overflowWrap:
                                    "anywhere",
                            }}
                        >
                            {project.name}
                        </h2>


                        <div
                            style={{
                                marginTop: 5,

                                fontSize: 11,

                                opacity: 0.55,
                            }}
                        >
                            Projeto #{project.id}
                        </div>

                    </div>


                    <button
                        type="button"

                        className="secondary-button"

                        disabled={
                            saving ||
                            addingComment
                        }

                        onClick={
                            onClose
                        }

                        style={{
                            flexShrink: 0,

                            minWidth: 74,
                        }}
                    >
                        Fechar
                    </button>

                </div>


                {/* =============================================
                    CONTEÚDO
                ============================================= */}

                <div
                    style={{
                        flex: 1,

                        overflowY:
                            "auto",

                        padding: 22,
                    }}
                >

                    {/* =========================================
                        PLANEJAMENTO
                    ========================================= */}

                    <section>

                        <div
                            style={{
                                marginBottom: 14,
                            }}
                        >

                            <div
                                style={{
                                    fontSize: 14,

                                    fontWeight: 800,
                                }}
                            >
                                Planejamento
                            </div>


                            <div
                                style={{
                                    marginTop: 3,

                                    fontSize: 11,

                                    opacity: 0.62,
                                }}
                            >
                                Responsáveis, prazo e esforço individual deste card.
                            </div>

                        </div>


                        <div
                            style={{
                                display: "grid",

                                gridTemplateColumns:
                                    "repeat(auto-fit, minmax(220px, 1fr))",

                                gap: 14,
                            }}
                        >

                            {/* =================================
                                RESPONSÁVEL FUNCIONAL
                            ================================= */}

                            <div className="form-field">

                                <label>
                                    Responsável funcional
                                </label>


                                <select
                                    value={
                                        functionalResponsibleId
                                    }

                                    disabled={
                                        !canEdit ||
                                        loading ||
                                        saving
                                    }

                                    onChange={(event) => {
                                        onFunctionalResponsibleChange(
                                            event.target.value
                                        );
                                    }}
                                >

                                    <option value="">
                                        Não definido
                                    </option>


                                    {users.map(
                                        (user) => (

                                            <option
                                                key={
                                                    user.id
                                                }

                                                value={
                                                    String(
                                                        user.id
                                                    )
                                                }
                                            >
                                                {user.name}
                                            </option>
                                        )
                                    )}

                                </select>

                            </div>


                            {/* =================================
                                RESPONSÁVEL TÉCNICO
                            ================================= */}

                            <div className="form-field">

                                <label>
                                    Responsável técnico
                                </label>


                                <select
                                    value={
                                        technicalResponsibleId
                                    }

                                    disabled={
                                        !canEdit ||
                                        loading ||
                                        saving
                                    }

                                    onChange={(event) => {
                                        onTechnicalResponsibleChange(
                                            event.target.value
                                        );
                                    }}
                                >

                                    <option value="">
                                        Não definido
                                    </option>


                                    {users.map(
                                        (user) => (

                                            <option
                                                key={
                                                    user.id
                                                }

                                                value={
                                                    String(
                                                        user.id
                                                    )
                                                }
                                            >
                                                {user.name}
                                            </option>
                                        )
                                    )}

                                </select>

                            </div>


                            {/* =================================
                                DATA DE INÍCIO
                            ================================= */}

                            <div className="form-field">

                                <label>
                                    Data de início
                                </label>


                                <input
                                    type="date"

                                    value={
                                        startDate
                                    }

                                    disabled={
                                        !canEdit ||
                                        saving
                                    }

                                    onChange={(event) => {
                                        onStartDateChange(
                                            event.target.value
                                        );
                                    }}
                                />

                            </div>


                            {/* =================================
                                PREVISÃO
                            ================================= */}

                            <div className="form-field">

                                <label>
                                    Previsão de conclusão
                                </label>


                                <input
                                    type="date"

                                    value={
                                        dueDate
                                    }

                                    disabled={
                                        !canEdit ||
                                        saving
                                    }

                                    onChange={(event) => {
                                        onDueDateChange(
                                            event.target.value
                                        );
                                    }}
                                />

                            </div>


                            {/* =================================
                                ESFORÇO
                            ================================= */}

                            <div className="form-field">

                                <label>
                                    Horas de esforço
                                </label>


                                <input
                                    type="number"

                                    min="0"

                                    step="0.25"

                                    placeholder="Ex.: 16"

                                    value={
                                        effortHours
                                    }

                                    disabled={
                                        !canEdit ||
                                        saving
                                    }

                                    onChange={(event) => {
                                        onEffortHoursChange(
                                            event.target.value
                                        );
                                    }}
                                />

                            </div>

                        </div>


                        {/* =====================================
                            ERRO DO PAINEL
                        ===================================== */}

                        {error && (

                            <div
                                className="alert alert-error"

                                style={{
                                    marginTop: 14,

                                    marginBottom: 0,
                                }}
                            >
                                {error}
                            </div>
                        )}


                        {/* =====================================
                            SALVAR
                        ===================================== */}

                        <div
                            style={{
                                display: "flex",

                                justifyContent:
                                    "flex-end",

                                marginTop: 16,
                            }}
                        >

                            <button
                                type="button"

                                className="primary-button"

                                disabled={
                                    !canEdit ||
                                    loading ||
                                    saving
                                }

                                onClick={
                                    onSave
                                }
                            >
                                {saving
                                    ? "Salvando..."
                                    : "Salvar planejamento"}
                            </button>

                        </div>

                    </section>


                    {/* =========================================
                        COMENTÁRIOS
                    ========================================= */}

                    <section
                        style={{
                            marginTop: 28,

                            paddingTop: 22,

                            borderTop:
                                "1px solid var(--border-color, #e5e7eb)",
                        }}
                    >

                        <div
                            style={{
                                display:
                                    "flex",

                                alignItems:
                                    "center",

                                justifyContent:
                                    "space-between",

                                gap: 12,

                                marginBottom: 14,
                            }}
                        >

                            <div>

                                <div
                                    style={{
                                        fontSize: 14,

                                        fontWeight: 800,
                                    }}
                                >
                                    Comentários
                                </div>


                                <div
                                    style={{
                                        marginTop: 3,

                                        fontSize: 11,

                                        opacity: 0.62,
                                    }}
                                >
                                    Histórico livre da demanda.
                                </div>

                            </div>


                            <span
                                style={{
                                    minWidth: 28,

                                    padding:
                                        "4px 8px",

                                    borderRadius:
                                        999,

                                    background:
                                        "var(--surface-hover, rgba(100, 116, 139, 0.10))",

                                    fontSize: 11,

                                    fontWeight: 800,

                                    textAlign:
                                        "center",
                                }}
                            >
                                {comments.length}
                            </span>

                        </div>


                        {/* =====================================
                            LISTA DE COMENTÁRIOS
                        ===================================== */}

                        {loading ? (

                            <div
                                style={{
                                    padding:
                                        "18px 0",

                                    fontSize: 12,

                                    opacity: 0.6,
                                }}
                            >
                                Carregando comentários...
                            </div>

                        ) : comments.length === 0 ? (

                            <div
                                style={{
                                    padding: 16,

                                    border:
                                        "1px dashed var(--border-color, #dfe3ea)",

                                    borderRadius:
                                        8,

                                    fontSize: 12,

                                    opacity: 0.6,

                                    textAlign:
                                        "center",
                                }}
                            >
                                Nenhum comentário neste card.
                            </div>

                        ) : (

                            <div
                                style={{
                                    display:
                                        "grid",

                                    gap: 10,
                                }}
                            >

                                {comments.map(
                                    (comment) => (

                                        <article
                                            key={
                                                comment.id
                                            }

                                            style={{
                                                padding:
                                                    "12px 14px",

                                                border:
                                                    "1px solid var(--border-color, #e5e7eb)",

                                                borderRadius:
                                                    9,

                                                background:
                                                    "var(--surface-hover, rgba(100, 116, 139, 0.045))",
                                            }}
                                        >

                                            <div
                                                style={{
                                                    display:
                                                        "flex",

                                                    alignItems:
                                                        "center",

                                                    justifyContent:
                                                        "space-between",

                                                    gap: 12,

                                                    marginBottom:
                                                        7,
                                                }}
                                            >

                                                <strong
                                                    style={{
                                                        fontSize:
                                                            11,
                                                    }}
                                                >
                                                    {comment.user_name ||
                                                        `Usuário #${comment.user_id}`}
                                                </strong>


                                                <span
                                                    style={{
                                                        fontSize:
                                                            10,

                                                        opacity:
                                                            0.5,

                                                        whiteSpace:
                                                            "nowrap",
                                                    }}
                                                >
                                                    {comment.created_at
                                                        ? (
                                                            parseApiDateTime(
                                                                comment.created_at
                                                            )?.toLocaleString(
                                                                "pt-BR"
                                                            ) || ""
                                                        )
                                                        : ""}
                                                </span>

                                            </div>


                                            <div
                                                style={{
                                                    fontSize:
                                                        12,

                                                    lineHeight:
                                                        1.55,

                                                    whiteSpace:
                                                        "pre-wrap",

                                                    overflowWrap:
                                                        "anywhere",
                                                }}
                                            >
                                                {comment.content}
                                            </div>

                                        </article>
                                    )
                                )}

                            </div>
                        )}


                        {/* =====================================
                            NOVO COMENTÁRIO
                        ===================================== */}

                        <div
                            style={{
                                marginTop: 14,
                            }}
                        >

                            <textarea
                                rows={4}

                                placeholder="Escreva um comentário..."

                                value={
                                    newComment
                                }

                                disabled={
                                    !canEdit ||
                                    addingComment
                                }

                                onChange={(event) => {
                                    onNewCommentChange(
                                        event.target.value
                                    );
                                }}

                                style={{
                                    width:
                                        "100%",

                                    resize:
                                        "vertical",

                                    boxSizing:
                                        "border-box",
                                }}
                            />


                            <div
                                style={{
                                    display:
                                        "flex",

                                    justifyContent:
                                        "flex-end",

                                    marginTop: 8,
                                }}
                            >

                                <button
                                    type="button"

                                    className="secondary-button"

                                    disabled={
                                        !canEdit ||
                                        !newComment.trim() ||
                                        addingComment
                                    }

                                    onClick={
                                        onAddComment
                                    }
                                >
                                    {addingComment
                                        ? "Adicionando..."
                                        : "Adicionar comentário"}
                                </button>

                            </div>

                        </div>

                    </section>

                </div>

            </aside>

        </div>,

        document.body
    );
}


export default CardDetailsPanel;
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


import PremiumSelect from "../../ui/PremiumSelect";
import { Save, X } from "lucide-react";
import { Button } from "../../ui/Button";
import { useDialogFocus } from "../../../hooks/ui/useDialogFocus";
import CardCommentsSection from "./CardCommentsSection";


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
    const dialogRef = useDialogFocus<HTMLElement>({
        open: Boolean(project),
        onClose,
        closeOnEscape: !saving && !addingComment,
    });

    // Sem projeto selecionado não existe painel para renderizar.
    if (!project) {
        return null;
    }


    // O painel continua sendo renderizado em document.body
    // para não sofrer cortes por overflow ou z-index da página.
    return createPortal(

        <div
            role="presentation"
            className="card-details-backdrop"

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
                    "var(--color-overlay)",
            }}
        >

            <aside
                ref={dialogRef}
                role="dialog"
                className="card-details-drawer"

                aria-modal="true"

                aria-labelledby="card-details-title"
                tabIndex={-1}

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
                        "var(--color-surface-raised)",

                    borderLeft:
                        "1px solid var(--color-border)",

                    boxShadow:
                        "var(--shadow-lg)",

                    overflow:
                        "hidden",
                }}
            >

                {/* =============================================
                    CABEÇALHO
                ============================================= */}

                <div
                    className="card-details-header"
                    style={{
                        padding:
                            "20px 22px 17px",

                        borderBottom:
                            "1px solid var(--color-border)",

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


                    <Button
                        variant="secondary"

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
                        <X size={15} strokeWidth={1.8} aria-hidden="true" />
                        Fechar
                    </Button>

                </div>


                {/* =============================================
                    CONTEÚDO
                ============================================= */}

                <div
                    className="card-details-body"
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

                    <section className="card-details-section">

                        <div
                            className="card-details-form-grid"
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

                                <label htmlFor="card-functional-responsible">
                                    Responsável funcional
                                </label>


                                <PremiumSelect
                                    id="card-functional-responsible"
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

                                </PremiumSelect>

                            </div>


                            {/* =================================
                                RESPONSÁVEL TÉCNICO
                            ================================= */}

                            <div className="form-field">

                                <label htmlFor="card-technical-responsible">
                                    Responsável técnico
                                </label>


                                <PremiumSelect
                                    id="card-technical-responsible"
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

                                </PremiumSelect>

                            </div>


                            {/* =================================
                                DATA DE INÍCIO
                            ================================= */}

                            <div className="form-field">

                                <label htmlFor="card-start-date">
                                    Data de início
                                </label>


                                <input
                                    id="card-start-date"
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

                                <label htmlFor="card-due-date">
                                    Previsão de conclusão
                                </label>


                                <input
                                    id="card-due-date"
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

                                <label htmlFor="card-effort-hours">
                                    Horas de esforço
                                </label>


                                <input
                                    id="card-effort-hours"
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

                            <Button
                                busy={saving}
                                loadingLabel="Salvando planejamento"

                                disabled={
                                    !canEdit ||
                                    loading
                                }

                                onClick={
                                    onSave
                                }
                            >
                                <Save size={15} strokeWidth={1.8} aria-hidden="true" />
                                {saving
                                    ? "Salvando..."
                                    : "Salvar planejamento"}
                            </Button>

                        </div>

                    </section>


                    <CardCommentsSection
                        comments={comments}
                        loading={loading}
                        canEdit={canEdit}
                        addingComment={addingComment}
                        newComment={newComment}
                        onNewCommentChange={onNewCommentChange}
                        onAddComment={onAddComment}
                    />

                </div>

            </aside>

        </div>,

        document.body
    );
}


export default CardDetailsPanel;

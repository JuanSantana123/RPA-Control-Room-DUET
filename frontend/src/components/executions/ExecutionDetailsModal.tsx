// ============================================================
// DUET CORE - EXECUTIONS - DETAILS MODAL
// ============================================================
//
// Modal visual responsável por apresentar os detalhes
// completos de uma execução.
//
// Responsabilidade:
// - apresentar informações do Robot;
// - apresentar pasta e usuário;
// - apresentar Agent e Agent ID;
// - apresentar status, PID e datas;
// - apresentar duração;
// - apresentar arquivo executado;
// - apresentar mensagem de erro;
// - permitir o fechamento do modal.
//
// Origem dos dados:
// - recebe a execução selecionada através de props.
//
// Dependências:
// - executionFormatters para datas, duração e status;
// - lucide-react para o ícone de fechamento.
//
// Este componente NÃO:
// - consulta API;
// - altera uma execução;
// - controla polling;
// - executa Stop ou Cancel;
// - mantém a seleção da execução.
//
// A seleção continua pertencendo à página Executions.tsx.
// ============================================================

import {
    X,
} from "lucide-react";
import { useEffect, useRef, type KeyboardEvent as ReactKeyboardEvent } from "react";
import { IconButton } from "../ui/Button";

import type {
    Execution,
} from "../../types/executions";

import {
    calcularDuracao,
    formatarData,
    formatarStatus,
} from "../../utils/executionFormatters";


// ============================================================
// PROPS
// ============================================================

interface ExecutionDetailsModalProps {

    // Execução atualmente selecionada.
    execution: Execution;

    // Solicita o fechamento do modal.
    onClose: () => void;
}


// ============================================================
// DETAIL
// ============================================================
//
// Pequeno componente visual utilizado exclusivamente dentro
// do modal para os campos apresentados em formato de card.
// ============================================================

interface DetailProps {
    label: string;
    value: string;
}


function Detail({
    label,
    value,
}: DetailProps) {

    return (
        <div className="execution-detail-card">

            <span>
                {label}
            </span>

            <strong>
                {value || "-"}
            </strong>

        </div>
    );
}


// ============================================================
// COMPONENTE PRINCIPAL
// ============================================================

function ExecutionDetailsModal({
    execution,
    onClose,
}: ExecutionDetailsModalProps) {

    const dialogRef = useRef<HTMLDivElement>(null);
    const closeButtonRef = useRef<HTMLButtonElement>(null);

    useEffect(() => {
        const previouslyFocused = document.activeElement instanceof HTMLElement
            ? document.activeElement
            : null;

        closeButtonRef.current?.focus();

        return () => {
            previouslyFocused?.focus();
        };
    }, []);

    const handleDialogKeyDown = (event: ReactKeyboardEvent<HTMLDivElement>) => {
        if (event.key === "Escape") {
            event.preventDefault();
            onClose();
            return;
        }

        if (event.key !== "Tab") return;

        const focusable = dialogRef.current?.querySelectorAll<HTMLElement>(
            'button:not(:disabled), [href], input:not(:disabled), select:not(:disabled), textarea:not(:disabled), [tabindex]:not([tabindex="-1"])'
        );

        if (!focusable?.length) {
            event.preventDefault();
            dialogRef.current?.focus();
            return;
        }

        const first = focusable[0];
        const last = focusable[focusable.length - 1];
        if (!first || !last) return;

        if (event.shiftKey && document.activeElement === first) {
            event.preventDefault();
            last.focus();
        } else if (!event.shiftKey && document.activeElement === last) {
            event.preventDefault();
            first.focus();
        }
    };

    return (
        <div
            className="execution-modal-overlay"
            role="presentation"
            onClick={onClose}
        >

            <div
                ref={dialogRef}
                className="execution-modal"
                role="dialog"
                aria-modal="true"
                aria-labelledby="execution-details-title"
                tabIndex={-1}
                onKeyDown={handleDialogKeyDown}
                onClick={(event) =>
                    event.stopPropagation()
                }
            >

                {/* =============================================
                    HEADER
                ============================================= */}

                <div className="execution-modal-header">

                    <div>

                        <span className="page-eyebrow">
                            DETALHES DA EXECUÇÃO
                        </span>

                        <h2 id="execution-details-title">
                            Execução #{execution.id}
                        </h2>

                    </div>


                    <IconButton
                        ref={closeButtonRef}
                        label="Fechar detalhes da execução"
                        icon={<X size={18} aria-hidden="true" />}
                        onClick={onClose}
                    />

                </div>


                {/* =============================================
                    BODY
                ============================================= */}

                <div className="execution-modal-body">

                    {/* =========================================
                        DADOS PRINCIPAIS
                    ========================================= */}

                    <div className="execution-detail-grid">

                        <Detail
                            label="Robô"
                            value={
                                execution.robot_name
                            }
                        />


                        <Detail
                            label="Pasta"
                            value={
                                execution.folder_name ||
                                "Pasta raiz"
                            }
                        />


                        <Detail
                            label="Usuário"
                            value={
                                execution.user_name ||
                                execution.username ||
                                "Usuário desconhecido"
                            }
                        />


                        <Detail
                            label="Dispositivo"
                            value={
                                execution.agent_name
                            }
                        />


                        <Detail
                            label="Situação"
                            value={
                                formatarStatus(
                                    execution.status
                                )
                            }
                        />


                        <Detail
                            label="PID"
                            value={
                                String(
                                    execution.pid ?? "-"
                                )
                            }
                        />


                        <Detail
                            label="Início"
                            value={
                                formatarData(
                                    execution.started_at
                                )
                            }
                        />


                        <Detail
                            label="Fim"
                            value={
                                formatarData(
                                    execution.finished_at
                                )
                            }
                        />


                        <Detail
                            label="Duração"
                            value={
                                calcularDuracao(
                                    execution.started_at,
                                    execution.finished_at
                                )
                            }
                        />


                        <Detail
                            label="ID do robô"
                            value={
                                String(
                                    execution.robot_id
                                )
                            }
                        />

                    </div>


                    {/* =========================================
                        AGENT ID
                    ========================================= */}

                    <div className="execution-detail-section">

                        <span className="execution-detail-label">
                            ID do dispositivo
                        </span>

                        <strong className="execution-detail-value break-word">
                            {execution.agent_id}
                        </strong>

                    </div>


                    {/* =========================================
                        ARQUIVO
                    ========================================= */}

                    <div className="execution-detail-section">

                        <span className="execution-detail-label">
                            Arquivo
                        </span>

                        <strong className="execution-detail-value break-word">
                            {execution.filename}
                        </strong>

                    </div>


                    {/* =========================================
                        ERRO
                    ========================================= */}

                    <div className="execution-detail-section">

                        <span className="execution-detail-label">
                            Mensagem de erro
                        </span>

                        <div className="execution-error-box">
                            {execution.error_message ||
                                "Nenhum erro registrado."}
                        </div>

                    </div>

                </div>

            </div>

        </div>
    );
}


export default ExecutionDetailsModal;

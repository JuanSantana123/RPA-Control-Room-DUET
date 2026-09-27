// ============================================================
// DUET CORE - SCHEDULES - TABLE ROW
// ============================================================
//
// Representa visualmente uma única linha da tabela de
// Agendamentos.
//
// Responsabilidade:
// - apresentar os dados de um Schedule;
// - apresentar informação de intervalo;
// - apresentar status ativo/inativo;
// - encaminhar ações de editar, ativar/desativar e excluir.
//
// Todas as operações são recebidas através de callbacks.
//
// Este componente NÃO:
// - chama a API;
// - altera diretamente o Schedule;
// - controla polling;
// - possui regras de criação/edição;
// - calcula a próxima execução.
// ============================================================

import type {
    Schedule,
} from "../../types/schedules";

import {
    formatarData,
    formatarTipo,
} from "../../utils/scheduleFormatters";
import { Pencil, Power, Trash2 } from "lucide-react";
import { Button } from "../ui/Button";


// ============================================================
// PROPS
// ============================================================

interface ScheduleRowProps {
    schedule: Schedule;
    canEdit: boolean;
    canDelete: boolean;

    onEdit: (
        id: number
    ) => void | Promise<void>;

    onToggleStatus: (
        id: number,
        ativo: boolean
    ) => void | Promise<void>;

    onDelete: (
        id: number
    ) => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function ScheduleRow({
    schedule,
    canEdit,
    canDelete,
    onEdit,
    onToggleStatus,
    onDelete,
}: ScheduleRowProps) {

    const graceSeconds = Number.isFinite(schedule.misfire_grace_seconds)
        ? schedule.misfire_grace_seconds
        : 300;
    const graceLabel = graceSeconds >= 3600
        ? `${graceSeconds / 3600} h`
        : `${Math.round(graceSeconds / 60)} min`;

    return (
        <tr>

            {/* ==================================================
                ROBÔ
                ================================================== */}

            <td>
                {schedule.robot_name}
            </td>


            {/* ==================================================
                AGENT
                ================================================== */}

            <td>

                <div>

                    <strong>
                        {schedule.agent_name}
                    </strong>

                    {schedule.agent_id && (

                        <div className="schedule-agent-id">
                            {schedule.agent_id}
                        </div>

                    )}

                </div>

            </td>


            {/* ==================================================
                TIPO
                ================================================== */}

            <td>
                {formatarTipo(
                    schedule.tipo
                )}
            </td>


            {/* ==================================================
                HORÁRIO
                ================================================== */}

            <td>

                {schedule.horario}

                {schedule.intervalo_ativo && (

                    <small className="schedule-interval-summary">
                        A cada{" "}
                        {schedule.intervalo_valor}{" "}

                        {schedule.intervalo_unidade ===
                        "minutes"
                            ? "minuto(s)"
                            : "hora(s)"
                        }

                        {" "}até{" "}

                        {schedule.horario_fim}

                    </small>

                )}

            </td>


            {/* ==================================================
                PRÓXIMA EXECUÇÃO
                ================================================== */}

            <td>

                {schedule.proxima_execucao
                    ? formatarData(
                        schedule.proxima_execucao
                    )
                    : "-"
                }

            </td>


            {/* ==================================================
                STATUS
                ================================================== */}

            <td>

                <div className="schedule-status-cell">
                    <span className={`schedule-status-badge ${schedule.ativo ? "active" : "inactive"}`}>
                        <i aria-hidden="true" />
                        {schedule.ativo ? "Ativo" : "Inativo"}
                    </span>
                    <small>
                        {schedule.misfire_policy === "skip"
                            ? `Ignora atraso > ${graceLabel}`
                            : `Recupera 1 atraso > ${graceLabel}`}
                    </small>
                    {schedule.ultima_ocorrencia_perdida && (
                        <strong>Ignorada em {formatarData(schedule.ultima_ocorrencia_perdida)}</strong>
                    )}
                </div>

            </td>


            {/* ==================================================
                AÇÕES
                ================================================== */}

            <td className="schedule-actions">

                {canEdit && <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                        onEdit(
                            schedule.id
                        );
                    }}
                >
                    <Pencil size={14} strokeWidth={1.9} aria-hidden="true" />
                    Editar
                </Button>}

                {canEdit && <Button
                    variant="secondary"
                    size="sm"
                    onClick={() => {
                        onToggleStatus(
                            schedule.id,
                            !schedule.ativo
                        );
                    }}
                >
                    <Power size={14} strokeWidth={1.9} aria-hidden="true" />
                    {schedule.ativo
                        ? "Desativar"
                        : "Ativar"
                    }
                </Button>}

                {canDelete && <Button
                    variant="danger"
                    size="sm"
                    onClick={() => {
                        onDelete(
                            schedule.id
                        );
                    }}
                >
                    <Trash2 size={14} strokeWidth={1.9} aria-hidden="true" />
                    Excluir
                </Button>}

                {!canEdit && !canDelete && (
                    <span className="table-readonly-label">Consulta</span>
                )}

            </td>

        </tr>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default ScheduleRow;

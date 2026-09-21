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


// ============================================================
// PROPS
// ============================================================

interface ScheduleRowProps {
    schedule: Schedule;

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
    onEdit,
    onToggleStatus,
    onDelete,
}: ScheduleRowProps) {

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

                        <div
                            style={{
                                fontSize: "11px",
                                color: "#94a3b8",
                                marginTop: "2px",
                            }}
                        >
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

                    <small
                        style={{
                            display: "block",
                        }}
                    >
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

                {schedule.ativo
                    ? "● Ativo"
                    : "● Inativo"
                }

            </td>


            {/* ==================================================
                AÇÕES
                ================================================== */}

            <td className="schedule-actions">

                <button
                    type="button"
                    className="table-action-button edit"
                    onClick={() => {
                        onEdit(
                            schedule.id
                        );
                    }}
                >
                    Editar
                </button>


                {" "}


                <button
                    type="button"
                    className="table-action-button toggle"
                    onClick={() => {
                        onToggleStatus(
                            schedule.id,
                            !schedule.ativo
                        );
                    }}
                >
                    {schedule.ativo
                        ? "Desativar"
                        : "Ativar"
                    }
                </button>


                {" "}


                <button
                    type="button"
                    className="table-action-button delete"
                    onClick={() => {
                        onDelete(
                            schedule.id
                        );
                    }}
                >
                    Excluir
                </button>

            </td>

        </tr>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default ScheduleRow;
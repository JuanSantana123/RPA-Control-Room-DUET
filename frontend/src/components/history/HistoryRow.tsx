// ============================================================
// DUET CORE - HISTORY - ROW
// ============================================================
//
// Linha visual de uma execução finalizada.
//
// Responsabilidade:
// - apresentar os dados de uma execução;
// - aplicar os formatadores de apresentação.
//
// Este componente NÃO:
// - busca execuções;
// - altera execuções;
// - controla polling;
// - executa chamadas HTTP.
// ============================================================

import type {
    HistoryExecution,
} from "../../types/history";

import {
    calculateHistoryDuration,
    formatHistoryDate,
    formatHistoryStatus,
} from "../../utils/historyFormatters";


// ============================================================
// PROPS
// ============================================================

interface HistoryRowProps {
    execution:
        HistoryExecution;
}


// ============================================================
// COMPONENTE
// ============================================================

function HistoryRow({
    execution,
}: HistoryRowProps) {

    return (
        <tr>

            {/* ID */}
            <td>
                {execution.id}
            </td>


            {/* ROBÔ */}
            <td>
                {execution.robot_name || "-"}
            </td>


            {/* PASTA */}
            <td>

                <div className="history-folder-cell">
                    {execution.folder_name ||
                        "Pasta raiz"}
                </div>

            </td>


            {/* USUÁRIO */}
            <td>

                <div className="history-user-cell">
                    {execution.user_name ||
                        execution.username ||
                        "Usuário desconhecido"}
                </div>

            </td>


            {/* AGENT */}
            <td>
                {execution.agent_name || "-"}
            </td>


            {/* INÍCIO */}
            <td>
                {formatHistoryDate(
                    execution.started_at
                )}
            </td>


            {/* FIM */}
            <td>
                {formatHistoryDate(
                    execution.finished_at
                )}
            </td>


            {/* DURAÇÃO */}
            <td>
                {calculateHistoryDuration(
                    execution.started_at,
                    execution.finished_at
                )}
            </td>


            {/* STATUS */}
            <td>
                {formatHistoryStatus(
                    execution.status
                )}
            </td>


            {/* ERRO */}
            <td>
                {execution.error_message || "-"}
            </td>

        </tr>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default HistoryRow;
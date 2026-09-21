// ============================================================
// DUET CORE - DASHBOARD - EXECUTION ROW
// ============================================================
//
// Linha individual da tabela de execuções em andamento.
//
// Responsabilidade:
// - apresentar ID;
// - apresentar robô;
// - apresentar Agent;
// - apresentar início;
// - apresentar status.
//
// Este componente NÃO:
// - busca execuções;
// - altera status;
// - controla atualização da lista.
//
// A formatação da data é delegada ao utilitário compartilhado
// do Dashboard.
// ============================================================

import type {
    DashboardExecution,
} from "../../types/dashboard";

import {
    formatarData,
} from "../../utils/dashboardFormatters";


// ============================================================
// PROPS
// ============================================================

interface DashboardExecutionRowProps {
    execution:
        DashboardExecution;
}


// ============================================================
// COMPONENTE
// ============================================================

function DashboardExecutionRow({
    execution,
}: DashboardExecutionRowProps) {

    return (
        <tr>

            <td>
                {execution.id}
            </td>

            <td>
                {execution.robot_name}
            </td>

            <td>

                <div className="agent-name">

                    <strong>
                        {execution.agent_name}
                    </strong>

                    <small>
                        {execution.agent_id}
                    </small>

                </div>

            </td>

            <td>
                {formatarData(
                    execution.started_at
                )}
            </td>

            <td>
                {execution.status}
            </td>

        </tr>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default DashboardExecutionRow;
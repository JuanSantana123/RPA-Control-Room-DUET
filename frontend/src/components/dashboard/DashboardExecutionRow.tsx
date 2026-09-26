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
import ExecutionStatusBadge from "../executions/ExecutionStatusBadge";


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

            <td data-label="ID">
                {execution.id}
            </td>

            <td data-label="Robô">
                {execution.robot_name}
            </td>

            <td data-label="Dispositivo">

                <div className="agent-name">

                    <strong>
                        {execution.agent_name}
                    </strong>

                    <small>
                        {execution.agent_id}
                    </small>

                </div>

            </td>

            <td data-label="Início">
                {formatarData(
                    execution.started_at
                )}
            </td>

            <td data-label="Situação">
                <ExecutionStatusBadge status={execution.status} />
            </td>

        </tr>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default DashboardExecutionRow;

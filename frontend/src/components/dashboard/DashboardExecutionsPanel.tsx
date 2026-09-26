// ============================================================
// DUET CORE - DASHBOARD - EXECUTIONS PANEL
// ============================================================
//
// Painel de execuções atualmente processadas pelos Agents.
//
// Responsabilidade:
// - apresentar quantidade de execuções ativas;
// - apresentar estado vazio;
// - apresentar tabela quando existirem execuções;
// - compor DashboardExecutionRow.
//
// Este componente NÃO:
// - executa GET /executions;
// - mantém estado da API;
// - realiza polling;
// - altera execuções.
// ============================================================

import {
    Activity,
} from "lucide-react";

import DashboardExecutionRow
    from "./DashboardExecutionRow";

import type {
    DashboardExecution,
} from "../../types/dashboard";
import EmptyState from "../ui/EmptyState";


// ============================================================
// PROPS
// ============================================================

interface DashboardExecutionsPanelProps {
    executions:
        DashboardExecution[];
}


// ============================================================
// COMPONENTE
// ============================================================

function DashboardExecutionsPanel({
    executions,
}: DashboardExecutionsPanelProps) {

    return (
        <section className="panel">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <div className="panel-header">

                <div>

                    <h2>
                        Execuções em andamento
                    </h2>

                    <p>
                        Execuções atualmente processadas pelos dispositivos
                    </p>

                </div>


                <div className="panel-header-meta">

                    <span className="panel-count">
                        {executions.length}
                    </span>

                    <span className="panel-count-label">
                        ativas
                    </span>

                </div>

            </div>


            {/* ==================================================
                CONTEÚDO
                ================================================== */}

            {executions.length === 0 ? (

                <EmptyState
                    icon={<Activity />}
                    title="Nenhuma execução em andamento"
                    description="O ambiente está livre. Novas execuções aparecerão aqui assim que forem iniciadas."
                />

            ) : (

                <div className="table-container">

                    <table>

                        <thead>

                            <tr>

                                <th>
                                    ID
                                </th>

                                <th>
                                    Robô
                                </th>

                                <th>
                                    Dispositivo
                                </th>

                                <th>
                                    Início
                                </th>

                                <th>
                                    Situação
                                </th>

                            </tr>

                        </thead>


                        <tbody>

                            {executions.map(
                                (execution) => (

                                    <DashboardExecutionRow
                                        key={
                                            execution.id
                                        }
                                        execution={
                                            execution
                                        }
                                    />

                                )
                            )}

                        </tbody>

                    </table>

                </div>

            )}

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default DashboardExecutionsPanel;

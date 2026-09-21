// ============================================================
// DUET CORE - DASHBOARD - PLATFORM SUMMARY
// ============================================================
//
// Resumo geral da plataforma apresentado na área inferior
// do Dashboard.
//
// Responsabilidade:
// - apresentar Agents cadastrados;
// - apresentar Agents disponíveis;
// - apresentar robôs disponíveis.
//
// Este componente é exclusivamente visual.
//
// Ele NÃO:
// - executa chamadas HTTP;
// - mantém estado;
// - altera ou deriva dados operacionais.
// ============================================================

import type {
    DashboardStats,
} from "../../types/dashboard";


// ============================================================
// PROPS
// ============================================================

interface DashboardPlatformSummaryProps {
    stats:
        DashboardStats | null;
}


// ============================================================
// COMPONENTE
// ============================================================

function DashboardPlatformSummary({
    stats,
}: DashboardPlatformSummaryProps) {

    return (
        <div className="dashboard-module">

            <div className="dashboard-module-header">

                <div>

                    <h2>
                        Resumo da plataforma
                    </h2>

                    <p>
                        Indicadores gerais do ambiente
                    </p>

                </div>

            </div>


            <div className="platform-summary">

                <div className="summary-item">

                    <span>
                        Agents cadastrados
                    </span>

                    <strong>
                        {stats?.total_agents ?? 0}
                    </strong>

                </div>


                <div className="summary-item">

                    <span>
                        Agents disponíveis
                    </span>

                    <strong>
                        {stats?.agents_online ?? 0}
                    </strong>

                </div>


                <div className="summary-item">

                    <span>
                        Robôs disponíveis
                    </span>

                    <strong>
                        {stats?.total_robots ?? 0}
                    </strong>

                </div>

            </div>

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default DashboardPlatformSummary;
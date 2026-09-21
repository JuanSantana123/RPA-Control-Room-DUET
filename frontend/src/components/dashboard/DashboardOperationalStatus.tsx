// ============================================================
// DUET CORE - DASHBOARD - OPERATIONAL STATUS
// ============================================================
//
// Módulo visual de status operacional da infraestrutura.
//
// Responsabilidade:
// - apresentar indicador "Operacional";
// - apresentar Agents conectados;
// - apresentar robôs cadastrados;
// - apresentar execuções ativas.
//
// IMPORTANTE:
// O texto "Operacional" já é fixo no Dashboard atual.
// Este componente preserva esse comportamento.
//
// Ele NÃO:
// - executa health check;
// - determina disponibilidade real da plataforma;
// - executa chamadas HTTP.
// ============================================================

import {
    Activity,
    Bot,
    Monitor,
} from "lucide-react";

import type {
    DashboardStats,
} from "../../types/dashboard";


// ============================================================
// PROPS
// ============================================================

interface DashboardOperationalStatusProps {
    stats:
        DashboardStats | null;

    activeExecutions:
        number;
}


// ============================================================
// COMPONENTE
// ============================================================

function DashboardOperationalStatus({
    stats,
    activeExecutions,
}: DashboardOperationalStatusProps) {

    return (
        <div className="dashboard-module">

            <div className="dashboard-module-header">

                <div>

                    <h2>
                        Status operacional
                    </h2>

                    <p>
                        Situação atual da infraestrutura de automação
                    </p>

                </div>


                <div className="module-status-indicator">

                    <span className="status-dot"></span>

                    Operacional

                </div>

            </div>


            <div className="operational-list">

                {/* ==================================================
                    AGENTS
                    ================================================== */}

                <div className="operational-item">

                    <div className="operational-item-label">

                        <Monitor
                            size={16}
                            strokeWidth={1.8}
                        />

                        <span>
                            Agents conectados
                        </span>

                    </div>

                    <strong>
                        {stats?.agents_online ?? 0}
                    </strong>

                </div>


                {/* ==================================================
                    ROBÔS
                    ================================================== */}

                <div className="operational-item">

                    <div className="operational-item-label">

                        <Bot
                            size={16}
                            strokeWidth={1.8}
                        />

                        <span>
                            Robôs cadastrados
                        </span>

                    </div>

                    <strong>
                        {stats?.total_robots ?? 0}
                    </strong>

                </div>


                {/* ==================================================
                    EXECUÇÕES
                    ================================================== */}

                <div className="operational-item">

                    <div className="operational-item-label">

                        <Activity
                            size={16}
                            strokeWidth={1.8}
                        />

                        <span>
                            Execuções ativas
                        </span>

                    </div>

                    <strong>
                        {activeExecutions}
                    </strong>

                </div>

            </div>

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default DashboardOperationalStatus;
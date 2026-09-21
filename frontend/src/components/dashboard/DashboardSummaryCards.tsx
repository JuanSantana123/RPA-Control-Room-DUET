// ============================================================
// DUET CORE - DASHBOARD - SUMMARY CARDS
// ============================================================
//
// Conjunto de indicadores principais apresentados no topo
// do Dashboard.
//
// Responsabilidade:
// - apresentar total de Agents;
// - apresentar Agents online;
// - apresentar total de robôs;
// - apresentar quantidade de execuções em andamento.
//
// Os dados são recebidos da página. Este componente NÃO:
// - executa chamadas HTTP;
// - mantém estado operacional;
// - calcula informações além das já fornecidas.
// ============================================================

import {
    Activity,
    Bot,
    Monitor,
    PlayCircle,
} from "lucide-react";

import type {
    DashboardStats,
} from "../../types/dashboard";


// ============================================================
// PROPS
// ============================================================

interface DashboardSummaryCardsProps {
    stats:
        DashboardStats | null;

    activeExecutions:
        number;
}


// ============================================================
// COMPONENTE
// ============================================================

function DashboardSummaryCards({
    stats,
    activeExecutions,
}: DashboardSummaryCardsProps) {

    return (
        <section className="cards">

            {/* ==================================================
                TOTAL DE AGENTS
                ================================================== */}

            <div className="card">

                <div className="card-top">

                    <span className="card-title">
                        Agents
                    </span>

                    <div className="card-icon">
                        <Monitor
                            size={21}
                            strokeWidth={1.8}
                        />
                    </div>

                </div>

                <div className="card-value">
                    {stats?.total_agents ?? 0}
                </div>

                <div className="card-info">
                    Agents cadastrados
                </div>

            </div>


            {/* ==================================================
                AGENTS ONLINE
                ================================================== */}

            <div className="card">

                <div className="card-top">

                    <span className="card-title">
                        Agents Online
                    </span>

                    <div className="card-icon card-icon-success">
                        <Activity
                            size={21}
                            strokeWidth={1.8}
                        />
                    </div>

                </div>

                <div className="card-value">
                    {stats?.agents_online ?? 0}
                </div>

                <div className="card-info">
                    Agents disponíveis
                </div>

            </div>


            {/* ==================================================
                TOTAL DE ROBÔS
                ================================================== */}

            <div className="card">

                <div className="card-top">

                    <span className="card-title">
                        Robôs
                    </span>

                    <div className="card-icon">
                        <Bot
                            size={21}
                            strokeWidth={1.8}
                        />
                    </div>

                </div>

                <div className="card-value">
                    {stats?.total_robots ?? 0}
                </div>

                <div className="card-info">
                    Robôs cadastrados
                </div>

            </div>


            {/* ==================================================
                EXECUÇÕES
                ================================================== */}

            <div className="card">

                <div className="card-top">

                    <span className="card-title">
                        Execuções
                    </span>

                    <div className="card-icon">
                        <PlayCircle
                            size={21}
                            strokeWidth={1.8}
                        />
                    </div>

                </div>

                <div className="card-value">
                    {activeExecutions}
                </div>

                <div className="card-info">
                    Execuções em andamento
                </div>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default DashboardSummaryCards;
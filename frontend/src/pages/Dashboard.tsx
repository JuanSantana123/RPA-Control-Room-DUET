// ============================================================
// DUET CORE - DASHBOARD PAGE
// ============================================================
//
// Página principal do Dashboard do Control Room.
//
// Responsabilidade:
// - coordenar o carregamento dos dados do Dashboard;
// - apresentar os estados globais de loading e erro;
// - compor os módulos visuais do Dashboard.
//
// Arquitetura:
//
// Dashboard
//   │
//   ├── useDashboardData
//   │     ├── GET /dashboard/stats
//   │     └── GET /executions
//   │
//   ├── DashboardSummaryCards
//   ├── DashboardExecutionsPanel
//   ├── DashboardOperationalStatus
//   └── DashboardPlatformSummary
//
// Esta página NÃO:
// - executa chamadas HTTP diretamente;
// - formata datas;
// - renderiza linhas da tabela diretamente;
// - mantém regras visuais dos cards;
// - realiza polling.
//
// O objetivo é manter Dashboard.tsx como camada fina de
// composição, preservando o comportamento existente.
// ============================================================

import DashboardSummaryCards
    from "../components/dashboard/DashboardSummaryCards";

import DashboardExecutionsPanel
    from "../components/dashboard/DashboardExecutionsPanel";

import DashboardOperationalStatus
    from "../components/dashboard/DashboardOperationalStatus";

import DashboardPlatformSummary
    from "../components/dashboard/DashboardPlatformSummary";

import {
    useDashboardData,
} from "../hooks/dashboard/useDashboardData";


// ============================================================
// DASHBOARD
// ============================================================

function Dashboard() {

    // ========================================================
    // DADOS
    // ========================================================
    //
    // Toda a comunicação com a API permanece encapsulada no
    // hook especializado do Dashboard.
    // ========================================================

    const {
        stats,
        executions,
        loading,
        error,
    } = useDashboardData();


    // ========================================================
    // ESTADO DE CARREGAMENTO
    // ========================================================
    //
    // Preserva exatamente o comportamento da página original:
    // enquanto as estatísticas estão sendo carregadas, nenhum
    // outro módulo do Dashboard é apresentado.
    // ========================================================

    if (loading) {

        return (
            <div className="empty-state">

                <div className="empty-icon">
                    ⏳
                </div>

                <h3>
                    Carregando Dashboard...
                </h3>

                <p>
                    Buscando informações do Control Room.
                </p>

            </div>
        );
    }


    // ========================================================
    // ESTADO DE ERRO
    // ========================================================
    //
    // A mensagem de erro global continua relacionada somente
    // ao carregamento das estatísticas do Dashboard.
    // ========================================================

    if (error) {

        return (
            <div className="empty-state">

                <div className="empty-icon">
                    ⚠️
                </div>

                <h3>
                    Erro ao carregar Dashboard
                </h3>

                <p>
                    {error}
                </p>

            </div>
        );
    }


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div>

            {/* ==================================================
                CARDS DE RESUMO
                ================================================== */}

            <DashboardSummaryCards
                stats={stats}
                activeExecutions={
                    executions.length
                }
            />


            {/* ==================================================
                EXECUÇÕES EM ANDAMENTO
                ================================================== */}

            <DashboardExecutionsPanel
                executions={
                    executions
                }
            />


            {/* ==================================================
                RESUMO OPERACIONAL
                ================================================== */}

            <section className="dashboard-lower-grid">

                <DashboardOperationalStatus
                    stats={stats}
                    activeExecutions={
                        executions.length
                    }
                />


                <DashboardPlatformSummary
                    stats={stats}
                />

            </section>

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default Dashboard;
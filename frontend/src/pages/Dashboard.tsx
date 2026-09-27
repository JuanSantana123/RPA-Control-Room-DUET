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

import DashboardCommandCenter
    from "../components/dashboard/DashboardCommandCenter";

import { DashboardSkeleton }
    from "../components/ui/Skeletons";
import FeedbackBanner from "../components/ui/FeedbackBanner";
import PageHeader from "../components/ui/PageHeader";

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
        refreshing,
        error,
        executionsError,
        recarregar,
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
        return <DashboardSkeleton />;
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
            <div className="page-container">
                <FeedbackBanner
                    tone="error"
                    title="Não foi possível carregar a visão geral"
                    message={error}
                    hint="Verifique a conexão com o Control Room e tente atualizar a página."
                    action={{
                        label: "Tentar novamente",
                        onClick: recarregar,
                        busy: refreshing,
                    }}
                />
            </div>
        );
    }


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="page-container dashboard-page">

            <PageHeader eyebrow="OPERAÇÃO" title="Visão geral" description="Acompanhe capacidade, automações e atividade do Control Room." />

            {executionsError && (
                <div className="dashboard-partial-warning">
                    <FeedbackBanner
                        tone="error"
                        title="Execuções temporariamente indisponíveis"
                        message={executionsError}
                        hint="Os demais indicadores continuam disponíveis."
                        action={{
                            label: "Atualizar",
                            onClick: recarregar,
                            busy: refreshing,
                        }}
                    />
                </div>
            )}

            <DashboardCommandCenter
                stats={stats}
                activeExecutions={executions.length}
            />

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

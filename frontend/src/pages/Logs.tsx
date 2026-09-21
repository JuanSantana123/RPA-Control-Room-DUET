// ============================================================
// DUET CORE - LOGS PAGE
// ============================================================
//
// Página principal de acompanhamento dos Logs do Control Room.
//
// Responsabilidade:
// - conectar useLogsData aos componentes visuais;
// - apresentar mensagens de erro;
// - compor cabeçalho e painel de eventos.
//
// Arquitetura:
//
// Logs
//   │
//   ├── useLogsData
//   │     ├── GET /logs
//   │     ├── loading / erro
//   │     ├── atualização manual
//   │     └── polling de 5 segundos
//   │
//   ├── LogsHeader
//   │
//   └── LogsPanel
//
// Esta página NÃO:
// - executa chamadas HTTP diretamente;
// - cria timers;
// - armazena logs diretamente;
// - classifica níveis de log;
// - renderiza individualmente os registros.
//
// A página funciona somente como camada de composição.
// ============================================================

import LogsHeader
    from "../components/logs/LogsHeader";

import LogsPanel
    from "../components/logs/LogsPanel";

import {
    useLogsData,
} from "../hooks/logs/useLogsData";


// ============================================================
// PÁGINA DE LOGS
// ============================================================

function Logs() {

    // ========================================================
    // DADOS
    // ========================================================

    const {
        logs,
        loading,
        error,
        carregarLogs,
    } = useLogsData();


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="logs-page">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <LogsHeader
                onRefresh={
                    carregarLogs
                }
            />


            {/* ==================================================
                ALERTA DE ERRO
                ================================================== */}

            {error && (

                <div className="logs-alert">

                    <span>
                        ⚠
                    </span>

                    <span>
                        {error}
                    </span>

                </div>

            )}


            {/* ==================================================
                PAINEL DE LOGS
                ================================================== */}

            <LogsPanel
                logs={
                    logs
                }
                loading={
                    loading
                }
                error={
                    error
                }
            />

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default Logs;
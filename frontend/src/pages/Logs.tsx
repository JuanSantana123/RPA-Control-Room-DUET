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
import { useMemo, useState } from "react";
import { TriangleAlert } from "lucide-react";
import LogsToolbar, { type LogLevelFilter } from "../components/logs/LogsToolbar";


// ============================================================
// PÁGINA DE LOGS
// ============================================================

function Logs() {

    const [query, setQuery] = useState("");
    const [level, setLevel] = useState<LogLevelFilter>("all");
    const [autoRefresh, setAutoRefresh] = useState(true);

    // ========================================================
    // DADOS
    // ========================================================

    const {
        logs,
        loading,
        refreshing,
        error,
        lastUpdated,
        total,
        truncated,
        carregarLogs,
    } = useLogsData(autoRefresh);

    const filteredLogs = useMemo(() => {
        const normalizedQuery = query.trim().toLocaleLowerCase("pt-BR");

        return logs.filter((log) => {
            if (level !== "all" && log.level.toUpperCase() !== level) return false;
            if (!normalizedQuery) return true;

            return [log.message, log.event, log.request_id, log.service, log.level]
                .filter((value): value is string => typeof value === "string")
                .some((value) => value.toLocaleLowerCase("pt-BR").includes(normalizedQuery));
        });
    }, [level, logs, query]);


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
                refreshing={refreshing}
                lastUpdated={lastUpdated}
                hasError={Boolean(error)}
                autoRefresh={autoRefresh}
            />


            {/* ==================================================
                ALERTA DE ERRO
                ================================================== */}

            {error && (

                <div className="logs-alert">

                    <TriangleAlert size={18} strokeWidth={1.8} aria-hidden="true" />

                    <span>
                        {error}
                    </span>

                </div>

            )}

            <LogsToolbar
                query={query}
                level={level}
                autoRefresh={autoRefresh}
                onQueryChange={setQuery}
                onLevelChange={setLevel}
                onAutoRefreshChange={setAutoRefresh}
            />


            {/* ==================================================
                PAINEL DE LOGS
                ================================================== */}

            <LogsPanel
                logs={
                    filteredLogs
                }
                loading={
                    loading
                }
                error={
                    error
                }
                filtered={Boolean(query.trim()) || level !== "all"}
                total={total}
                truncated={truncated}
            />

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default Logs;

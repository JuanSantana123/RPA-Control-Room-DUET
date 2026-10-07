import { FileClock, ScrollText } from "lucide-react";

import type { SystemLog } from "../../types/logs";

import EmptyState from "../ui/EmptyState";
import PanelHeader from "../ui/PanelHeader";

import { getLogPresentation } from "./logPresentation";


function formatTimestamp(value: string) {
    const date = new Date(value);

    return Number.isNaN(date.getTime())
        ? value || "Horário não informado"
        : date.toLocaleString("pt-BR");
}


function levelClass(level: string) {
    const normalized = level.toLowerCase();

    return [
        "success",
        "warning",
        "error",
        "critical",
        "debug",
    ].includes(normalized)
        ? normalized
        : "info";
}


function categoryLabel(category?: string | null) {
    switch (category?.toUpperCase()) {
        case "SYSTEM":
            return "Sistema";

        case "AUDIT":
            return "Auditoria";

        case "SECURITY":
            return "Segurança";

        case "INTEGRATION":
            return "Integração";

        default:
            return category || "Sistema";
    }
}


interface LogsPanelProps {
    logs: SystemLog[];
    loading: boolean;
    error: string;
    filtered: boolean;
    total: number;
    truncated: boolean;
}


export default function LogsPanel({
    logs,
    loading,
    error,
    filtered,
    total,
    truncated,
}: LogsPanelProps) {
    return (
        <section
            className="logs-panel"
            aria-busy={loading}
            aria-labelledby="logs-panel-title"
        >
            <PanelHeader
                titleId="logs-panel-title"
                icon={<ScrollText />}
                title="Registros recentes"
                description={
                    truncated
                        ? `Exibindo os 500 mais recentes de ${total} eventos`
                        : `${total} eventos disponíveis nesta leitura`
                }
                actions={
                    <span
                        className="logs-panel-count"
                        aria-label={`${logs.length} registros`}
                    >
                        {logs.length}
                    </span>
                }
            />

            {loading ? (
                <div
                    className="logs-loading-state"
                    role="status"
                >
                    <span className="logs-state-icon">
                        <FileClock size={21} />
                    </span>

                    Carregando registros...
                </div>
            ) : logs.length === 0 ? (
                <EmptyState
                    icon={<FileClock />}
                    title={
                        filtered
                            ? "Nenhum registro corresponde aos filtros"
                            : "Nenhum registro disponível"
                    }
                    description={
                        error
                            ? "A última atualização falhou. Os registros anteriores não estavam disponíveis."
                            : filtered
                              ? "Ajuste a pesquisa ou o nível para ampliar os resultados."
                              : "Os eventos operacionais do Control Room aparecerão aqui."
                    }
                />
            ) : (
                <div
                    className="logs-list"
                    role="log"
                    aria-live="off"
                >
                    {logs.map((log, index) => {
                        const presentation = getLogPresentation(log);

                        return (
                            <article
                                className="logs-entry"
                                key={`${log.timestamp}-${index}`}
                            >
                                <time
                                    className="logs-timestamp"
                                    dateTime={log.timestamp}
                                >
                                    {formatTimestamp(log.timestamp)}
                                </time>

                                <span
                                    className={
                                        `logs-level logs-level-${levelClass(log.level)}`
                                    }
                                >
                                    {log.level || "INFO"}
                                </span>

                                <div className="logs-entry__content">
                                    <pre className="logs-message">
                                        {presentation.headline}

                                        {presentation.detail
                                            ? `\n${presentation.detail}`
                                            : ""}
                                    </pre>

                                    {(
                                        log.event
                                        || log.request_id
                                        || log.service
                                        || log.actor_username
                                        || log.resource_name
                                        || log.status
                                    ) && (
                                        <div
                                            className="logs-entry__metadata"
                                            aria-label="Metadados do registro"
                                        >
                                            {log.actor_username && (
                                                <code>
                                                    {presentation.actorLabel}:{" "}
                                                    {log.actor_username}
                                                </code>
                                            )}

                                            {log.resource_name && (
                                                <code>
                                                    {presentation.resourceLabel}:{" "}
                                                    {log.resource_name}
                                                </code>
                                            )}

                                            {presentation.statusLabel && (
                                                <code>
                                                    status:{" "}
                                                    {presentation.statusLabel}
                                                </code>
                                            )}

                                            {log.category && (
                                                <code>
                                                    categoria:{" "}
                                                    {categoryLabel(log.category)}
                                                </code>
                                            )}

                                            {log.component && (
                                                <code>
                                                    componente:{" "}
                                                    {log.component}
                                                </code>
                                            )}

                                            {log.event && (
                                                <code>
                                                    evento técnico: {log.event}
                                                </code>
                                            )}

                                            {log.service && (
                                                <code>
                                                    serviço: {log.service}
                                                </code>
                                            )}

                                            {log.request_id && (
                                                <code>
                                                    referência: {log.request_id}
                                                </code>
                                            )}
                                        </div>
                                    )}
                                </div>
                            </article>
                        );
                    })}
                </div>
            )}

            <footer className="logs-panel-footer">
                <span>Conteúdo exibido como texto não confiável.</span>
                <span>Mais recentes primeiro</span>
            </footer>
        </section>
    );
}
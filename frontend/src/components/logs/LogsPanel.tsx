import { FileClock, ScrollText } from "lucide-react";
import type { SystemLog } from "../../types/logs";
import EmptyState from "../ui/EmptyState";

function formatTimestamp(value: string) {
  const date = new Date(value);
  return Number.isNaN(date.getTime()) ? value || "Horário não informado" : date.toLocaleString("pt-BR");
}

function levelClass(level: string) {
  const normalized = level.toLowerCase();
  return ["success", "warning", "error", "critical", "debug"].includes(normalized) ? normalized : "info";
}

interface LogsPanelProps {
  logs: SystemLog[];
  loading: boolean;
  error: string;
  filtered: boolean;
  total: number;
  truncated: boolean;
}

export default function LogsPanel({ logs, loading, error, filtered, total, truncated }: LogsPanelProps) {
  return (
    <section className="logs-panel" aria-busy={loading} aria-labelledby="logs-panel-title">
      <div className="logs-panel-header">
        <div className="logs-panel-heading">
          <span className="logs-panel-icon"><ScrollText size={19} aria-hidden="true" /></span>
          <div><h2 id="logs-panel-title">Registros recentes</h2><p>{truncated ? `Exibindo os 500 mais recentes de ${total} eventos` : `${total} eventos disponíveis nesta leitura`}</p></div>
        </div>
        <span className="logs-panel-count" aria-label={`${logs.length} registros`}>{logs.length}</span>
      </div>
      {loading ? (
        <div className="logs-loading-state" role="status"><span className="logs-state-icon"><FileClock size={21} /></span>Carregando registros...</div>
      ) : logs.length === 0 ? (
        <EmptyState
          icon={<FileClock />}
          title={filtered ? "Nenhum registro corresponde aos filtros" : "Nenhum registro disponível"}
          description={error ? "A última atualização falhou. Os registros anteriores não estavam disponíveis." : filtered ? "Ajuste a pesquisa ou o nível para ampliar os resultados." : "Os eventos operacionais do Control Room aparecerão aqui."}
        />
      ) : (
        <div className="logs-list" role="log" aria-live="off">
          {logs.map((log, index) => (
            <article className="logs-entry" key={`${log.timestamp}-${index}`}>
              <time className="logs-timestamp" dateTime={log.timestamp}>{formatTimestamp(log.timestamp)}</time>
              <span className={`logs-level logs-level-${levelClass(log.level)}`}>{log.level || "INFO"}</span>
              <div className="logs-entry__content">
                <pre className="logs-message">{log.message}</pre>
                {(log.event || log.request_id || log.service) && (
                  <div className="logs-entry__metadata" aria-label="Metadados do registro">
                    {log.event && <code>evento: {log.event}</code>}
                    {log.service && <code>serviço: {log.service}</code>}
                    {log.request_id && <code>referência: {log.request_id}</code>}
                  </div>
                )}
              </div>
            </article>
          ))}
        </div>
      )}
      <footer className="logs-panel-footer"><span>Conteúdo exibido como texto não confiável.</span><span>Mais recentes primeiro</span></footer>
    </section>
  );
}

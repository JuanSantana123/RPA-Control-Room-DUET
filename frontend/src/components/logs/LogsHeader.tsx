import { CircleAlert, RefreshCw, Wifi } from "lucide-react";
import { Button } from "../ui/Button";

interface LogsHeaderProps {
  onRefresh: () => void;
  refreshing: boolean;
  lastUpdated: Date | null;
  hasError: boolean;
  autoRefresh: boolean;
}

export default function LogsHeader({ onRefresh, refreshing, lastUpdated, hasError, autoRefresh }: LogsHeaderProps) {
  const statusLabel = hasError
    ? lastUpdated ? "Atualização interrompida" : "Control Room indisponível"
    : !autoRefresh
      ? "Atualização pausada"
    : lastUpdated
      ? `Atualizado ${lastUpdated.toLocaleTimeString("pt-BR")}`
      : "Conectando";

  return (
    <header className="page-heading logs-page-header">
      <div>
        <p className="page-eyebrow logs-page-eyebrow">Observabilidade</p>
        <h1>Atividade do sistema</h1>
        <p>Investigue eventos técnicos com atualização automática controlável e referências rastreáveis.</p>
      </div>
      <div className="logs-header-actions">
        <span
          className={`logs-live-indicator${hasError ? " logs-live-indicator--error" : ""}${!autoRefresh && !hasError ? " logs-live-indicator--paused" : ""}`}
          role="status"
          aria-live="polite"
        >
          {hasError ? <CircleAlert size={14} aria-hidden="true" /> : <Wifi size={14} aria-hidden="true" />}
          {statusLabel}
        </span>
        <Button
          variant="secondary"
          size="sm"
          onClick={onRefresh}
          busy={refreshing}
          loadingLabel="Atualizando registros"
        >
          <RefreshCw size={15} aria-hidden="true" />
          Atualizar
        </Button>
      </div>
    </header>
  );
}

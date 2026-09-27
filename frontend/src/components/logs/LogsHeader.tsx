import { CircleAlert, RefreshCw, Wifi } from "lucide-react";
import { Button } from "../ui/Button";
import PageHeader from "../ui/PageHeader";

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
    <>
      <PageHeader
        eyebrow="OBSERVABILIDADE"
        title="Atividade do sistema"
        description="Investigue eventos técnicos, falhas e referências de requisição."
        actions={
          <Button
            variant="secondary"
            onClick={onRefresh}
            busy={refreshing}
            loadingLabel="Atualizando registros"
          >
            <RefreshCw size={15} aria-hidden="true" />
            Atualizar
          </Button>
        }
      />
      <div className="page-operational-status logs-operational-status">
        <span
          className={`logs-live-indicator${hasError ? " logs-live-indicator--error" : ""}${!autoRefresh && !hasError ? " logs-live-indicator--paused" : ""}`}
          role="status"
          aria-live="polite"
        >
          {hasError ? <CircleAlert size={14} aria-hidden="true" /> : <Wifi size={14} aria-hidden="true" />}
          {statusLabel}
        </span>
      </div>
    </>
  );
}

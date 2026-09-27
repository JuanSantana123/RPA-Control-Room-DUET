import { AlertTriangle, CircleStop, Copy, ListOrdered, X } from "lucide-react";
import { createPortal } from "react-dom";

import { useInteraction } from "../../context/useInteraction";
import { useDialogFocus } from "../../hooks/ui/useDialogFocus";
import type { Execution } from "../../types/executions";
import { calcularDuracao, calcularTempoDeFila, formatarData, formatarPrioridade } from "../../utils/executionFormatters";
import { Button, IconButton } from "../ui/Button";
import PremiumSelect from "../ui/PremiumSelect";
import ExecutionStatusBadge from "./ExecutionStatusBadge";
import ExecutionTimeline from "./ExecutionTimeline";

interface ExecutionDetailsModalProps {
  execution: Execution;
  stopping: boolean;
  cancelling: boolean;
  updatingPriority: boolean;
  queueWarningSeconds: number;
  canStop: boolean;
  canCancel: boolean;
  canUpdatePriority: boolean;
  onClose: () => void;
  onStopExecution: (executionId: number, agentId: string) => void | Promise<void>;
  onCancelExecution: (executionId: number) => void | Promise<void>;
  onUpdatePriority: (executionId: number, priority: Execution["priority"]) => void | Promise<void>;
}

function Detail({ label, value }: { label: string; value: string }) {
  return (
    <div className="execution-detail-card">
      <span>{label}</span>
      <strong title={value}>{value || "-"}</strong>
    </div>
  );
}

export default function ExecutionDetailsModal({
  execution,
  stopping,
  cancelling,
  updatingPriority,
  queueWarningSeconds,
  canStop,
  canCancel,
  canUpdatePriority,
  onClose,
  onStopExecution,
  onCancelExecution,
  onUpdatePriority,
}: ExecutionDetailsModalProps) {
  const { notify } = useInteraction();
  const busy = stopping || cancelling || updatingPriority;
  const dialogRef = useDialogFocus<HTMLDivElement>({ open: true, onClose, closeOnEscape: !busy });
  const queueWait = calcularTempoDeFila(execution.queued_at);
  const queueDelayed = execution.status === "queued" && queueWait.seconds > queueWarningSeconds;

  const copyDiagnostics = async () => {
    const summary = [
      `Execução: #${execution.id}`,
      `Status: ${execution.status}`,
      `Robô: ${execution.robot_name}`,
      `Dispositivo: ${execution.agent_name} (${execution.agent_id})`,
      `PID: ${execution.pid ?? "não informado"}`,
      `Início: ${execution.started_at ?? "não iniciado"}`,
      `Fim: ${execution.finished_at ?? "não concluído"}`,
      execution.schedule_run_id ? `Ocorrência: ${execution.schedule_run_id}` : "",
      execution.status === "queued" ? `Prioridade: ${formatarPrioridade(execution.priority)}` : "",
      execution.status === "queued" ? `Posição no dispositivo: ${execution.queue_position ?? "calculando"}` : "",
      execution.status === "queued" ? `Entrada na fila: ${execution.queued_at ?? "não informada"}` : "",
    ].filter(Boolean).join("\n");

    try {
      await navigator.clipboard.writeText(summary);
      notify({ tone: "success", title: "Resumo copiado", message: "Os identificadores operacionais estão prontos para compartilhar com o suporte." });
    } catch {
      notify({ tone: "danger", title: "Não foi possível copiar", message: "Seu navegador bloqueou o acesso à área de transferência." });
    }
  };

  return createPortal(
    <div className="execution-modal-overlay ui-modal-backdrop" role="presentation" onMouseDown={(event) => {
      if (event.target === event.currentTarget && !busy) onClose();
    }}>
      <div ref={dialogRef} className="execution-modal ui-modal-surface" role="dialog" aria-modal="true"
        aria-labelledby="execution-details-title" aria-describedby="execution-details-description" tabIndex={-1}>
        <header className="execution-modal-header ui-modal-header">
          <div className="execution-modal-heading">
            <span className="page-eyebrow">CENTRAL DA EXECUÇÃO</span>
            <div className="execution-modal-title-row">
              <h2 id="execution-details-title">Execução #{execution.id}</h2>
              <ExecutionStatusBadge status={execution.status} />
            </div>
            <p id="execution-details-description">{execution.robot_name} em {execution.agent_name}</p>
          </div>
          <IconButton data-autofocus label="Fechar detalhes da execução" icon={<X size={18} aria-hidden="true" />}
            disabled={busy} onClick={onClose} />
        </header>

        <div className="execution-modal-body">
          <ExecutionTimeline execution={execution} />

          <div className="execution-detail-grid">
            <Detail label="Origem" value={execution.source_type === "development" ? "Desenvolvimento" : execution.schedule_id ? `Agendamento #${execution.schedule_id}` : "Execução manual"} />
            <Detail label="Versão do robô" value={execution.robot_version ? `v${execution.robot_version}` : "Não informada"} />
            <Detail label="Usuário" value={execution.user_name || execution.username || "Usuário desconhecido"} />
            <Detail label="PID" value={String(execution.pid ?? "Não iniciado")} />
            <Detail label="Início" value={formatarData(execution.started_at)} />
            <Detail label="Duração" value={calcularDuracao(execution.started_at, execution.finished_at)} />
          </div>

          {execution.status === "queued" && (
            <section className={`execution-detail-section execution-queue-panel${queueDelayed ? " execution-queue-panel--warning" : ""}`}
              aria-labelledby="execution-queue-title">
              <div className="execution-queue-panel__heading">
                <div>
                  <span className="execution-detail-label" id="execution-queue-title">Gestão da fila</span>
                  <strong>
                    <ListOrdered size={16} aria-hidden="true" />
                    {execution.queue_position ? `${execution.queue_position}ª posição neste dispositivo` : "Posição sendo calculada"}
                  </strong>
                  <p>{queueWait.label}. A prioridade pode ser ajustada até o início da execução.</p>
                </div>
                {queueDelayed && (
                  <span className="execution-queue-attention">
                    <AlertTriangle size={15} aria-hidden="true" /> Requer atenção
                  </span>
                )}
              </div>
              {canUpdatePriority ? <div className="execution-queue-priority-field">
                <label htmlFor={`execution-priority-${execution.id}`}>Prioridade operacional</label>
                <PremiumSelect
                  id={`execution-priority-${execution.id}`}
                  value={execution.priority}
                  disabled={updatingPriority}
                  onChange={(event) => void onUpdatePriority(execution.id, event.target.value as Execution["priority"])}
                >
                  <option value="low">Baixa — pode aguardar</option>
                  <option value="normal">Normal — ordem padrão</option>
                  <option value="high">Alta — atendimento prioritário</option>
                  <option value="urgent">Urgente — incidente crítico</option>
                </PremiumSelect>
                <small>{updatingPriority ? "Reposicionando na fila…" : `Prioridade atual: ${formatarPrioridade(execution.priority)}`}</small>
              </div> : (
                <div className="execution-queue-priority-readonly">
                  <span>Prioridade operacional</span>
                  <strong>{formatarPrioridade(execution.priority)}</strong>
                  <small>Consulte a ordem atual sem alterar a fila.</small>
                </div>
              )}
            </section>
          )}

          <section className="execution-detail-section" aria-labelledby="execution-identifiers-title">
            <span className="execution-detail-label" id="execution-identifiers-title">Identificadores operacionais</span>
            <dl className="execution-identifiers">
              <div><dt>Dispositivo</dt><dd>{execution.agent_id}</dd></div>
              <div><dt>Pacote</dt><dd>{execution.filename}</dd></div>
              {execution.folder_name && <div><dt>Pasta</dt><dd>{execution.folder_name}</dd></div>}
              {execution.schedule_run_id && <div><dt>Ocorrência</dt><dd>{execution.schedule_run_id}</dd></div>}
            </dl>
          </section>

          {execution.error_message && (
            <section className="execution-detail-section execution-detail-section--error">
              <span className="execution-detail-label">Falha registrada</span>
              <div className="execution-error-box">{execution.error_message}</div>
            </section>
          )}
        </div>

        <footer className="execution-modal-actions ui-modal-footer">
          <Button variant="ghost" size="sm" onClick={() => void copyDiagnostics()}>
            <Copy size={15} aria-hidden="true" /> Copiar resumo
          </Button>
          <div>
            <Button variant="secondary" onClick={onClose} disabled={busy}>Fechar</Button>
            {canCancel && execution.status === "queued" && (
              <Button variant="danger" busy={cancelling} loadingLabel="Cancelando execução"
                onClick={() => void onCancelExecution(execution.id)}>Cancelar da fila</Button>
            )}
            {canStop && execution.status === "running" && (
              <Button variant="danger" busy={stopping} loadingLabel="Parando execução"
                onClick={() => void onStopExecution(execution.id, execution.agent_id)}>
                <CircleStop size={15} aria-hidden="true" /> Parar execução
              </Button>
            )}
          </div>
        </footer>
      </div>
    </div>,
    document.body,
  );
}

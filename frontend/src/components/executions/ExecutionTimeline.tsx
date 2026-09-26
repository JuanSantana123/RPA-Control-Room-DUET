import { Check, Clock3, Flag, Play } from "lucide-react";
import type { Execution } from "../../types/executions";
import { formatarData } from "../../utils/executionFormatters";

type StepState = "complete" | "active" | "pending" | "error";

interface TimelineStep {
  label: string;
  description: string;
  state: StepState;
  icon: typeof Clock3;
}

export default function ExecutionTimeline({ execution }: { execution: Execution }) {
  const isQueued = execution.status === "queued";
  const isRunning = execution.status === "running";
  const isFailure = ["failed", "error", "cancelled", "stopped"].includes(execution.status);
  const isFinished = !isQueued && !isRunning;

  const steps: TimelineStep[] = [
    {
      label: "Solicitação recebida",
      description: execution.schedule_id ? `Agendamento #${execution.schedule_id}` : "Execução manual",
      state: isQueued ? "active" : "complete",
      icon: Clock3,
    },
    {
      label: "Execução no dispositivo",
      description: execution.started_at ? formatarData(execution.started_at) : "Aguardando início",
      state: isRunning ? "active" : isQueued ? "pending" : "complete",
      icon: Play,
    },
    {
      label: "Conclusão",
      description: execution.finished_at ? formatarData(execution.finished_at) : "Ainda não concluída",
      state: isFailure ? "error" : isFinished ? "complete" : "pending",
      icon: isFinished && !isFailure ? Check : Flag,
    },
  ];

  return (
    <ol className="execution-timeline" aria-label="Linha do tempo da execução">
      {steps.map((step) => {
        const Icon = step.icon;
        return (
          <li key={step.label} className={`execution-timeline__step execution-timeline__step--${step.state}`}>
            <span className="execution-timeline__marker" aria-hidden="true"><Icon size={15} /></span>
            <div>
              <strong>{step.label}</strong>
              <span>{step.description}</span>
            </div>
          </li>
        );
      })}
    </ol>
  );
}

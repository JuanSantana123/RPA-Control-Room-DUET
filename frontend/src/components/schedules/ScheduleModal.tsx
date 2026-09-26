import type { Dispatch, FormEvent, SetStateAction } from "react";
import { createPortal } from "react-dom";
import { CalendarClock, Globe2, RotateCw, X } from "lucide-react";

import { useDialogFocus } from "../../hooks/ui/useDialogFocus";
import type { AgentOption, RobotOption } from "../../types/schedules";
import { Button, IconButton } from "../ui/Button";
import FeedbackBanner from "../ui/FeedbackBanner";
import PremiumSelect from "../ui/PremiumSelect";
import { PanelSkeleton } from "../ui/Skeletons";
import { Switch } from "../ui/Switch";
import { TextField } from "../ui/TextField";

const DIAS_SEMANA = [
  ["mon", "Seg"], ["tue", "Ter"], ["wed", "Qua"], ["thu", "Qui"],
  ["fri", "Sex"], ["sat", "Sáb"], ["sun", "Dom"],
] as const;

interface ScheduleModalProps {
  editandoId: number | null;
  robots: RobotOption[];
  agents: AgentOption[];
  timezone: string;
  robotId: string;
  setRobotId: Dispatch<SetStateAction<string>>;
  agentId: string;
  setAgentId: Dispatch<SetStateAction<string>>;
  tipo: string;
  dataInicio: string;
  setDataInicio: Dispatch<SetStateAction<string>>;
  horario: string;
  setHorario: Dispatch<SetStateAction<string>>;
  diasSemana: string[];
  intervaloAtivo: boolean;
  setIntervaloAtivo: Dispatch<SetStateAction<boolean>>;
  intervaloValor: number;
  setIntervaloValor: Dispatch<SetStateAction<number>>;
  intervaloUnidade: string;
  setIntervaloUnidade: Dispatch<SetStateAction<string>>;
  horarioFim: string;
  setHorarioFim: Dispatch<SetStateAction<string>>;
  salvando: boolean;
  loadingOptions: boolean;
  formError: string;
  onClose: () => void;
  onChangeType: (novoTipo: string) => void;
  onToggleWeekday: (dia: string) => void;
  onRetryOptions: () => void | Promise<unknown>;
  onSave: () => void | Promise<void>;
}

export default function ScheduleModal({
  editandoId, robots, agents, timezone, robotId, setRobotId, agentId, setAgentId, tipo,
  dataInicio, setDataInicio, horario, setHorario, diasSemana, intervaloAtivo,
  setIntervaloAtivo, intervaloValor, setIntervaloValor, intervaloUnidade,
  setIntervaloUnidade, horarioFim, setHorarioFim, salvando, loadingOptions,
  formError, onClose, onChangeType, onToggleWeekday, onRetryOptions, onSave,
}: ScheduleModalProps) {
  const dialogRef = useDialogFocus<HTMLDivElement>({ open: true, onClose, closeOnEscape: !salvando });
  const weeklyInvalid = tipo === "weekly" && diasSemana.length === 0;
  const intervalInvalid = tipo !== "once" && intervaloAtivo && (!intervaloValor || !horarioFim);
  const formInvalid = loadingOptions || !robotId || !dataInicio || !horario || weeklyInvalid || intervalInvalid;

  const handleSubmit = (event: FormEvent<HTMLFormElement>) => {
    event.preventDefault();
    if (!formInvalid && !salvando) void onSave();
  };

  return createPortal(
    <div className="schedule-modal-overlay" onMouseDown={(event) => {
      if (event.target === event.currentTarget && !salvando) onClose();
    }}>
      <div ref={dialogRef} className="schedule-modal" role="dialog" aria-modal="true"
        aria-labelledby="schedule-modal-title" aria-describedby="schedule-modal-description" tabIndex={-1}>
        <header className="schedule-modal-header">
          <div className="schedule-modal-heading">
            <span className="schedule-modal-heading__icon" aria-hidden="true"><CalendarClock size={19} /></span>
            <div>
              <h2 id="schedule-modal-title">{editandoId === null ? "Novo agendamento" : "Editar agendamento"}</h2>
              <p id="schedule-modal-description">Defina a automação, o destino e quando a execução deverá começar.</p>
            </div>
          </div>
          <IconButton label="Fechar agendamento" icon={<X size={17} aria-hidden="true" />}
            disabled={salvando} onClick={onClose} />
        </header>

        <form className="schedule-modal-form" onSubmit={handleSubmit}>
          <div className="schedule-modal-body">
            {formError && <FeedbackBanner tone="error" title="Não foi possível concluir o agendamento"
              message={formError} hint={loadingOptions ? undefined : "Seu preenchimento foi preservado. Corrija o item indicado e tente novamente."} />}

            {loadingOptions ? (
              <div className="schedule-modal-loading" aria-label="Carregando opções do agendamento"><PanelSkeleton lines={5} /></div>
            ) : <>
              <section className="schedule-form-section" aria-labelledby="schedule-target-title">
                <div className="schedule-form-section__heading"><span>1</span><div>
                  <h3 id="schedule-target-title">O que será executado</h3>
                  <p>Escolha o robô e, opcionalmente, fixe um dispositivo.</p>
                </div></div>
                <div className="schedule-form-grid">
                  <div className="schedule-form-group">
                    <label htmlFor="schedule-robot">Robô</label>
                    <PremiumSelect id="schedule-robot" value={robotId} onChange={(event) => setRobotId(event.target.value)} required>
                      <option value="">Selecione um robô</option>
                      {robots.map((robot) => <option key={robot.id} value={robot.id}>{robot.name}</option>)}
                    </PremiumSelect>
                  </div>
                  <div className="schedule-form-group">
                    <label htmlFor="schedule-agent">Dispositivo</label>
                    <PremiumSelect id="schedule-agent" value={agentId} onChange={(event) => setAgentId(event.target.value)}>
                      <option value="">Seleção automática</option>
                      {agents.map((agent) => <option key={agent.agent_id} value={agent.agent_id}>{agent.name} · {agent.status}</option>)}
                    </PremiumSelect>
                    <small>Automático usa um dispositivo disponível no momento da execução.</small>
                  </div>
                </div>
                {robots.length === 0 && <div className="schedule-options-empty" role="status">
                  <span>Nenhum robô publicado está disponível.</span>
                  <Button size="sm" variant="ghost" type="button" onClick={() => void onRetryOptions()}>
                    <RotateCw size={14} aria-hidden="true" /> Atualizar opções
                  </Button>
                </div>}
              </section>

              <section className="schedule-form-section" aria-labelledby="schedule-time-title">
                <div className="schedule-form-section__heading"><span>2</span><div>
                  <h3 id="schedule-time-title">Quando deverá executar</h3>
                  <p>Configure o início e a recorrência da automação.</p>
                </div></div>
                <div className="schedule-timezone-note" role="note">
                  <Globe2 size={16} aria-hidden="true" />
                  <div>
                    <strong>Fuso horário do Control Room</strong>
                    <span>{timezone} · horários inválidos ou ambíguos em mudanças de horário civil serão recusados.</span>
                  </div>
                </div>
                <div className="schedule-form-grid schedule-form-grid--timing">
                  <div className="schedule-form-group">
                    <label htmlFor="schedule-type">Frequência</label>
                    <PremiumSelect id="schedule-type" value={tipo} onChange={(event) => onChangeType(event.target.value)} required>
                      <option value="once">Uma vez</option><option value="daily">Diariamente</option>
                      <option value="weekly">Semanalmente</option><option value="monthly">Mensalmente</option>
                    </PremiumSelect>
                  </div>
                  <TextField id="schedule-start-date" label="Data de início" type="date" value={dataInicio}
                    onChange={(event) => setDataInicio(event.target.value)} required />
                  <TextField id="schedule-time" label="Horário" type="time" value={horario}
                    onChange={(event) => setHorario(event.target.value)} required />
                </div>

                {tipo === "weekly" && <fieldset className="schedule-weekdays-fieldset">
                  <legend>Dias da semana</legend>
                  <div className="schedule-weekdays">{DIAS_SEMANA.map(([value, label]) => <label key={value}>
                    <input type="checkbox" checked={diasSemana.includes(value)} onChange={() => onToggleWeekday(value)} />
                    <span>{label}</span>
                  </label>)}</div>
                  {weeklyInvalid && <small>Selecione ao menos um dia.</small>}
                </fieldset>}

                {tipo !== "once" && <div className="schedule-interval-block">
                  <Switch label="Repetir dentro de uma janela"
                    description="Cria novas execuções no intervalo informado até o horário limite."
                    checked={intervaloAtivo} onChange={(event) => setIntervaloAtivo(event.target.checked)} />
                  {intervaloAtivo && <div className="schedule-interval-config">
                    <TextField id="schedule-interval-value" label="Executar a cada" type="number" min={1}
                      value={intervaloValor} onChange={(event) => setIntervaloValor(Number(event.target.value))} required />
                    <div className="schedule-form-group"><label htmlFor="schedule-interval-unit">Unidade</label>
                      <PremiumSelect id="schedule-interval-unit" value={intervaloUnidade}
                        onChange={(event) => setIntervaloUnidade(event.target.value)}>
                        <option value="minutes">Minutos</option><option value="hours">Horas</option>
                      </PremiumSelect>
                    </div>
                    <TextField id="schedule-end-time" label="Repetir até" type="time" value={horarioFim}
                      onChange={(event) => setHorarioFim(event.target.value)} required />
                  </div>}
                </div>}
              </section>
            </>}
          </div>

          <footer className="schedule-modal-actions">
            <p aria-live="polite">{formInvalid ? "Preencha os campos obrigatórios para salvar." : "Configuração pronta para ser salva."}</p>
            <div>
              <Button variant="secondary" type="button" onClick={onClose} disabled={salvando}>Cancelar</Button>
              <Button variant="primary" type="submit" busy={salvando} disabled={formInvalid} loadingLabel="Salvando agendamento">
                {editandoId === null ? "Criar agendamento" : "Salvar alterações"}
              </Button>
            </div>
          </footer>
        </form>
      </div>
    </div>,
    document.body,
  );
}

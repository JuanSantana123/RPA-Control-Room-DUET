// ============================================================
// DUET CORE - SCHEDULES - MODAL
// ============================================================
//
// Modal visual utilizado para criar ou editar Agendamentos.
//
// Responsabilidade:
// - renderizar os campos do formulário;
// - renderizar Robots e Agents disponíveis;
// - renderizar seleção de tipo;
// - renderizar dias da semana quando o tipo for weekly;
// - renderizar configuração de intervalo quando aplicável;
// - encaminhar alterações através dos setters/callbacks;
// - encaminhar as ações de salvar e cancelar.
//
// A lógica do Scheduler NÃO pertence a este componente.
//
// Este componente NÃO:
// - executa chamadas HTTP;
// - monta payload;
// - valida regras de negócio;
// - carrega Schedule para edição;
// - cria ou atualiza Schedule;
// - calcula próxima execução.
//
// Toda a lógica permanece em useScheduleForm.ts.
// ============================================================

import type {
    Dispatch,
    SetStateAction,
} from "react";

import type {
    AgentOption,
    RobotOption,
} from "../../types/schedules";


// ============================================================
// DIAS DA SEMANA
// ============================================================
//
// Mantém exatamente os valores técnicos utilizados atualmente
// pelo Scheduler.
// ============================================================

const DIAS_SEMANA = [
    ["mon", "Segunda"],
    ["tue", "Terça"],
    ["wed", "Quarta"],
    ["thu", "Quinta"],
    ["fri", "Sexta"],
    ["sat", "Sábado"],
    ["sun", "Domingo"],
];


// ============================================================
// PROPS
// ============================================================

interface ScheduleModalProps {
    editandoId: number | null;

    robots: RobotOption[];
    agents: AgentOption[];

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

    onClose: () => void;

    onChangeType: (
        novoTipo: string
    ) => void;

    onToggleWeekday: (
        dia: string
    ) => void;

    onSave: () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function ScheduleModal({
    editandoId,

    robots,
    agents,

    robotId,
    setRobotId,

    agentId,
    setAgentId,

    tipo,

    dataInicio,
    setDataInicio,

    horario,
    setHorario,

    diasSemana,

    intervaloAtivo,
    setIntervaloAtivo,

    intervaloValor,
    setIntervaloValor,

    intervaloUnidade,
    setIntervaloUnidade,

    horarioFim,
    setHorarioFim,

    salvando,

    onClose,
    onChangeType,
    onToggleWeekday,
    onSave,
}: ScheduleModalProps) {

    return (
        <div className="schedule-modal-overlay">

            <div className="schedule-modal">

                {/* ==================================================
                    CABEÇALHO DO MODAL
                    ================================================== */}

                <div className="schedule-modal-header">

                    <div>

                        <h2>
                            {editandoId === null
                                ? "Novo Agendamento"
                                : "Editar Agendamento"
                            }
                        </h2>

                        <p>
                            Configure quando o robô deverá executar.
                        </p>

                    </div>


                    <button
                        type="button"
                        onClick={onClose}
                    >
                        ✕
                    </button>

                </div>


                {/* ==================================================
                    ROBÔ
                    ================================================== */}

                <div className="schedule-form-group">

                    <label>
                        Robô
                    </label>

                    <select
                        value={robotId}
                        onChange={(event) => {
                            setRobotId(
                                event.target.value
                            );
                        }}
                        required
                    >

                        <option value="">
                            Selecione um robô
                        </option>

                        {robots.map(
                            (robot) => (

                                <option
                                    key={robot.id}
                                    value={robot.id}
                                >
                                    {robot.name}
                                </option>

                            )
                        )}

                    </select>

                </div>


                <br />


                {/* ==================================================
                    AGENT
                    ================================================== */}

                <div className="schedule-form-group">

                    <label>
                        Agent
                    </label>

                    <select
                        value={agentId}
                        onChange={(event) => {
                            setAgentId(
                                event.target.value
                            );
                        }}
                    >

                        <option value="">
                            Automático
                        </option>

                        {agents.map(
                            (agent) => (

                                <option
                                    key={agent.agent_id}
                                    value={agent.agent_id}
                                >
                                    {agent.name} - {agent.agent_id} ({agent.status})
                                </option>

                            )
                        )}

                    </select>

                    <small>
                        Automático seleciona um Agent disponível no momento da execução.
                    </small>

                </div>


                <br />


                {/* ==================================================
                    TIPO
                    ================================================== */}

                <div className="schedule-form-group">

                    <label>
                        Tipo de agendamento
                    </label>

                    <select
                        value={tipo}
                        onChange={(event) => {
                            onChangeType(
                                event.target.value
                            );
                        }}
                        required
                    >

                        <option value="once">
                            Uma vez
                        </option>

                        <option value="daily">
                            Diário
                        </option>

                        <option value="weekly">
                            Semanal
                        </option>

                        <option value="monthly">
                            Mensal
                        </option>

                    </select>

                </div>


                <br />


                {/* ==================================================
                    DATA
                    ================================================== */}

                <div className="schedule-form-group">

                    <label>
                        Data de início
                    </label>

                    <input
                        type="date"
                        value={dataInicio}
                        onChange={(event) => {
                            setDataInicio(
                                event.target.value
                            );
                        }}
                        required
                    />

                </div>


                <br />


                {/* ==================================================
                    DIAS DA SEMANA
                    ================================================== */}

                {tipo === "weekly" && (

                    <div>

                        <label>
                            Dias da semana
                        </label>

                        <div className="schedule-weekdays">

                            {DIAS_SEMANA.map(
                                ([valor, nome]) => (

                                    <label
                                        key={valor}
                                    >

                                        <input
                                            type="checkbox"
                                            checked={
                                                diasSemana.includes(
                                                    valor
                                                )
                                            }
                                            onChange={() => {
                                                onToggleWeekday(
                                                    valor
                                                );
                                            }}
                                        />

                                        {" "}

                                        {nome}

                                    </label>

                                )
                            )}

                        </div>

                    </div>

                )}


                {tipo === "weekly" && (
                    <br />
                )}


                {/* ==================================================
                    INTERVALO
                    ================================================== */}

                {tipo !== "once" && (

                    <div>

                        <label>

                            <input
                                type="checkbox"
                                checked={intervaloAtivo}
                                onChange={(event) => {
                                    setIntervaloAtivo(
                                        event.target.checked
                                    );
                                }}
                            />

                            {" "}

                            Repetir em intervalos

                        </label>

                    </div>

                )}


                {/* ==================================================
                    CONFIGURAÇÃO DO INTERVALO
                    ================================================== */}

                {tipo !== "once" &&
                    intervaloAtivo && (

                        <div className="schedule-interval-config">

                            <div>

                                <label>
                                    Executar a cada
                                </label>

                                <input
                                    type="number"
                                    min="1"
                                    value={intervaloValor}
                                    onChange={(event) => {
                                        setIntervaloValor(
                                            Number(
                                                event.target.value
                                            )
                                        );
                                    }}
                                />

                            </div>


                            <br />


                            <div>

                                <label>
                                    Unidade
                                </label>

                                <select
                                    value={intervaloUnidade}
                                    onChange={(event) => {
                                        setIntervaloUnidade(
                                            event.target.value
                                        );
                                    }}
                                >

                                    <option value="minutes">
                                        Minutos
                                    </option>

                                    <option value="hours">
                                        Horas
                                    </option>

                                </select>

                            </div>


                            <br />


                            <div>

                                <label>
                                    Repetir até
                                </label>

                                <input
                                    type="time"
                                    value={horarioFim}
                                    onChange={(event) => {
                                        setHorarioFim(
                                            event.target.value
                                        );
                                    }}
                                />

                            </div>

                        </div>

                    )}


                <br />


                {/* ==================================================
                    HORÁRIO
                    ================================================== */}

                <div className="schedule-form-group">

                    <label>
                        Horário
                    </label>

                    <input
                        type="time"
                        value={horario}
                        onChange={(event) => {
                            setHorario(
                                event.target.value
                            );
                        }}
                        required
                    />

                </div>


                {/* ==================================================
                    BOTÕES
                    ================================================== */}

                <div className="schedule-modal-actions">

                    <button
                        type="button"
                        className="schedule-cancel-button"
                        onClick={onClose}
                        disabled={salvando}
                    >
                        Cancelar
                    </button>


                    <button
                        type="button"
                        className="schedule-save-button"
                        onClick={onSave}
                        disabled={salvando}
                    >
                        {salvando
                            ? "Salvando..."
                            : "Salvar Agendamento"
                        }
                    </button>

                </div>

            </div>

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default ScheduleModal;
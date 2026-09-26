// ============================================================
// DUET CORE - EXECUTIONS - TABLE ROW
// ============================================================
//
// Representa visualmente uma única execução dentro da tabela.
//
// Responsabilidade:
// - apresentar os dados da execução;
// - apresentar o status;
// - disponibilizar ação de detalhes;
// - disponibilizar Stop para execução "running";
// - disponibilizar Cancel para execução "queued".
//
// Origem dos dados e ações:
// - recebe a Execution e callbacks através de props.
//
// Dependências:
// - executionFormatters para datas e duração;
// - ExecutionStatusBadge para apresentação do status;
// - lucide-react para os ícones.
//
// Este componente NÃO:
// - consulta API;
// - executa Stop ou Cancel diretamente;
// - controla polling;
// - controla filtros;
// - mantém a execução selecionada.
//
// As ações permanecem sob responsabilidade da página/hooks.
// ============================================================

import {
    CircleStop,
    Eye,
    Server,
    Clock3,
} from "lucide-react";

import type {
    Execution,
} from "../../types/executions";

import {
    calcularDuracao,
    calcularTempoDeFila,
    formatarData,
    formatarPrioridade,
} from "../../utils/executionFormatters";

import ExecutionStatusBadge from "./ExecutionStatusBadge";
import { Button, IconButton } from "../ui/Button";


// ============================================================
// PROPS
// ============================================================

interface ExecutionRowProps {

    // Execução representada por esta linha.
    execution: Execution;

    // IDs usados para representar ações em andamento.
    parandoExecucao: number | null;
    cancelandoExecucao: number | null;
    queueWarningSeconds: number;

    // Abre os detalhes da execução.
    onViewDetails: (
        execution: Execution
    ) => void;

    // Solicita parada de execução em andamento.
    onStopExecution: (
        executionId: number,
        agentId: string
    ) => void | Promise<void>;

    // Solicita cancelamento de execução da fila.
    onCancelExecution: (
        executionId: number
    ) => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function ExecutionRow({
    execution,
    parandoExecucao,
    cancelandoExecucao,
    queueWarningSeconds,
    onViewDetails,
    onStopExecution,
    onCancelExecution,
}: ExecutionRowProps) {

    return (
        <tr>

            {/* =================================================
                ID
            ================================================= */}

            <td>
                <span className="execution-id">
                    #{execution.id}
                </span>
            </td>


            {/* =================================================
                ROBOT
            ================================================= */}

            <td>
                <div className="execution-robot-cell">

                    <strong>
                        {execution.robot_name}
                    </strong>

                    {/* Só exibe o filename quando for diferente
                        do nome apresentado para o Robot. */}
                    {execution.filename &&
                        execution.filename !==
                            execution.robot_name && (

                        <span>
                            {execution.filename}
                        </span>
                    )}

                </div>
            </td>


            {/* =================================================
                PASTA
            ================================================= */}

            <td>
                <div className="execution-folder-cell">
                    {execution.folder_name ||
                        "Pasta raiz"}
                </div>
            </td>


            {/* =================================================
                USUÁRIO
            ================================================= */}

            <td>
                <div className="execution-user-cell">

                    <strong>
                        {execution.user_name ||
                            execution.username ||
                            "Usuário desconhecido"}
                    </strong>

                    {execution.username &&
                        execution.user_name &&
                        execution.username !==
                            execution.user_name && (

                        <span>
                            {execution.username}
                        </span>
                    )}

                </div>
            </td>


            {/* =================================================
                AGENT
            ================================================= */}

            <td>
                <div className="execution-agent-cell">

                    <Server size={14} />

                    <div>

                        <strong>
                            {execution.agent_name}
                        </strong>

                        <div className="execution-agent-id">
                            {execution.agent_id}
                        </div>

                    </div>

                </div>
            </td>


            {/* =================================================
                PID
            ================================================= */}

            <td>
                <span className="execution-monospace">
                    {execution.pid ?? "-"}
                </span>
            </td>


            {/* =================================================
                INÍCIO
            ================================================= */}

            <td>
                {formatarData(
                    execution.started_at
                )}
            </td>


            {/* =================================================
                DURAÇÃO
            ================================================= */}

            <td>
                <span className="execution-duration">

                    <Clock3 size={14} />

                    {calcularDuracao(
                        execution.started_at,
                        execution.finished_at
                    )}

                </span>
            </td>


            {/* =================================================
                STATUS
            ================================================= */}

            <td>
                <div className="execution-status-stack">
                    <ExecutionStatusBadge status={execution.status} />
                    {execution.status === "queued" && (() => {
                        const wait = calcularTempoDeFila(execution.queued_at);
                        const delayed = wait.seconds > queueWarningSeconds;
                        return (
                            <div className={`execution-queue-context${delayed ? " execution-queue-context--warning" : ""}`}>
                                <span className={`execution-priority execution-priority--${execution.priority}`}>
                                    {formatarPrioridade(execution.priority)}
                                </span>
                                {execution.queue_position && <span>#{execution.queue_position} no dispositivo</span>}
                                <span>{wait.label}</span>
                            </div>
                        );
                    })()}
                </div>
            </td>


            {/* =================================================
                AÇÕES
            ================================================= */}

            <td>
                <div className="execution-actions">

                    {/* Detalhes */}
                    <IconButton
                        size="sm"
                        label={`Ver detalhes da execução ${execution.id}`}
                        tooltip="Ver detalhes"
                        icon={<Eye size={16} aria-hidden="true" />}
                        onClick={() =>
                            onViewDetails(
                                execution
                            )
                        }
                    />


                    {/* Stop disponível somente durante running. */}
                    {execution.status ===
                        "running" && (

                        <Button
                            size="sm"
                            variant="danger"
                            onClick={() =>
                                onStopExecution(
                                    execution.id,
                                    execution.agent_id
                                )
                            }
                            busy={parandoExecucao === execution.id}
                            loadingLabel="Parando execução"
                        >
                            <CircleStop size={14} aria-hidden="true" />
                            Parar
                        </Button>
                    )}


                    {/* Cancel disponível somente enquanto
                        a execução estiver na fila. */}
                    {execution.status ===
                        "queued" && (

                        <Button
                            size="sm"
                            variant="danger"
                            onClick={() =>
                                onCancelExecution(
                                    execution.id
                                )
                            }
                            busy={cancelandoExecucao === execution.id}
                            loadingLabel="Cancelando execução"
                        >
                            Cancelar
                        </Button>
                    )}

                </div>
            </td>

        </tr>
    );
}


export default ExecutionRow;

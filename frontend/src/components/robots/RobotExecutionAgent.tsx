// ============================================================
// DUET CORE - ROBOTS - EXECUTION AGENT SELECTOR
// ============================================================
//
// Responsabilidade:
// - renderizar o seletor do Agent utilizado para execução
//   manual de Robots;
// - apresentar os Agents disponíveis;
// - informar externamente quando a seleção for alterada.
//
// Este componente NÃO:
// - carrega Agents;
// - executa Robots;
// - conhece tokens de Agent;
// - realiza chamadas HTTP;
// - decide permissões.
//
// O estado e as operações permanecem controlados pelo fluxo
// externo da página/hook.
//
// Integrações:
// - página Robots;
// - futuro hook useRobotExecution;
// - tipo ExecutionAgent.
// ============================================================

import { Server } from "lucide-react";

import type {
    ExecutionAgent,
} from "../../types/robots";


interface RobotExecutionAgentProps {
    executionAgents: ExecutionAgent[];

    selectedExecutionAgent: string;

    onSelectedExecutionAgentChange: (
        agentId: string
    ) => void;
}


function RobotExecutionAgent({
    executionAgents,
    selectedExecutionAgent,
    onSelectedExecutionAgentChange,
}: RobotExecutionAgentProps) {

    return (
        <div className="execution-agent-section">

            <div className="form-field">
                <label htmlFor="execution-agent">
                    Agent para execução
                </label>

                <select
                    id="execution-agent"
                    value={selectedExecutionAgent}
                    onChange={(event) =>
                        onSelectedExecutionAgentChange(
                            event.target.value
                        )
                    }
                >
                    <option value="">
                        Selecione um Agent
                    </option>

                    {executionAgents.map((agent) => (
                        <option
                            key={agent.agent_id}
                            value={agent.agent_id}
                        >
                            {agent.name} — {agent.agent_id}
                        </option>
                    ))}
                </select>
            </div>


            <div className="execution-agent-hint">
                <Server
                    size={15}
                    strokeWidth={1.7}
                />

                <span>
                    O robô será executado no Agent selecionado.
                </span>
            </div>
        </div>
    );
}


export default RobotExecutionAgent;
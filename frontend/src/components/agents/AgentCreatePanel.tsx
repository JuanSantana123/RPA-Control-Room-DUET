// ============================================================
// DUET CORE - AGENTS - CREATE PANEL
// ============================================================
//
// Painel visual responsável pelo formulário de cadastro
// de um novo Device/Agent.
//
// Responsabilidade:
// - exibir o campo de porta de comunicação;
// - refletir o estado atual do formulário;
// - bloquear edição durante o cadastro;
// - encaminhar alterações da porta;
// - encaminhar a solicitação de cadastro.
//
// Este componente NÃO:
// - chama POST /agents;
// - valida regras de cadastro;
// - define rpa_directory;
// - cria agent_id ou agent_token;
// - altera diretamente a lista de Agents.
//
// Essas responsabilidades pertencem a useAgentsData.ts.
// ============================================================

import type {
    Dispatch,
    SetStateAction,
} from "react";

import {
    Boxes,
    Network,
    Plus,
} from "lucide-react";

import type {
    NewAgentForm,
} from "../../types/agents";


// ============================================================
// PROPS
// ============================================================

interface AgentCreatePanelProps {
    newAgent: NewAgentForm;

    setNewAgent:
        Dispatch<
            SetStateAction<NewAgentForm>
        >;

    creatingAgent: boolean;

    onCreate:
        () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function AgentCreatePanel({
    newAgent,
    setNewAgent,
    creatingAgent,
    onCreate,
}: AgentCreatePanelProps) {

    return (
        <section className="content-panel agent-create-panel">

            <div className="content-panel-header">

                <div>

                    <h2>
                        Novo Device
                    </h2>

                    <p>
                        Configure os parâmetros iniciais do device de execução.
                    </p>

                </div>


                <div className="section-icon">
                    <Plus
                        size={18}
                        strokeWidth={1.8}
                    />
                </div>

            </div>


            <div className="agent-form">

                <div className="form-field">


                    <div className="form-field">

                        <label htmlFor="agent-environment">
                            Ambiente
                        </label>

                        <div className="input-with-icon">

                            <Boxes
                                size={16}
                                strokeWidth={1.8}
                            />

                            <select
                                id="agent-environment"
                                value={newAgent.environment}
                                disabled={creatingAgent}
                                onChange={(event) => {

                                    setNewAgent({
                                        ...newAgent,

                                        environment:
                                            event.target.value as
                                                "development" |
                                                "production",
                                    });
                                }}
                            >
                                <option value="development">
                                    Desenvolvimento / Homologação
                                </option>

                                <option value="production">
                                    Produção
                                </option>
                            </select>

                        </div>

                    </div>

                    <label htmlFor="agent-port">
                        Porta de comunicação
                    </label>


                    <div className="input-with-icon">

                        <Network
                            size={16}
                            strokeWidth={1.8}
                        />


                        <input
                            id="agent-port"
                            type="number"
                            placeholder="Ex.: 8000"
                            value={newAgent.port}
                            disabled={creatingAgent}
                            onChange={(event) => {

                                setNewAgent({
                                    ...newAgent,
                                    port:
                                        event.target.value,
                                });
                            }}
                        />

                    </div>

                </div>


                <button
                    className="primary-button"
                    onClick={onCreate}
                    disabled={creatingAgent}
                >

                    <Plus
                        size={16}
                        strokeWidth={2}
                    />

                    {creatingAgent
                        ? "Cadastrando..."
                        : "Cadastrar Device"
                    }

                </button>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default AgentCreatePanel;
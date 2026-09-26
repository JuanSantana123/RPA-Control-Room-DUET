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
    CircleCheck,
    Network,
    Plus,
    ServerCog,
} from "lucide-react";

import type {
    NewAgentForm,
} from "../../types/agents";
import PremiumSelect from "../ui/PremiumSelect";
import { Button } from "../ui/Button";
import { TextField } from "../ui/TextField";


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
    const numericPort = Number(newAgent.port);
    const portIsValid = Number.isInteger(numericPort) && numericPort >= 1 && numericPort <= 65535;
    const portError = newAgent.port && !portIsValid
        ? "Use uma porta inteira entre 1 e 65535."
        : undefined;

    return (
        <section className="content-panel agent-create-panel">

            <div className="content-panel-header">

                <div>

                    <h2>
                        Novo dispositivo
                    </h2>

                    <p>
                        Configure os parâmetros iniciais do device de execução.
                    </p>

                </div>


                <div className="agent-create-panel__status" aria-label="Cadastro em duas etapas">
                    <ServerCog
                        size={18}
                        strokeWidth={1.8}
                        aria-hidden="true"
                    />
                    <span>Configuração rápida</span>
                </div>

            </div>


            <form
                className="agent-form"
                onSubmit={(event) => {
                    event.preventDefault();
                    if (portIsValid) void onCreate();
                }}
            >

                <div className="form-field">

                        <label htmlFor="agent-environment">
                            <span className="agent-field-step">1</span>
                            Ambiente de execução
                        </label>

                        <div className="input-with-icon">

                            <Boxes
                                size={16}
                                strokeWidth={1.8}
                            />

                            <PremiumSelect
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
                            </PremiumSelect>

                        </div>

                </div>

                <TextField
                    id="agent-port"
                    label={<span className="agent-field-label"><span className="agent-field-step">2</span>Porta de comunicação</span>}
                    description="Porta local reservada para a comunicação segura com este dispositivo."
                    error={portError}
                    type="number"
                    inputMode="numeric"
                    min={1}
                    max={65535}
                    placeholder="Ex.: 8000"
                    value={newAgent.port}
                    disabled={creatingAgent}
                    leadingIcon={<Network size={16} strokeWidth={1.8} />}
                    onChange={(event) => {
                        setNewAgent({
                            ...newAgent,
                            port: event.target.value,
                        });
                    }}
                />


                <Button
                    variant="primary"
                    className="agent-create-submit"
                    type="submit"
                    busy={creatingAgent}
                    disabled={!portIsValid}
                    loadingLabel="Cadastrando dispositivo"
                >

                    <Plus
                        size={16}
                        strokeWidth={2}
                    />

                    Cadastrar dispositivo

                </Button>

                <div className="agent-create-panel__assurance">
                    <CircleCheck size={15} aria-hidden="true" />
                    <span>Você poderá baixar o instalador e o token após o cadastro.</span>
                </div>

            </form>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default AgentCreatePanel;

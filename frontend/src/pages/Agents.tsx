import { useEffect, useState } from "react";

import api from "../services/api";


// ============================================================
// TIPO - AGENT
// ============================================================
//
// Representa um Agent retornado pelo Control Room.
//
// Esses dados vêm da API:
//
// GET /agents
// ============================================================

interface Agent {
    agent_id: string;
    name: string;
    host: string;
    port: number;
    rpa_directory: string | null;
    status: string;
}


// ============================================================
// PÁGINA DE AGENTS
// ============================================================
//
// Esta página substitui a antiga página:
//
// /agents-page
//
// A interface agora será responsabilidade do React.
//
// O FastAPI continua responsável pela API e pelo banco.
// ============================================================

function Agents() {

    // ========================================================
    // ESTADOS
    // ========================================================

    // Guarda a lista de Agents retornada pela API.
    const [agents, setAgents] = useState<Agent[]>([]);

    // Indica se a API ainda está sendo consultada.
    const [loading, setLoading] = useState(true);

    // Guarda uma mensagem de erro, caso a consulta falhe.
    const [error, setError] = useState("");

    // Guarda os dados do novo Agent.
    const [newAgent, setNewAgent] = useState({
        agent_id: "",
        name: "",
        host: "",
        port: "",
        rpa_directory: ""
    });

    // Controla o envio do cadastro.
    const [creatingAgent, setCreatingAgent] = useState(false);


    // ========================================================
    // BUSCAR AGENTS
    // ========================================================
    //
    // Consulta:
    //
    // GET /agents
    //
    // Essa é uma API que já existe no nosso Control Room.
    // ========================================================

    useEffect(() => {

        api
            .get("/agents")

            .then((response) => {

                // Guarda os Agents retornados pelo backend.
                setAgents(response.data.agents);

            })

            .catch((err) => {

                // Mostra o erro no console para diagnóstico.
                console.error(
                    "Erro ao buscar Agents:",
                    err
                );

                // Mostra uma mensagem amigável na tela.
                setError(
                    "Não foi possível carregar os Agents."
                );

            })

            .finally(() => {

                // Finaliza o carregamento.
                setLoading(false);

            });

    }, []);


        // ========================================================
        // CADASTRAR AGENT
        // ========================================================
        //
        // Cria um novo Agent no Control Room.
        //
        // POST /agents/register
        // ========================================================

        const cadastrarAgent = async () => {

            // Valida os campos obrigatórios.
            if (
                !newAgent.agent_id.trim() ||
                !newAgent.name.trim() ||
                !newAgent.host.trim() ||
                !newAgent.port.trim()
            ) {
                setError(
                    "Preencha ID, nome, host e porta do Agent."
                );

                return;
            }

            try {

                setCreatingAgent(true);
                setError("");

                // Envia os dados para o Control Room.
                const response = await api.post(
                    "/agents/register",
                    {
                        agent_id: newAgent.agent_id.trim(),
                        name: newAgent.name.trim(),
                        host: newAgent.host.trim(),
                        port: Number(newAgent.port),
                        rpa_directory:
                            newAgent.rpa_directory.trim() || null
                    }
                );

                // Verifica se o cadastro foi realizado.
                if (response.data.status !== "success") {

                    setError(
                        response.data.message ||
                        "Não foi possível cadastrar o Agent."
                    );

                    return;
                }

                // Adiciona o novo Agent na lista.
                setAgents((agentsAtuais) => [
                    ...agentsAtuais,
                    response.data.agent
                ]);

                // Limpa o formulário.
                setNewAgent({
                    agent_id: "",
                    name: "",
                    host: "",
                    port: "",
                    rpa_directory: ""
                });

            } catch (err) {

                console.error(
                    "Erro ao cadastrar Agent:",
                    err
                );

                setError(
                    "Não foi possível cadastrar o Agent."
                );

            } finally {

                setCreatingAgent(false);
            }
        };
        // ========================================================
        // EXCLUIR AGENT
        // ========================================================
        //
        // Remove o Agent do Control Room.
        //
        // DELETE /agents/{agent_id}
        // ========================================================

        const excluirAgent = async (
            agentId: string,
            agentName: string
        ) => {

            // Confirma antes de excluir.
            const confirmar = window.confirm(
                `Deseja realmente excluir o Agent "${agentName}"?`
            );

            if (!confirmar) {
                return;
            }

            try {

                // Chama o endpoint DELETE do Control Room.
                const response = await api.delete(
                    `/agents/${agentId}`
                );

                // Verifica se o backend confirmou a exclusão.
                if (response.data.status === "success") {

                    // Remove o Agent da lista exibida na tela.
                    setAgents((agentsAtuais) =>
                        agentsAtuais.filter(
                            (agent) => agent.agent_id !== agentId
                        )
                    );

                } else {

                    // Caso o backend retorne erro.
                    alert(
                        response.data.message ||
                        "Não foi possível excluir o Agent."
                    );
                }

            } catch (err) {

                // Mostra o erro no console para diagnóstico.
                console.error(
                    "Erro ao excluir Agent:",
                    err
                );

                alert(
                    "Não foi possível excluir o Agent."
                );
            }
        };
    // ========================================================
    // INTERFACE
    // ========================================================

    return (

        <div>

            {/* Título da página. */}
            <h1>Agents</h1>

            {/* ====================================================
                CADASTRAR AGENT
                ==================================================== */}

            <section>

                <h2>
                    Cadastrar Agent
                </h2>

                <input
                    type="text"
                    placeholder="ID do Agent"
                    value={newAgent.agent_id}
                    disabled={creatingAgent}
                    onChange={(event) =>
                        setNewAgent({
                            ...newAgent,
                            agent_id: event.target.value
                        })
                    }
                />

                <input
                    type="text"
                    placeholder="Nome"
                    value={newAgent.name}
                    disabled={creatingAgent}
                    onChange={(event) =>
                        setNewAgent({
                            ...newAgent,
                            name: event.target.value
                        })
                    }
                />

                <input
                    type="text"
                    placeholder="Host / IP"
                    value={newAgent.host}
                    disabled={creatingAgent}
                    onChange={(event) =>
                        setNewAgent({
                            ...newAgent,
                            host: event.target.value
                        })
                    }
                />

                <input
                    type="number"
                    placeholder="Porta"
                    value={newAgent.port}
                    disabled={creatingAgent}
                    onChange={(event) =>
                        setNewAgent({
                            ...newAgent,
                            port: event.target.value
                        })
                    }
                />

                <input
                    type="text"
                    placeholder="Diretório dos robôs"
                    value={newAgent.rpa_directory}
                    disabled={creatingAgent}
                    onChange={(event) =>
                        setNewAgent({
                            ...newAgent,
                            rpa_directory: event.target.value
                        })
                    }
                />

                <button
                    onClick={cadastrarAgent}
                    disabled={creatingAgent}
                >
                    {creatingAgent
                        ? "Cadastrando..."
                        : "Cadastrar Agent"}
                </button>

            </section>


            {/* ====================================================
                CARREGAMENTO
                ==================================================== */}

            {loading && (
                <p>
                    Carregando Agents...
                </p>
            )}


            {/* ====================================================
                ERRO
                ==================================================== */}

            {error && (
                <p>
                    {error}
                </p>
            )}


            {/* ====================================================
                LISTA DE AGENTS
                ==================================================== */}

            {!loading && !error && (

                <section>

                    <h2>
                        Agents cadastrados
                    </h2>


                    {agents.length === 0 ? (

                        // Nenhum Agent foi cadastrado ainda.
                        <p>
                            Nenhum Agent cadastrado.
                        </p>

                    ) : (

                        <div>

                            {agents.map((agent) => (

                                <div key={agent.agent_id}>

                                    {/* Nome do Agent. */}
                                    <h3>
                                        {agent.name}
                                    </h3>


                                    {/* Identificador do Agent. */}
                                    <p>
                                        <strong>
                                            ID:
                                        </strong>{" "}

                                        {agent.agent_id}
                                    </p>


                                    {/* Endereço do Agent. */}
                                    <p>
                                        <strong>
                                            Host:
                                        </strong>{" "}

                                        {agent.host}
                                    </p>


                                    {/* Porta utilizada pelo Agent. */}
                                    <p>
                                        <strong>
                                            Porta:
                                        </strong>{" "}

                                        {agent.port}
                                    </p>


                                    {/* Status atual do Agent. */}
                                    <p>
                                        <strong>
                                            Status:
                                        </strong>{" "}

                                        {agent.status}
                                    </p>


                                    {/* Diretório onde os robôs são armazenados. */}
                                    <p>
                                        <strong>
                                            Diretório:
                                        </strong>{" "}

                                        {agent.rpa_directory || "-"}
                                    </p>

                                     {/* Botão para excluir o Agent. */}
                                    <button
                                        onClick={() =>
                                            excluirAgent(
                                                agent.agent_id,
                                                agent.name
                                            )
                                        }
                                    >
                                        Excluir
                                    </button>

                                </div>

                            ))}

                        </div>

                    )}

                </section>

            )}

        </div>

    );
}

export default Agents;
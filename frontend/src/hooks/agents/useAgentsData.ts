// ============================================================
// DUET CORE - AGENTS - DATA HOOK
// ============================================================
//
// Hook responsável pela camada operacional da área de
// Devices/Agents.
//
// Responsabilidade:
// - carregar os Agents cadastrados;
// - controlar loading e mensagens de erro;
// - controlar o formulário de cadastro;
// - cadastrar um novo Agent;
// - excluir um Agent;
// - baixar o pacote de instalação de um Agent.
//
// Integrações:
// - GET    /agents
// - POST   /agents
// - DELETE /agents/{agent_id}
// - GET    /agents/{agent_id}/download
//
// Este hook NÃO:
// - renderiza cards;
// - renderiza formulário;
// - define layout;
// - possui responsabilidade visual.
//
// O comportamento foi extraído de pages/Agents.tsx preservando
// os endpoints, mensagens e fluxo atualmente utilizados.
// ============================================================

import {
    useEffect,
    useState,
} from "react";

import api from "../../services/api";

import type {
    Agent,
    NewAgentForm,
} from "../../types/agents";


// ============================================================
// HOOK
// ============================================================

export function useAgentsData() {

    // ========================================================
    // AGENTS
    // ========================================================

    const [
        agents,
        setAgents,
    ] = useState<Agent[]>([]);


    // ========================================================
    // CARREGAMENTO / ERRO
    // ========================================================

    const [
        loading,
        setLoading,
    ] = useState(true);


    const [
        error,
        setError,
    ] = useState("");


    // ========================================================
    // NOVO AGENT
    // ========================================================
    //
    // A porta continua sendo o único parâmetro informado
    // pelo usuário através da interface.
    // ========================================================

    const [
    newAgent,
    setNewAgent,
] = useState<NewAgentForm>({
    port: "",

    // Novos Devices começam classificados como
    // Desenvolvimento / Homologação.
    environment: "development",
});


    const [
        creatingAgent,
        setCreatingAgent,
    ] = useState(false);


    // ========================================================
    // BUSCAR AGENTS
    // ========================================================
    //
    // GET /agents
    //
    // Mantém o mesmo comportamento da página original:
    // a consulta é executada uma vez quando a feature monta.
    // ========================================================

    useEffect(() => {

        api
            .get("/agents")

            .then((response) => {

                // Guarda os Agents retornados pelo backend.
                setAgents(
                    response.data.agents
                );
            })

            .catch((err) => {

                console.error(
                    "Erro ao buscar Agents:",
                    err
                );


                setError(
                    "Não foi possível carregar os Agents."
                );
            })

            .finally(() => {

                setLoading(
                    false
                );
            });

    }, []);


    // ========================================================
    // CADASTRAR AGENT
    // ========================================================

    const cadastrarAgent =
        async () => {

            // ====================================================
            // VALIDAÇÃO
            // ====================================================
            //
            // A porta continua sendo o único campo obrigatório
            // informado pelo usuário.
            // ====================================================

            if (
                !newAgent.port.trim()
            ) {

                setError(
                    "Preencha a porta de comunicação."
                );


                return;
            }


            try {

                setCreatingAgent(
                    true
                );


                setError("");


                // =================================================
                // CRIAR AGENT
                // =================================================
                //
                // O backend continua responsável por gerar:
                // - agent_id;
                // - agent_token.
                //
                // O diretório-base permanece fixo em C:\RPA-Agent.
                // =================================================

                const response =
                    await api.post(
                        "/agents",
                        {
                            port:
                                Number(
                                    newAgent.port
                                ),
                                environment:
                                    newAgent.environment,

                            rpa_directory:
                                "C:\\RPA-Agent",
                        }
                    );


                // =================================================
                // VALIDAR RESPOSTA
                // =================================================

                if (
                    response.data.status !==
                    "success"
                ) {

                    setError(
                        response.data.message ||
                        "Não foi possível cadastrar o Agent."
                    );


                    return;
                }


                // =================================================
                // ATUALIZAR LISTA LOCAL
                // =================================================

                setAgents(
                    (agentsAtuais) => [
                        ...agentsAtuais,
                        response.data.agent,
                    ]
                );


                // =================================================
                // LIMPAR FORMULÁRIO
                // =================================================

                setNewAgent({
                    port: "",
                    environment: "development",
                });

            } catch (err: any) {

                console.error(
                    "Erro ao cadastrar Agent:",
                    err
                );


                console.error(
                    "Resposta da API:",
                    err.response?.data
                );


                setError(
                    err.response?.data?.detail ||
                    err.response?.data?.message ||
                    "Não foi possível cadastrar o Agent."
                );

            } finally {

                setCreatingAgent(
                    false
                );
            }
        };

    



    // ========================================================
    // ALTERAR AMBIENTE DO AGENT
    // ========================================================
    //
    // PATCH /agents/{agent_id}/environment
    //
    // A alteração é persistida pelo Control Room.
    // O frontend apenas atualiza sua cópia local após a
    // confirmação de sucesso da API.
    // ========================================================

    const alterarAmbienteAgent =
        async (
            agentId: string,
            environment:
                "development" |
                "production"
        ) => {

            try {

                setError("");

                const response =
                    await api.patch(
                        `/agents/${agentId}/environment`,
                        {
                            environment,
                        }
                    );


                if (
                    response.data.status !==
                    "success"
                ) {

                    setError(
                        response.data.message ||
                        "Não foi possível alterar o ambiente do Device."
                    );

                    return;
                }


                // Atualiza somente o Agent modificado,
                // sem recarregar toda a página.
                setAgents(
                    (agentsAtuais) =>
                        agentsAtuais.map(
                            (agent) =>
                                agent.agent_id === agentId
                                    ? {
                                        ...agent,
                                        environment,
                                    }
                                    : agent
                        )
                );

            } catch (err: any) {

                console.error(
                    "Erro ao alterar ambiente do Agent:",
                    err
                );

                setError(
                    err.response?.data?.detail ||
                    err.response?.data?.message ||
                    "Não foi possível alterar o ambiente do Device."
                );
            }
        };
    // ========================================================
    // EXCLUIR AGENT
    // ========================================================

    const excluirAgent =
        async (
            agentId: string,
            agentName: string
        ) => {

            // Mantém exatamente a confirmação existente.
            const confirmar =
                window.confirm(
                    `Deseja realmente excluir o Agent "${agentName}"?`
                );


            if (!confirmar) {
                return;
            }


            try {

                const response =
                    await api.delete(
                        `/agents/${agentId}`
                    );


                if (
                    response.data.status ===
                    "success"
                ) {

                    // Remove somente o Agent excluído da
                    // lista atualmente exibida.
                    setAgents(
                        (agentsAtuais) =>
                            agentsAtuais.filter(
                                (agent) =>
                                    agent.agent_id !==
                                    agentId
                            )
                    );

                } else {

                    alert(
                        response.data.message ||
                        "Não foi possível excluir o Agent."
                    );
                }

            } catch (err) {

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
    // BAIXAR AGENT
    // ========================================================
    //
    // Solicita ao Control Room o pacote específico do Agent,
    // cria uma URL temporária no navegador e dispara o download.
    // ========================================================

    const baixarAgent =
        async (
            agentId: string
        ) => {

            try {

                // =================================================
                // SOLICITAR PACOTE
                // =================================================

                const response =
                    await api.get(
                        `/agents/${agentId}/download`,
                        {
                            responseType:
                                "blob",
                        }
                    );


                // =================================================
                // CRIAR BLOB
                // =================================================

                const blob =
                    new Blob(
                        [
                            response.data,
                        ],
                        {
                            type:
                                "application/zip",
                        }
                    );


                const url =
                    window.URL.createObjectURL(
                        blob
                    );


                // =================================================
                // DISPARAR DOWNLOAD
                // =================================================

                const link =
                    document.createElement(
                        "a"
                    );


                link.href =
                    url;


                // Mantém exatamente o nome atualmente utilizado
                // pela página original.
                link.download =
                    `RPA-Agent-${agentId}.exe`;


                document.body.appendChild(
                    link
                );


                link.click();


                // =================================================
                // LIMPEZA
                // =================================================

                link.remove();


                window.URL.revokeObjectURL(
                    url
                );

            } catch (err) {

                console.error(
                    "Erro ao baixar Agent:",
                    err
                );


                alert(
                    "Não foi possível baixar o Agent."
                );
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        agents,
        loading,
        error,

        newAgent,
        setNewAgent,

        creatingAgent,
        alterarAmbienteAgent,
        cadastrarAgent,
        excluirAgent,
        baixarAgent,
    };
}
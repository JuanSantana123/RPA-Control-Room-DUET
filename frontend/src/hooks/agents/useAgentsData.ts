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
    useRef,
    useState,
} from "react";

import api from "../../services/api";

import type {
    Agent,
    NewAgentForm,
} from "../../types/agents";
import { getApiErrorDetails, getApiErrorMessage } from "../../utils/apiErrors";
import { useInteraction } from "../../context/useInteraction";
import { usePollingTask } from "../async/usePollingTask";


// ============================================================
// HOOK
// ============================================================

export function useAgentsData() {

    const { confirm, notify } = useInteraction();

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

    const clearError = () => setError("");
    const [updatingAvailability, setUpdatingAvailability] = useState<string | null>(null);
    const [refreshing, setRefreshing] = useState(false);
    const [lastUpdated, setLastUpdated] = useState<Date | null>(null);
    const requestSequence = useRef(0);


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
    // Mantém dados úteis durante falhas de atualização, cancela requisições
    // obsoletas e pausa o polling quando a aba não está visível.
    // ========================================================

    const carregarAgentsComSinal = async (
        background = false,
        signal?: AbortSignal,
    ) => {
        const requestId = ++requestSequence.current;
        if (background) setRefreshing(true);

        try {
            const response = await api.get("/agents", { signal });
            if (requestId !== requestSequence.current) return;

            setAgents(response.data.agents ?? []);
            setLastUpdated(new Date());
            setError("");
        } catch (err) {
            if (signal?.aborted || requestId !== requestSequence.current) return;
            setError(getApiErrorMessage(
                err,
                agents.length > 0
                    ? "Não foi possível atualizar a saúde dos Devices. Os últimos dados válidos foram preservados."
                    : "Não foi possível carregar os Devices.",
            ));
        } finally {
            if (!signal?.aborted && requestId === requestSequence.current) {
                setLoading(false);
                setRefreshing(false);
            }
        }
    };

    usePollingTask(
        (signal) => carregarAgentsComSinal(agents.length > 0, signal),
        { intervalMs: 10_000 },
    );

    const carregarAgents = () => carregarAgentsComSinal(true);


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

            const port = Number(newAgent.port);

            if (!newAgent.port.trim()) {

                setError(
                    "Preencha a porta de comunicação."
                );


                return;
            }

            if (!Number.isInteger(port) || port < 1 || port > 65535) {
                setError(
                    "Informe uma porta inteira entre 1 e 65535. Exemplo: 8000."
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
                            port,
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

                    const backendMessage =
                        typeof response.data.message === "string"
                            ? response.data.message.trim()
                            : "";

                    const message = response.data.error_code === "agent_token_key_unavailable"
                        ? backendMessage
                        : backendMessage === "Não foi possível criar o Agent."
                            ? "O Control Room recusou o cadastro sem detalhar a causa. Confirme se DUET_AGENT_TOKEN_KEY está configurada e reinicie o serviço; se ela já estiver configurada, consulte o evento agent_creation_failed nos logs."
                            : backendMessage || "Não foi possível cadastrar o dispositivo. O Control Room não retornou um motivo; consulte os logs do sistema e tente novamente.";

                    setError(
                        message
                    );


                    return;
                }


                // =================================================
                // ATUALIZAR LISTA LOCAL
                // =================================================

                await carregarAgentsComSinal(true);


                // =================================================
                // LIMPAR FORMULÁRIO
                // =================================================

                setNewAgent({
                    port: "",
                    environment: "development",
                });

            } catch (err) {

                console.error(
                    "Erro ao cadastrar Agent:",
                    err
                );


                setError(getApiErrorDetails(
                    err,
                    "O dispositivo não pôde ser cadastrado. Verifique a configuração do Control Room e tente novamente."
                ).message);

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

            } catch (err) {

                console.error(
                    "Erro ao alterar ambiente do Agent:",
                    err
                );

                setError(getApiErrorMessage(
                    err,
                    "Não foi possível alterar o ambiente do dispositivo."
                ));
            }
        };



    
    // ========================================================
    // ALTERAR DISPLAY DO AGENT
    // ========================================================
    //
    // PATCH /agents/{agent_id}/display
    //
    // Persiste no Control Room a configuração de display
    // desejada para este Device.
    //
    // A aplicação física da resolução pelo RPA-Agent será
    // integrada posteriormente.
    // ========================================================

    const alterarDisplayAgent =
        async (
            agentId: string,
            width: number,
            height: number,
            scale: number
        ) => {

            try {

                setError("");


                const response =
                    await api.patch(
                        `/agents/${agentId}/display`,
                        {
                            width,
                            height,
                            scale,
                        }
                    );


                if (
                    response.data.status !==
                    "success"
                ) {

                    setError(
                        response.data.message ||
                        "Não foi possível alterar o display do Device."
                    );

                    return;
                }


                // Atualiza somente o Device modificado.
                //
                // Mantemos a telemetria atual intacta porque
                // display_current representa o estado REAL da
                // máquina, e não o valor que acabamos de desejar.
                setAgents(
                    (agentsAtuais) =>
                        agentsAtuais.map(
                            (agent) =>
                                agent.agent_id === agentId
                                    ? {
                                        ...agent,
                                        display_width: width,
                                        display_height: height,
                                        display_scale: scale,
                                    }
                                    : agent
                        )
                );

            } catch (err) {

                console.error(
                    "Erro ao alterar display do Agent:",
                    err
                );


                setError(getApiErrorMessage(
                    err,
                    "Não foi possível alterar a configuração de display do dispositivo."
                ));
            }
        };

    const alterarDisponibilidadeAgent = async (
        agentId: string,
        acceptingWork: boolean,
        reason: string | null,
    ) => {
        try {
            setError("");
            setUpdatingAvailability(agentId);
            const response = await api.patch(`/agents/${agentId}/availability`, {
                accepting_work: acceptingWork,
                reason,
            });

            if (response.data.status !== "success") {
                setError(response.data.message || "Não foi possível alterar a disponibilidade do Device.");
                return false;
            }

            const updatedAgent = response.data.agent as Agent;
            setAgents((current) => current.map((agent) => (
                agent.agent_id === agentId ? updatedAgent : agent
            )));
            notify({
                tone: "success",
                title: acceptingWork ? "Device liberado" : "Manutenção ativada",
                message: response.data.message,
            });
            return true;
        } catch (err) {
            setError(getApiErrorMessage(
                err,
                "Não foi possível alterar a disponibilidade do Device.",
            ));
            return false;
        } finally {
            setUpdatingAvailability(null);
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
            const confirmar = await confirm({
                title: `Excluir o Device “${agentName}”?`,
                description: "O Device deixará de receber novas automações e será removido do gerenciamento do Control Room.",
                detail: "Confirme que não existem execuções em andamento nem agendamentos dependentes deste Device.",
                confirmLabel: "Excluir Device",
                tone: "danger",
            });


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

                    setError(
                        response.data.message ||
                        "Não foi possível excluir o dispositivo."
                    );
                }

            } catch (err) {

                console.error(
                    "Erro ao excluir Agent:",
                    err
                );


                setError(getApiErrorMessage(
                    err,
                    "Não foi possível excluir o dispositivo."
                ));
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


                setError(getApiErrorMessage(
                    err,
                    "Não foi possível gerar o instalador deste dispositivo."
                ));
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        agents,
        loading,
        error,
        clearError,

        newAgent,
        setNewAgent,

        creatingAgent,
        updatingAvailability,
        refreshing,
        lastUpdated,
        carregarAgents,
        alterarAmbienteAgent,
        alterarDisponibilidadeAgent,
        alterarDisplayAgent,
        cadastrarAgent,
        excluirAgent,
        baixarAgent,
    };
}

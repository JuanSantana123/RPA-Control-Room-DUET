import { useEffect, useState } from "react";

import api from "../services/api";

// ============================================================
// TIPOS
// ============================================================

// Representa um robô disponível para agendamento.
interface RobotOption {
    id: number;
    name: string;
}

// Representa um Agent disponível para agendamento.
interface AgentOption {
    agent_id: string;
    name: string;
    status: string;
}

// Representa um agendamento retornado pela API.
interface Schedule {
    id: number;

    robot_id: number;
    robot_name: string;

    agent_id: string | null;
    agent_name: string;

    tipo: string;

    data_inicio: string | null;
    horario: string;

    dias_semana: string | null;

    intervalo_ativo: boolean;
    intervalo_valor: number | null;
    intervalo_unidade: string | null;
    horario_fim: string | null;

    proxima_execucao: string | null;

    ativo: boolean;
}


// ============================================================
// PÁGINA DE AGENDAMENTOS
// ============================================================

function Schedules() {

    // ========================================================
    // LISTA DE AGENDAMENTOS
    // ========================================================

    const [schedules, setSchedules] =
        useState<Schedule[]>([]);

    // ========================================================
    // ESTADO DO MODAL
    // ========================================================

    const [modalAberto, setModalAberto] =
        useState(false);

    // Guarda o ID quando estamos editando.
    //
    // null = novo agendamento.
    const [editandoId, setEditandoId] =
        useState<number | null>(null);

    // ========================================================
    // OPÇÕES DE ROBÔS E AGENTS
    // ========================================================

    const [robots, setRobots] =
        useState<RobotOption[]>([]);

    const [agents, setAgents] =
        useState<AgentOption[]>([]);

    // ========================================================
    // FORMULÁRIO
    // ========================================================

    const [robotId, setRobotId] =
        useState("");

    const [agentId, setAgentId] =
        useState("");

    const [tipo, setTipo] =
        useState("once");

    const [dataInicio, setDataInicio] =
        useState("");

    const [horario, setHorario] =
        useState("08:00");

    const [diasSemana, setDiasSemana] =
        useState<string[]>([]);

    const [intervaloAtivo, setIntervaloAtivo] =
        useState(false);

    const [intervaloValor, setIntervaloValor] =
        useState(1);

    const [intervaloUnidade, setIntervaloUnidade] =
        useState("minutes");

    const [horarioFim, setHorarioFim] =
        useState("");

    // ========================================================
    // CONTROLE DE CARREGAMENTO
    // ========================================================

    const [loading, setLoading] =
        useState(true);

    const [salvando, setSalvando] =
        useState(false);

    const [error, setError] =
        useState("");

    // ========================================================
    // CARREGAR AGENDAMENTOS
    // ========================================================
    //
    // Equivalente ao:
    //
    // GET /api/schedules
    //
    // do schedules.html.
    // ========================================================

    const carregarAgendamentos = async () => {

        try {

            const response =
                await api.get("/api/schedules");

            const data =
                response.data;

            if (
                response.status !== 200 ||
                data.status !== "success"
            ) {

                console.error(
                    "Erro ao carregar agendamentos:",
                    data
                );

                return;
            }

            setSchedules(
                data.schedules || []
            );

            setError("");

        } catch (err) {

            console.error(
                "Erro ao carregar agendamentos:",
                err
            );

            setError(
                "Não foi possível carregar os agendamentos."
            );

        } finally {

            setLoading(false);
        }
    };


    // ========================================================
    // CARREGAR ROBÔS E AGENTS
    // ========================================================
    //
    // Equivalente ao:
    //
    // GET /api/schedules/options
    //
    // do schedules.html.
    // ========================================================

    const carregarOpcoesAgendamento =
        async () => {

            try {

                const response =
                    await api.get(
                        "/api/schedules/options"
                    );

                const data =
                    response.data;

                if (
                    response.status !== 200 ||
                    data.status !== "success"
                ) {

                    window.alert(
                        data.message ||
                        "Não foi possível carregar as opções."
                    );

                    return;
                }

                // Guarda os robôs disponíveis.
                setRobots(
                    data.robots || []
                );

                // Guarda os Agents disponíveis.
                setAgents(
                    data.agents || []
                );

            } catch (err) {

                console.error(
                    "Erro ao carregar opções:",
                    err
                );

                window.alert(
                    "Erro ao carregar robôs e Agents."
                );
            }
        };


    // ========================================================
    // PRIMEIRA CARGA
    // ========================================================

    useEffect(() => {

        carregarAgendamentos();

    }, []);


    // ========================================================
    // ATUALIZAÇÃO AUTOMÁTICA
    // ========================================================
    //
    // Mantém o mesmo comportamento do schedules.html:
    // a lista é atualizada periodicamente.
    //
    // Como o HTML original não definia um setInterval
    // explicitamente para schedules, usamos 5 segundos
    // para manter a tela sincronizada.
    // ========================================================

    useEffect(() => {

        const intervalo =
            setInterval(() => {

                carregarAgendamentos();

            }, 5000);

        return () => {

            clearInterval(intervalo);

        };

    }, []);


    // ========================================================
    // ABRIR NOVO AGENDAMENTO
    // ========================================================

    const novoAgendamento = async () => {

        // Primeiro carregamos os robôs e Agents.
        await carregarOpcoesAgendamento();

        // Limpa o estado de edição.
        setEditandoId(null);

        // Limpa o robô selecionado.
        setRobotId("");

        // Agent automático.
        setAgentId("");

        // Tipo padrão.
        setTipo("once");

        // ====================================================
        // DATA ATUAL
        // ====================================================

        const hoje =
            new Date();

        const ano =
            hoje.getFullYear();

        const mes =
            String(
                hoje.getMonth() + 1
            ).padStart(2, "0");

        const dia =
            String(
                hoje.getDate()
            ).padStart(2, "0");

        setDataInicio(
            `${ano}-${mes}-${dia}`
        );

        // Horário padrão utilizado no HTML antigo.
        setHorario("08:00");

        // Limpa dias da semana.
        setDiasSemana([]);

        // Desativa intervalo.
        setIntervaloAtivo(false);

        // Valores padrão do intervalo.
        setIntervaloValor(1);

        setIntervaloUnidade("minutes");

        setHorarioFim("");

        // Abre o modal.
        setModalAberto(true);
    };


    // ========================================================
    // FECHAR MODAL
    // ========================================================

    const fecharModal = () => {

        setModalAberto(false);

        setEditandoId(null);
    };


    // ========================================================
    // ALTERAR DIA DA SEMANA
    // ========================================================

    const alterarDiaSemana = (
        dia: string
    ) => {

        setDiasSemana((diasAtuais) => {

            // Se o dia já estiver selecionado,
            // removemos.
            if (
                diasAtuais.includes(dia)
            ) {

                return diasAtuais.filter(
                    (item) => item !== dia
                );
            }

            // Caso contrário, adicionamos.
            return [
                ...diasAtuais,
                dia
            ];
        });
    };


    // ========================================================
    // ALTERAR TIPO
    // ========================================================

    const alterarTipoAgendamento = (
        novoTipo: string
    ) => {

        setTipo(novoTipo);

        // Quando não for semanal,
        // os dias da semana deixam de ser utilizados.
        if (novoTipo !== "weekly") {

            setDiasSemana([]);
        }

        // Quando for "once", intervalo não pode ser utilizado.
        if (novoTipo === "once") {

            setIntervaloAtivo(false);
        }
    };


    // ========================================================
    // SALVAR AGENDAMENTO
    // ========================================================
    //
    // POST  /api/schedules
    //
    // ou
    //
    // PUT /api/schedules/{id}
    //
    // dependendo se é criação ou edição.
    // ========================================================

    const salvarAgendamento = async () => {

        // ====================================================
        // VALIDAÇÕES
        // ====================================================

        if (!robotId) {

            window.alert(
                "Selecione um robô."
            );

            return;
        }

        if (!dataInicio) {

            window.alert(
                "Informe a data de início."
            );

            return;
        }

        if (!horario) {

            window.alert(
                "Informe o horário."
            );

            return;
        }

        // ====================================================
        // VALIDAÇÃO DOS DIAS
        // ====================================================

        let diasSemanaValor:
            string | null = null;

        if (tipo === "weekly") {

            if (
                diasSemana.length === 0
            ) {

                window.alert(
                    "Selecione pelo menos um dia da semana."
                );

                return;
            }

            diasSemanaValor =
                diasSemana.join(",");
        }

        // ====================================================
        // INTERVALO
        // ====================================================

        const intervaloValorEnvio =
            intervaloAtivo
                ? intervaloValor
                : null;

        const intervaloUnidadeEnvio =
            intervaloAtivo
                ? intervaloUnidade
                : null;

        const horarioFimEnvio =
            intervaloAtivo
                ? horarioFim
                : null;

        // ====================================================
        // PAYLOAD
        // ====================================================

        const payload = {

            robot_id: Number(robotId),

            agent_id:
                agentId || null,

            tipo: tipo,

            data_inicio:
                `${dataInicio}T${horario}`,

            horario: horario,

            dias_semana:
                diasSemanaValor,

            intervalo_ativo:
                intervaloAtivo,

            intervalo_valor:
                intervaloValorEnvio,

            intervalo_unidade:
                intervaloUnidadeEnvio,

            horario_fim:
                horarioFimEnvio
        };

        try {

            setSalvando(true);

            // ====================================================
            // CRIAÇÃO
            // ====================================================

            if (editandoId === null) {

                const response =
                    await api.post(
                        "/api/schedules",
                        payload
                    );

                const data =
                    response.data;

                if (
                    response.status !== 200 ||
                    data.status !== "success"
                ) {

                    window.alert(
                        data.message ||
                        "Não foi possível criar o agendamento."
                    );

                    return;
                }

                window.alert(
                    "Agendamento criado com sucesso!"
                );

            }

            // ====================================================
            // EDIÇÃO
            // ====================================================

            else {

                const response =
                    await api.put(
                        `/api/schedules/${editandoId}`,
                        payload
                    );

                const data =
                    response.data;

                if (
                    response.status !== 200 ||
                    data.status !== "success"
                ) {

                    window.alert(
                        data.message ||
                        "Não foi possível atualizar o agendamento."
                    );

                    return;
                }

                window.alert(
                    "Agendamento atualizado com sucesso!"
                );
            }

            // Fecha o modal.
            fecharModal();

            // Atualiza a tabela.
            await carregarAgendamentos();

        } catch (err) {

            console.error(
                "Erro ao salvar agendamento:",
                err
            );

            window.alert(
                "Erro ao comunicar com o Control Room."
            );

        } finally {

            setSalvando(false);
        }
    };


    // ========================================================
    // EDITAR AGENDAMENTO
    // ========================================================

    const editarAgendamento = async (
        id: number
    ) => {

        try {

            // Busca os dados completos do agendamento.
            const response =
                await api.get(
                    `/api/schedules/${id}`
                );

            const data =
                response.data;

            if (
                response.status !== 200 ||
                data.status !== "success"
            ) {

                window.alert(
                    data.message ||
                    "Erro ao carregar o agendamento."
                );

                return;
            }

            const schedule =
                data.schedule;

            // Guarda o ID que está sendo editado.
            setEditandoId(id);

            // Carrega as opções do formulário.
            await carregarOpcoesAgendamento();

            // ====================================================
            // PREENCHER FORMULÁRIO
            // ====================================================

            setRobotId(
                String(schedule.robot_id)
            );

            setAgentId(
                schedule.agent_id || ""
            );

            setTipo(
                schedule.tipo
            );

            setDataInicio(
                schedule.data_inicio
                    ? schedule.data_inicio.substring(0, 10)
                    : ""
            );

            setHorario(
                schedule.horario || ""
            );

            // ====================================================
            // DIAS DA SEMANA
            // ====================================================

            setDiasSemana(
                schedule.dias_semana
                    ? schedule.dias_semana
                        .split(",")
                        .filter(Boolean)
                    : []
            );

            // ====================================================
            // INTERVALO
            // ====================================================

            setIntervaloAtivo(
                Boolean(
                    schedule.intervalo_ativo
                )
            );

            setIntervaloValor(
                schedule.intervalo_valor || 1
            );

            setIntervaloUnidade(
                schedule.intervalo_unidade ||
                "minutes"
            );

            setHorarioFim(
                schedule.horario_fim || ""
            );

            // Abre o modal.
            setModalAberto(true);

        } catch (err) {

            console.error(
                "Erro ao carregar agendamento:",
                err
            );

            window.alert(
                "Erro ao carregar o agendamento."
            );
        }
    };


    // ========================================================
    // EXCLUIR AGENDAMENTO
    // ========================================================

    const excluirAgendamento = async (
        id: number
    ) => {

        // Solicita confirmação.
        const confirmar =
            window.confirm(
                "Tem certeza que deseja excluir este agendamento?"
            );

        if (!confirmar) {
            return;
        }

        try {

            const response =
                await api.delete(
                    `/api/schedules/${id}`
                );

            const data =
                response.data;

            if (
                response.status !== 200 ||
                data.status !== "success"
            ) {

                window.alert(
                    data.message ||
                    "Não foi possível excluir o agendamento."
                );

                return;
            }

            // Atualiza a lista após exclusão.
            await carregarAgendamentos();

        } catch (err) {

            console.error(
                "Erro ao excluir agendamento:",
                err
            );

            window.alert(
                "Erro ao comunicar com o Control Room."
            );
        }
    };


    // ========================================================
    // ALTERAR STATUS
    // ========================================================

    const alterarStatusAgendamento =
        async (
            id: number,
            ativo: boolean
        ) => {

            try {

                const response =
                    await api.put(
                        `/api/schedules/${id}/status`,
                        null,
                        {
                            params: {
                                ativo: ativo
                            }
                        }
                    );

                const data =
                    response.data;

                if (
                    response.status !== 200 ||
                    data.status !== "success"
                ) {

                    window.alert(
                        data.message ||
                        "Não foi possível alterar o status."
                    );

                    return;
                }

                // Atualiza a tabela.
                await carregarAgendamentos();

            } catch (err) {

                console.error(
                    "Erro ao alterar status:",
                    err
                );

                window.alert(
                    "Erro ao comunicar com o Control Room."
                );
            }
        };


    // ========================================================
    // FORMATAR TIPO
    // ========================================================

    const formatarTipo = (
        tipoAgendamento: string
    ) => {

        const tipos: Record<string, string> = {

            once: "Uma vez",

            daily: "Diário",

            weekly: "Semanal",

            monthly: "Mensal"
        };

        return (
            tipos[tipoAgendamento] ||
            tipoAgendamento
        );
    };


    // ========================================================
    // FORMATAR DATA
    // ========================================================

    const formatarData = (
        data: string | null
    ) => {

        if (!data) {
            return "-";
        }

        return new Date(
            data
        ).toLocaleString(
            "pt-BR"
        );
    };


    // ========================================================
    // INTERFACE
    // ========================================================

    return (

        <div>

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <section>

                <div>

                    <div>

                        <h1>
                            Agendamentos
                        </h1>

                        <p>
                            Robôs programados para execução automática
                        </p>

                    </div>

                    {/* Botão para criar novo agendamento. */}
                    <button
                        type="button"
                        onClick={novoAgendamento}
                    >
                        + Novo Agendamento
                    </button>

                </div>

            </section>


            {/* ==================================================
                ERRO
                ================================================== */}

            {error && (

                <p>
                    {error}
                </p>

            )}


            {/* ==================================================
                TABELA
                ================================================== */}

            <section>

                <table>

                    <thead>

                        <tr>

                            <th>
                                Robô
                            </th>

                            <th>
                                Agent
                            </th>

                            <th>
                                Tipo
                            </th>

                            <th>
                                Horário
                            </th>

                            <th>
                                Próxima execução
                            </th>

                            <th>
                                Status
                            </th>

                            <th>
                                Ações
                            </th>

                        </tr>

                    </thead>


                    <tbody>

                        {loading && (

                            <tr>

                                <td colSpan={7}>
                                    Carregando agendamentos...
                                </td>

                            </tr>

                        )}


                        {!loading &&
                            schedules.length === 0 && (

                                <tr>

                                    <td colSpan={7}>
                                        Nenhum agendamento cadastrado.
                                    </td>

                                </tr>

                            )}


                        {!loading &&
                            schedules.map(
                                (schedule) => (

                                    <tr
                                        key={schedule.id}
                                    >

                                        {/* ROBÔ */}

                                        <td>
                                            {schedule.robot_name}
                                        </td>


                                        {/* AGENT */}

                                        <td>
                                            {schedule.agent_name}
                                        </td>


                                        {/* TIPO */}

                                        <td>
                                            {formatarTipo(
                                                schedule.tipo
                                            )}
                                        </td>


                                        {/* HORÁRIO */}

                                        <td>

                                            {schedule.horario}

                                            {schedule.intervalo_ativo && (

                                                <small
                                                    style={{
                                                        display: "block"
                                                    }}
                                                >
                                                    A cada{" "}
                                                    {
                                                        schedule.intervalo_valor
                                                    }{" "}

                                                    {schedule.intervalo_unidade ===
                                                    "minutes"
                                                        ? "minuto(s)"
                                                        : "hora(s)"
                                                    }

                                                    {" "}até{" "}

                                                    {
                                                        schedule.horario_fim
                                                    }

                                                </small>

                                            )}

                                        </td>


                                        {/* PRÓXIMA EXECUÇÃO */}

                                        <td>
                                            {schedule.proxima_execucao
                                                ? formatarData(
                                                    schedule.proxima_execucao
                                                )
                                                : "-"
                                            }
                                        </td>


                                        {/* STATUS */}

                                        <td>

                                            {schedule.ativo
                                                ? "● Ativo"
                                                : "● Inativo"
                                            }

                                        </td>


                                        {/* AÇÕES */}

                                        <td>

                                            <button
                                                type="button"
                                                onClick={() => {
                                                    editarAgendamento(
                                                        schedule.id
                                                    );
                                                }}
                                            >
                                                Editar
                                            </button>


                                            {" "}


                                            <button
                                                type="button"
                                                onClick={() => {
                                                    alterarStatusAgendamento(
                                                        schedule.id,
                                                        !schedule.ativo
                                                    );
                                                }}
                                            >
                                                {schedule.ativo
                                                    ? "Desativar"
                                                    : "Ativar"
                                                }
                                            </button>


                                            {" "}


                                            <button
                                                type="button"
                                                onClick={() => {
                                                    excluirAgendamento(
                                                        schedule.id
                                                    );
                                                }}
                                            >
                                                Excluir
                                            </button>

                                        </td>

                                    </tr>

                                )
                            )}

                    </tbody>

                </table>

            </section>


            {/* ==================================================
                MODAL
                ================================================== */}

            {modalAberto && (

                <div
                    style={{
                        position: "fixed",
                        inset: 0,
                        background: "rgba(0, 0, 0, 0.55)",
                        display: "flex",
                        alignItems: "center",
                        justifyContent: "center",
                        zIndex: 1000,
                    }}
                >

                    <div
                        style={{
                            background: "white",
                            width: "500px",
                            maxWidth: "90%",
                            maxHeight: "90vh",
                            overflowY: "auto",
                            borderRadius: "10px",
                            padding: "25px",
                            boxShadow:
                                "0 10px 40px rgba(0,0,0,0.25)",
                        }}
                    >

                        {/* ==================================================
                            CABEÇALHO DO MODAL
                            ================================================== */}

                        <div
                            style={{
                                display: "flex",
                                justifyContent: "space-between",
                                alignItems: "center",
                                marginBottom: "20px",
                            }}
                        >

                            <div>

                                <h2
                                    style={{
                                        margin: 0
                                    }}
                                >
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
                                onClick={fecharModal}
                            >
                                ✕
                            </button>

                        </div>


                        {/* ==================================================
                            ROBÔ
                            ================================================== */}

                        <div>

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
                                style={{
                                    width: "100%"
                                }}
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

                        <div>

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
                                style={{
                                    width: "100%"
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
                                            {agent.name} ({agent.status})
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

                        <div>

                            <label>
                                Tipo de agendamento
                            </label>

                            <select
                                value={tipo}
                                onChange={(event) => {
                                    alterarTipoAgendamento(
                                        event.target.value
                                    );
                                }}
                                required
                                style={{
                                    width: "100%"
                                }}
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

                        <div>

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
                                style={{
                                    width: "100%"
                                }}
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

                                <div
                                    style={{
                                        display: "grid",
                                        gridTemplateColumns:
                                            "repeat(4, 1fr)",
                                        gap: "8px",
                                        marginTop: "10px",
                                    }}
                                >

                                    {[
                                        ["mon", "Segunda"],
                                        ["tue", "Terça"],
                                        ["wed", "Quarta"],
                                        ["thu", "Quinta"],
                                        ["fri", "Sexta"],
                                        ["sat", "Sábado"],
                                        ["sun", "Domingo"],
                                    ].map(
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
                                                        alterarDiaSemana(
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
                                        checked={
                                            intervaloAtivo
                                        }
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

                                <div
                                    style={{
                                        marginTop: "15px"
                                    }}
                                >

                                    <div>

                                        <label>
                                            Executar a cada
                                        </label>

                                        <input
                                            type="number"
                                            min="1"
                                            value={
                                                intervaloValor
                                            }
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
                                            value={
                                                intervaloUnidade
                                            }
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
                                            value={
                                                horarioFim
                                            }
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

                        <div>

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
                                style={{
                                    width: "100%"
                                }}
                            />

                        </div>


                        {/* ==================================================
                            BOTÕES
                            ================================================== */}

                        <div
                            style={{
                                display: "flex",
                                justifyContent: "flex-end",
                                gap: "10px",
                                marginTop: "25px",
                            }}
                        >

                            <button
                                type="button"
                                onClick={fecharModal}
                                disabled={salvando}
                            >
                                Cancelar
                            </button>


                            <button
                                type="button"
                                onClick={salvarAgendamento}
                                disabled={salvando}
                            >
                                {salvando
                                    ? "Salvando..."
                                    : editandoId === null
                                        ? "Salvar Agendamento"
                                        : "Atualizar Agendamento"
                                }
                            </button>

                        </div>

                    </div>

                </div>

            )}

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default Schedules;
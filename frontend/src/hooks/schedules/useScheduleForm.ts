// ============================================================
// DUET CORE - SCHEDULES - FORM HOOK
// ============================================================
//
// Hook responsável pelo ciclo completo do formulário de
// criação e edição de Agendamentos.
//
// Responsabilidade:
// - controlar abertura e fechamento do modal;
// - carregar Robots e Agents disponíveis;
// - inicializar um novo agendamento;
// - carregar um agendamento existente para edição;
// - controlar todos os campos do formulário;
// - controlar dias da semana;
// - aplicar as regras relacionadas ao tipo;
// - validar o formulário;
// - montar o payload esperado pelo Control Room;
// - criar ou atualizar o Schedule.
//
// Integrações:
// - GET  /schedules/options
// - GET  /schedules/{id}
// - POST /schedules
// - PUT  /schedules/{id}
//
// Este hook NÃO:
// - carrega a tabela de agendamentos;
// - executa polling;
// - exclui agendamentos;
// - ativa ou desativa agendamentos;
// - renderiza o modal.
//
// O callback onScheduleSaved é recebido da camada superior
// para atualizar a listagem depois de um POST/PUT concluído.
//
// As regras foram transportadas de pages/Schedules.tsx sem
// alteração do contrato funcional do Scheduler.
// ============================================================

import {
    useState,
} from "react";

import api from "../../services/api";
import { getApiErrorMessage } from "../../utils/apiErrors";

import type {
    AgentOption,
    RobotOption,
} from "../../types/schedules";

interface ScheduleOptionsResponse {
    status: "success" | "error";
    robots?: RobotOption[];
    agents?: AgentOption[];
    timezone?: string;
    message?: string;
}


// ============================================================
// PROPS DO HOOK
// ============================================================

interface UseScheduleFormProps {

    // Executado após criação/edição concluída com sucesso.
    // Na integração final receberá carregarAgendamentos().
    onScheduleSaved: () => void | Promise<void>;
}


// ============================================================
// HOOK
// ============================================================

export function useScheduleForm({
    onScheduleSaved,
}: UseScheduleFormProps) {

    // ========================================================
    // MODAL / EDIÇÃO
    // ========================================================

    const [
        modalAberto,
        setModalAberto,
    ] = useState(false);


    // null = criação.
    // number = edição do Schedule correspondente.
    const [
        editandoId,
        setEditandoId,
    ] = useState<number | null>(
        null
    );


    // ========================================================
    // OPÇÕES DE ROBOTS E AGENTS
    // ========================================================

    const [
        robots,
        setRobots,
    ] = useState<RobotOption[]>([]);


    const [
        agents,
        setAgents,
    ] = useState<AgentOption[]>([]);

    const [
        timezone,
        setTimezone,
    ] = useState("America/Sao_Paulo");


    // ========================================================
    // CAMPOS DO FORMULÁRIO
    // ========================================================

    const [
        robotId,
        setRobotId,
    ] = useState("");


    const [
        agentId,
        setAgentId,
    ] = useState("");


    const [
        tipo,
        setTipo,
    ] = useState("once");


    const [
        dataInicio,
        setDataInicio,
    ] = useState("");


    const [
        horario,
        setHorario,
    ] = useState("08:00");


    const [
        diasSemana,
        setDiasSemana,
    ] = useState<string[]>([]);


    const [
        intervaloAtivo,
        setIntervaloAtivo,
    ] = useState(false);


    const [
        intervaloValor,
        setIntervaloValor,
    ] = useState(1);


    const [
        intervaloUnidade,
        setIntervaloUnidade,
    ] = useState("minutes");


    const [
        horarioFim,
        setHorarioFim,
    ] = useState("");

    const [
        misfirePolicy,
        setMisfirePolicy,
    ] = useState<"run_once" | "skip">("run_once");

    const [
        misfireGraceSeconds,
        setMisfireGraceSeconds,
    ] = useState(300);


    // ========================================================
    // SALVAMENTO
    // ========================================================

    const [
        salvando,
        setSalvando,
    ] = useState(false);

    const [loadingOptions, setLoadingOptions] = useState(false);
    const [formError, setFormError] = useState("");
    const [successMessage, setSuccessMessage] = useState("");


    // ========================================================
    // CARREGAR ROBOTS E AGENTS
    // ========================================================

    const carregarOpcoesAgendamento =
        async () => {

            setLoadingOptions(true);
            setFormError("");

            try {

                const response =
                    await api.get<ScheduleOptionsResponse>(
                        "/schedules/options"
                    );


                const data =
                    response.data;


                if (
                    response.status !== 200 ||
                    data.status !== "success"
                ) {

                    setFormError(
                        data.message ||
                        "Não foi possível carregar os robôs e dispositivos disponíveis."
                    );
                    return false;
                }


                setRobots(
                    data.robots || []
                );


                setAgents(
                    data.agents || []
                );

                if (typeof data.timezone === "string" && data.timezone.trim()) {
                    setTimezone(data.timezone);
                }

                return true;

            } catch (err) {
                setFormError(getApiErrorMessage(
                    err,
                    "Não foi possível carregar os robôs e dispositivos disponíveis."
                ));
                return false;
            } finally {
                setLoadingOptions(false);
            }
        };


    // ========================================================
    // NOVO AGENDAMENTO
    // ========================================================

    const novoAgendamento =
        async () => {
            setEditandoId(
                null
            );

            setFormError("");
            setSuccessMessage("");


            setRobotId("");


            // Agent vazio significa seleção automática.
            setAgentId("");


            setTipo(
                "once"
            );


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
                ).padStart(
                    2,
                    "0"
                );


            const dia =
                String(
                    hoje.getDate()
                ).padStart(
                    2,
                    "0"
                );


            setDataInicio(
                `${ano}-${mes}-${dia}`
            );


            // Horário padrão atual.
            setHorario(
                "08:00"
            );


            setDiasSemana(
                []
            );


            setIntervaloAtivo(
                false
            );


            setIntervaloValor(
                1
            );


            setIntervaloUnidade(
                "minutes"
            );


            setHorarioFim("");

            setMisfirePolicy("run_once");

            setMisfireGraceSeconds(300);


            setModalAberto(
                true
            );

            await carregarOpcoesAgendamento();
        };


    // ========================================================
    // FECHAR MODAL
    // ========================================================

    const fecharModal = () => {

        setModalAberto(
            false
        );


        setEditandoId(
            null
        );

        setFormError("");
    };


    // ========================================================
    // ALTERAR DIA DA SEMANA
    // ========================================================

    const alterarDiaSemana = (
        dia: string
    ) => {

        setDiasSemana(
            (diasAtuais) => {

                if (
                    diasAtuais.includes(
                        dia
                    )
                ) {

                    return diasAtuais.filter(
                        (item) =>
                            item !== dia
                    );
                }


                return [
                    ...diasAtuais,
                    dia,
                ];
            }
        );
    };


    // ========================================================
    // ALTERAR TIPO
    // ========================================================

    const alterarTipoAgendamento = (
        novoTipo: string
    ) => {

        setTipo(
            novoTipo
        );


        // Fora de weekly, dias deixam de ser utilizados.
        if (
            novoTipo !== "weekly"
        ) {

            setDiasSemana(
                []
            );
        }


        // Schedule "once" não utiliza repetição em intervalo.
        if (
            novoTipo === "once"
        ) {

            setIntervaloAtivo(
                false
            );
        }
    };


    // ========================================================
    // SALVAR AGENDAMENTO
    // ========================================================

    const salvarAgendamento =
        async () => {

            // ====================================================
            // VALIDAÇÕES
            // ====================================================

            if (!robotId) {
                setFormError("Selecione o robô que será executado.");
                return;
            }


            if (!dataInicio) {

                setFormError("Informe a data de início do agendamento.");
                return;
            }


            if (!horario) {

                setFormError("Informe o horário da primeira execução.");
                return;
            }

            if (
                !Number.isInteger(misfireGraceSeconds)
                || misfireGraceSeconds < 30
                || misfireGraceSeconds > 86400
            ) {
                setFormError("Informe uma tolerância entre 30 segundos e 24 horas.");
                return;
            }


            // ====================================================
            // DIAS DA SEMANA
            // ====================================================

            let diasSemanaValor:
                string | null = null;


            if (
                tipo === "weekly"
            ) {

                if (
                    diasSemana.length === 0
                ) {

                    setFormError("Selecione pelo menos um dia para a recorrência semanal.");
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
            //
            // Mantém exatamente os campos e transformações
            // utilizados atualmente por Schedules.tsx.
            // ====================================================

            const payload = {

                robot_id:
                    Number(robotId),

                agent_id:
                    agentId || null,

                tipo:
                    tipo,

                data_inicio:
                    `${dataInicio}T${horario}`,

                horario:
                    horario,

                dias_semana:
                    diasSemanaValor,

                intervalo_ativo:
                    intervaloAtivo,

                intervalo_valor:
                    intervaloValorEnvio,

                intervalo_unidade:
                    intervaloUnidadeEnvio,

                horario_fim:
                    horarioFimEnvio,

                misfire_policy:
                    misfirePolicy,

                misfire_grace_seconds:
                    misfireGraceSeconds,
            };


            try {

                setSalvando(
                    true
                );

                setFormError("");


                // =================================================
                // CRIAÇÃO
                // =================================================

                if (
                    editandoId === null
                ) {

                    const response =
                        await api.post(
                            "/schedules",
                            payload
                        );


                    const data =
                        response.data;


                    if (
                        response.status !== 200 ||
                        data.status !== "success"
                    ) {

                        setFormError(data.message || "Não foi possível criar o agendamento.");
                        return;
                    }

                    setSuccessMessage("Agendamento criado com sucesso.");

                }

                // =================================================
                // EDIÇÃO
                // =================================================

                else {

                    const response =
                        await api.put(
                            `/schedules/${editandoId}`,
                            payload
                        );


                    const data =
                        response.data;


                    if (
                        response.status !== 200 ||
                        data.status !== "success"
                    ) {

                        setFormError(data.message || "Não foi possível atualizar o agendamento.");
                        return;
                    }

                    setSuccessMessage("Agendamento atualizado com sucesso.");
                }


                // Fecha somente após operação bem-sucedida.
                fecharModal();


                // Atualiza a tabela através da função fornecida
                // pela camada de dados.
                await onScheduleSaved();

            } catch (err) {
                setFormError(getApiErrorMessage(
                    err,
                    "Não foi possível salvar o agendamento. Revise os dados e tente novamente."
                ));

            } finally {

                setSalvando(
                    false
                );
            }
        };


    // ========================================================
    // EDITAR AGENDAMENTO
    // ========================================================

    const editarAgendamento =
        async (
            id: number
        ) => {

            setEditandoId(id);
            setModalAberto(true);
            setFormError("");
            setSuccessMessage("");
            setLoadingOptions(true);

            try {

                // Busca os dados completos do Schedule.
                const response =
                    await api.get(
                        `/schedules/${id}`
                    );


                const data =
                    response.data;


                if (
                    response.status !== 200 ||
                    data.status !== "success"
                ) {

                    setFormError(data.message || "Não foi possível carregar o agendamento selecionado.");
                    setLoadingOptions(false);
                    return;
                }


                const schedule =
                    data.schedule;


                // Mantém a ordem atual:
                // primeiro temos o Schedule e depois carregamos
                // as opções necessárias ao formulário.
                await carregarOpcoesAgendamento();


                // =================================================
                // PREENCHER FORMULÁRIO
                // =================================================

                setRobotId(
                    String(
                        schedule.robot_id
                    )
                );


                setAgentId(
                    schedule.agent_id ||
                    ""
                );


                setTipo(
                    schedule.tipo
                );


                setDataInicio(
                    schedule.data_inicio
                        ? schedule.data_inicio.substring(
                            0,
                            10
                        )
                        : ""
                );


                setHorario(
                    schedule.horario ||
                    ""
                );


                // =================================================
                // DIAS DA SEMANA
                // =================================================

                setDiasSemana(
                    schedule.dias_semana
                        ? schedule.dias_semana
                            .split(",")
                            .filter(Boolean)
                        : []
                );


                // =================================================
                // INTERVALO
                // =================================================

                setIntervaloAtivo(
                    Boolean(
                        schedule.intervalo_ativo
                    )
                );


                setIntervaloValor(
                    schedule.intervalo_valor ||
                    1
                );


                setIntervaloUnidade(
                    schedule.intervalo_unidade ||
                    "minutes"
                );


                setHorarioFim(
                    schedule.horario_fim ||
                    ""
                );

                setMisfirePolicy(
                    schedule.misfire_policy === "skip"
                        ? "skip"
                        : "run_once"
                );

                setMisfireGraceSeconds(
                    typeof schedule.misfire_grace_seconds === "number"
                        ? schedule.misfire_grace_seconds
                        : 300
                );


            } catch (err) {
                setLoadingOptions(false);
                setFormError(getApiErrorMessage(
                    err,
                    "Não foi possível carregar o agendamento selecionado."
                ));
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        // Modal / modo.
        modalAberto,
        editandoId,

        // Opções.
        robots,
        agents,
        timezone,

        // Campos.
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

        misfirePolicy,
        setMisfirePolicy,

        misfireGraceSeconds,
        setMisfireGraceSeconds,

        // Estado operacional.
        salvando,
        loadingOptions,
        formError,
        successMessage,
        clearSuccessMessage: () => setSuccessMessage(""),

        // Ações.
        novoAgendamento,
        fecharModal,
        alterarDiaSemana,
        alterarTipoAgendamento,
        salvarAgendamento,
        editarAgendamento,
        recarregarOpcoes: carregarOpcoesAgendamento,
    };
}

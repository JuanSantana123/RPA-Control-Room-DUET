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

import type {
    AgentOption,
    RobotOption,
} from "../../types/schedules";


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


    // ========================================================
    // SALVAMENTO
    // ========================================================

    const [
        salvando,
        setSalvando,
    ] = useState(false);


    // ========================================================
    // CARREGAR ROBOTS E AGENTS
    // ========================================================

    const carregarOpcoesAgendamento =
        async () => {

            try {

                const response =
                    await api.get(
                        "/schedules/options"
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


                setRobots(
                    data.robots || []
                );


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
    // NOVO AGENDAMENTO
    // ========================================================

    const novoAgendamento =
        async () => {

            // Mantém a ordem atual:
            // primeiro busca as opções disponíveis.
            await carregarOpcoesAgendamento();


            setEditandoId(
                null
            );


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


            setModalAberto(
                true
            );
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
            };


            try {

                setSalvando(
                    true
                );


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


                // Fecha somente após operação bem-sucedida.
                fecharModal();


                // Atualiza a tabela através da função fornecida
                // pela camada de dados.
                await onScheduleSaved();

            } catch (err) {

                console.error(
                    "Erro ao salvar agendamento:",
                    err
                );


                window.alert(
                    "Erro ao comunicar com o Control Room."
                );

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

                    window.alert(
                        data.message ||
                        "Erro ao carregar o agendamento."
                    );


                    return;
                }


                const schedule =
                    data.schedule;


                // Guarda o Schedule em edição.
                setEditandoId(
                    id
                );


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


                setModalAberto(
                    true
                );

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
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        // Modal / modo.
        modalAberto,
        editandoId,

        // Opções.
        robots,
        agents,

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

        // Estado operacional.
        salvando,

        // Ações.
        novoAgendamento,
        fecharModal,
        alterarDiaSemana,
        alterarTipoAgendamento,
        salvarAgendamento,
        editarAgendamento,
    };
}
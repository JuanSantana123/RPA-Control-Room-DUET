// ============================================================
// DUET CORE - SCHEDULES - DATA HOOK
// ============================================================
//
// Hook responsável pela camada operacional da lista de
// Agendamentos.
//
// Responsabilidade:
// - carregar os agendamentos do Control Room;
// - manter a lista sincronizada através de polling;
// - excluir um agendamento;
// - ativar ou desativar um agendamento;
// - controlar loading e erro da listagem.
//
// Integrações:
// - GET    /schedules
// - DELETE /schedules/{id}
// - PUT    /schedules/{id}/status
//
// Este hook NÃO:
// - cria agendamentos;
// - edita o formulário;
// - carrega opções de Robots/Agents;
// - monta payload de criação/edição;
// - controla o modal.
//
// A implementação foi extraída de pages/Schedules.tsx
// preservando o comportamento existente do Scheduler.
// ============================================================

import {
    useRef,
    useState,
} from "react";

import api from "../../services/api";
import { useInteraction } from "../../context/useInteraction";
import { usePollingTask } from "../async/usePollingTask";
import { getApiErrorMessage } from "../../utils/apiErrors";

import type {
    Schedule,
} from "../../types/schedules";


// ============================================================
// HOOK
// ============================================================

export function useSchedulesData() {

    const { confirm, notify } = useInteraction();

    // ========================================================
    // LISTA DE AGENDAMENTOS
    // ========================================================

    const [
        schedules,
        setSchedules,
    ] = useState<Schedule[]>([]);


    // ========================================================
    // CONTROLE DE CARREGAMENTO
    // ========================================================

    const [
        loading,
        setLoading,
    ] = useState(true);


    const [
        error,
        setError,
    ] = useState("");

    const requestSequence = useRef(0);


    // ========================================================
    // CARREGAR AGENDAMENTOS
    // ========================================================
    //
    // Equivalente ao comportamento existente:
    //
    // GET /api/schedules
    //
    // O prefixo /api continua sendo tratado pela instância
    // compartilhada de services/api.
    // ========================================================

    const carregarAgendamentosComSinal =
        async (signal?: AbortSignal) => {

            const requestId = ++requestSequence.current;

            try {

                const response =
                    await api.get(
                        "/schedules",
                        { signal },
                    );

                if (requestId !== requestSequence.current) {
                    return;
                }


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

                if (signal?.aborted || requestId !== requestSequence.current) {
                    return;
                }

                console.error(
                    "Erro ao carregar agendamentos:",
                    err
                );


                setError(getApiErrorMessage(
                    err,
                    "Não foi possível carregar os agendamentos.",
                ));

            } finally {

                if (!signal?.aborted && requestId === requestSequence.current) {
                    setLoading(false);
                }
            }
        };

    const carregarAgendamentos = () => carregarAgendamentosComSinal();


    // ========================================================
    // ========================================================
    // CARGA INICIAL + ATUALIZAÇÃO AUTOMÁTICA
    // ========================================================
    //
    // Ao montar a tela:
    //
    // 1. carrega os agendamentos imediatamente;
    // 2. inicia o polling automático a cada 5 segundos;
    // 3. ao sair da tela, remove o intervalo.
    //
    // O comportamento funcional permanece:
    // abertura da tela -> carga imediata -> atualização a cada 5s.
    // ========================================================

    usePollingTask(
        (signal) => carregarAgendamentosComSinal(signal),
        { intervalMs: 5000 },
    );

    // ========================================================
    // EXCLUIR AGENDAMENTO
    // ========================================================

    const excluirAgendamento =
        async (
            id: number
        ) => {

            // Mantém exatamente a confirmação existente.
            const confirmar = await confirm({
                title: "Excluir agendamento?",
                description: "As ocorrências futuras deixarão de ser criadas. Execuções já registradas permanecerão no histórico.",
                confirmLabel: "Excluir agendamento",
                tone: "danger",
            });


            if (!confirmar) {
                return;
            }


            try {

                const response =
                    await api.delete(
                        `/schedules/${id}`
                    );


                const data =
                    response.data;


                if (
                    response.status !== 200 ||
                    data.status !== "success"
                ) {

                    notify({ tone: "danger", title: "Agendamento não excluído", message: data.message || "O Control Room recusou a exclusão." });


                    return;
                }


                // Atualiza a lista após exclusão.
                await carregarAgendamentos();
                notify({ tone: "success", title: "Agendamento excluído", message: "As próximas ocorrências não serão mais criadas." });

            } catch (err) {

                console.error(
                    "Erro ao excluir agendamento:",
                    err
                );


                notify({ tone: "danger", title: "Falha de comunicação", message: "Não foi possível excluir o agendamento no Control Room." });
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
                        `/schedules/${id}/status`,
                        null,
                        {
                            params: {
                                ativo: ativo,
                            },
                        }
                    );


                const data =
                    response.data;


                if (
                    response.status !== 200 ||
                    data.status !== "success"
                ) {

                    notify({ tone: "danger", title: "Status não alterado", message: data.message || "O Control Room recusou a alteração." });


                    return;
                }


                // Atualiza a tabela após a alteração.
                await carregarAgendamentos();
                notify({ tone: "success", title: ativo ? "Agendamento ativado" : "Agendamento pausado" });

            } catch (err) {

                console.error(
                    "Erro ao alterar status:",
                    err
                );


                notify({ tone: "danger", title: "Falha de comunicação", message: "Não foi possível alterar o agendamento no Control Room." });
            }
        };


    // ========================================================
    // CONTRATO PÚBLICO
    // ========================================================

    return {
        schedules,
        loading,
        error,

        carregarAgendamentos,
        excluirAgendamento,
        alterarStatusAgendamento,
    };
}

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
    useEffect,
    useState,
} from "react";

import api from "../../services/api";

import type {
    Schedule,
} from "../../types/schedules";


// ============================================================
// HOOK
// ============================================================

export function useSchedulesData() {

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

    const carregarAgendamentos =
        async () => {

            try {

                const response =
                    await api.get(
                        "/schedules"
                    );


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

    useEffect(() => {

        // ====================================================
        // PRIMEIRA CARGA
        // ====================================================
        //
        // Não esperamos os primeiros 5 segundos.
        // A lista é consultada assim que o hook é montado.
        // ====================================================

        carregarAgendamentos();


        // ====================================================
        // POLLING
        // ====================================================
        //
        // Depois da primeira carga, mantém a lista sincronizada
        // com o Control Room a cada 5 segundos.
        // ====================================================

        const intervalo =
            setInterval(() => {

                carregarAgendamentos();

            }, 5000);


        // ====================================================
        // CLEANUP
        // ====================================================
        //
        // Quando a página deixa de existir, o intervalo precisa
        // ser encerrado para não continuar realizando requisições.
        // ====================================================

        return () => {

            clearInterval(
                intervalo
            );
        };

    }, []);

    // ========================================================
    // EXCLUIR AGENDAMENTO
    // ========================================================

    const excluirAgendamento =
        async (
            id: number
        ) => {

            // Mantém exatamente a confirmação existente.
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

                    window.alert(
                        data.message ||
                        "Não foi possível alterar o status."
                    );


                    return;
                }


                // Atualiza a tabela após a alteração.
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
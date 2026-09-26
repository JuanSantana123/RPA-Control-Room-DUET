// ============================================================
// DUET CORE - SCHEDULES PAGE
// ============================================================
//
// Página principal da área de Agendamentos.
//
// Responsabilidade:
// - compor os componentes visuais da tela;
// - conectar a camada de dados ao formulário;
// - conectar ações da listagem aos componentes;
// - controlar a composição entre tabela e modal.
//
// A lógica operacional foi distribuída por responsabilidade:
//
// useSchedulesData
// - carregamento da lista;
// - polling;
// - exclusão;
// - ativação/desativação.
//
// useScheduleForm
// - criação e edição;
// - estado do formulário;
// - Robots e Agents;
// - validações;
// - montagem do payload;
// - comunicação de POST/PUT.
//
// Componentes:
// - SchedulesHeader;
// - SchedulesTable;
// - ScheduleModal.
//
// Esta página NÃO deve concentrar:
// - chamadas HTTP;
// - regras do Scheduler;
// - polling;
// - montagem de payload;
// - implementação interna do formulário;
// - implementação interna da tabela.
//
// Dessa forma, Schedules.tsx permanece como camada de
// orquestração da feature.
// ============================================================

import SchedulesHeader
    from "../components/schedules/SchedulesHeader";

import SchedulesTable
    from "../components/schedules/SchedulesTable";

import ScheduleModal
    from "../components/schedules/ScheduleModal";

import {
    useSchedulesData,
} from "../hooks/schedules/useSchedulesData";

import {
    useScheduleForm,
} from "../hooks/schedules/useScheduleForm";
import FeedbackBanner from "../components/ui/FeedbackBanner";


// ============================================================
// PÁGINA DE AGENDAMENTOS
// ============================================================

function Schedules() {

    // ========================================================
    // DADOS / OPERAÇÕES DA LISTAGEM
    // ========================================================
    //
    // Responsável por:
    // - GET da lista;
    // - polling;
    // - exclusão;
    // - ativação/desativação.
    // ========================================================

    const {
        schedules,
        loading,
        error,

        carregarAgendamentos,
        excluirAgendamento,
        alterarStatusAgendamento,
    } = useSchedulesData();


    // ========================================================
    // FORMULÁRIO
    // ========================================================
    //
    // O formulário recebe carregarAgendamentos como callback.
    //
    // Assim, depois de criar ou editar um Schedule com sucesso,
    // useScheduleForm solicita a atualização da listagem sem
    // precisar assumir a responsabilidade pelo GET da tabela.
    // ========================================================

    const {
        modalAberto,
        editandoId,

        robots,
        agents,
        timezone,

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

        salvando,
        loadingOptions,
        formError,
        successMessage,
        clearSuccessMessage,

        novoAgendamento,
        fecharModal,
        alterarDiaSemana,
        alterarTipoAgendamento,
        salvarAgendamento,
        editarAgendamento,
        recarregarOpcoes,
    } = useScheduleForm({
        onScheduleSaved:
            carregarAgendamentos,
    });


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="page-container schedules-page">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <SchedulesHeader
                onNewSchedule={
                    novoAgendamento
                }
            />


            {/* ==================================================
                ERRO
                ================================================== */}

            {error && (
                <FeedbackBanner
                    tone="error"
                    title="Não foi possível atualizar os agendamentos"
                    message={error}
                    hint="Os dados exibidos podem estar desatualizados. Tente novamente em instantes."
                    action={{
                        label: "Atualizar agora",
                        onClick: carregarAgendamentos,
                    }}
                />
            )}

            {successMessage && (
                <FeedbackBanner
                    tone="success"
                    title="Agendamento salvo"
                    message={successMessage}
                    onDismiss={clearSuccessMessage}
                />
            )}


            {/* ==================================================
                TABELA
                ================================================== */}

            <SchedulesTable
                schedules={
                    schedules
                }
                loading={
                    loading
                }
                onEdit={
                    editarAgendamento
                }
                onToggleStatus={
                    alterarStatusAgendamento
                }
                onDelete={
                    excluirAgendamento
                }
            />


            {/* ==================================================
                MODAL
                ================================================== */}

            {modalAberto && (

                <ScheduleModal
                    editandoId={
                        editandoId
                    }

                    robots={
                        robots
                    }
                    agents={
                        agents
                    }
                    timezone={timezone}

                    robotId={
                        robotId
                    }
                    setRobotId={
                        setRobotId
                    }

                    agentId={
                        agentId
                    }
                    setAgentId={
                        setAgentId
                    }

                    tipo={
                        tipo
                    }

                    dataInicio={
                        dataInicio
                    }
                    setDataInicio={
                        setDataInicio
                    }

                    horario={
                        horario
                    }
                    setHorario={
                        setHorario
                    }

                    diasSemana={
                        diasSemana
                    }

                    intervaloAtivo={
                        intervaloAtivo
                    }
                    setIntervaloAtivo={
                        setIntervaloAtivo
                    }

                    intervaloValor={
                        intervaloValor
                    }
                    setIntervaloValor={
                        setIntervaloValor
                    }

                    intervaloUnidade={
                        intervaloUnidade
                    }
                    setIntervaloUnidade={
                        setIntervaloUnidade
                    }

                    horarioFim={
                        horarioFim
                    }
                    setHorarioFim={
                        setHorarioFim
                    }

                    misfirePolicy={misfirePolicy}
                    setMisfirePolicy={setMisfirePolicy}

                    misfireGraceSeconds={misfireGraceSeconds}
                    setMisfireGraceSeconds={setMisfireGraceSeconds}

                    salvando={
                        salvando
                    }
                    loadingOptions={loadingOptions}
                    formError={formError}

                    onClose={
                        fecharModal
                    }
                    onChangeType={
                        alterarTipoAgendamento
                    }
                    onToggleWeekday={
                        alterarDiaSemana
                    }
                    onSave={
                        salvarAgendamento
                    }
                    onRetryOptions={recarregarOpcoes}
                />

            )}

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default Schedules;

// ============================================================
// DUET CORE - SCHEDULES - HEADER
// ============================================================
//
// Cabeçalho visual da página de Agendamentos.
//
// Responsabilidade:
// - exibir título e descrição da área;
// - disponibilizar a ação "Novo Agendamento".
//
// A ação é recebida da página através de callback.
//
// Este componente NÃO:
// - abre modal diretamente;
// - executa chamadas HTTP;
// - possui regras de Scheduler;
// - controla estado de formulário.
// ============================================================


// ============================================================
// PROPS
// ============================================================

interface SchedulesHeaderProps {
    onNewSchedule: () => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function SchedulesHeader({
    onNewSchedule,
}: SchedulesHeaderProps) {

    return (
        <section className="page-heading">

            <div>

                <div className="page-eyebrow">
                    AUTOMATION SCHEDULES
                </div>

                <h1>
                    Agendamentos
                </h1>

                <p>
                    Robôs programados para execução automática
                </p>

            </div>


            <button
                type="button"
                className="primary-button"
                onClick={onNewSchedule}
            >
                + Novo Agendamento
            </button>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default SchedulesHeader;
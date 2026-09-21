// ============================================================
// DUET CORE - SCHEDULES - TABLE
// ============================================================
//
// Tabela visual da área de Agendamentos.
//
// Responsabilidade:
// - renderizar o painel da listagem;
// - renderizar cabeçalhos da tabela;
// - apresentar estado de carregamento;
// - apresentar estado de lista vazia;
// - delegar cada Schedule para ScheduleRow.
//
// As ações operacionais são recebidas por callbacks e
// encaminhadas para cada linha.
//
// Este componente NÃO:
// - carrega dados;
// - executa polling;
// - chama endpoints;
// - cria ou edita agendamentos;
// - mantém estado do Scheduler.
// ============================================================

import ScheduleRow from "./ScheduleRow";

import type {
    Schedule,
} from "../../types/schedules";


// ============================================================
// PROPS
// ============================================================

interface SchedulesTableProps {
    schedules: Schedule[];
    loading: boolean;

    onEdit: (
        id: number
    ) => void | Promise<void>;

    onToggleStatus: (
        id: number,
        ativo: boolean
    ) => void | Promise<void>;

    onDelete: (
        id: number
    ) => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function SchedulesTable({
    schedules,
    loading,
    onEdit,
    onToggleStatus,
    onDelete,
}: SchedulesTableProps) {

    return (
        <section className="content-panel schedules-panel">

            <div className="content-panel-header">

                <div>
                    <h2>
                        Agendamentos cadastrados
                    </h2>

                    <p>
                        Gerencie as execuções automáticas dos robôs.
                    </p>
                </div>

            </div>


            <div className="schedules-table-wrapper">

                <table className="schedules-table">

                    <thead>

                        <tr>
                            <th>Robô</th>
                            <th>Agent</th>
                            <th>Tipo</th>
                            <th>Horário</th>
                            <th>Próxima execução</th>
                            <th>Status</th>
                            <th>Ações</th>
                        </tr>

                    </thead>


                    <tbody>

                        {/* ==========================================
                            CARREGAMENTO
                            ========================================== */}

                        {loading && (

                            <tr>
                                <td
                                    colSpan={7}
                                    className="table-empty-state"
                                >
                                    Carregando agendamentos...
                                </td>
                            </tr>

                        )}


                        {/* ==========================================
                            LISTA VAZIA
                            ========================================== */}

                        {!loading &&
                            schedules.length === 0 && (

                                <tr>
                                    <td
                                        colSpan={7}
                                        className="table-empty-state"
                                    >
                                        Nenhum agendamento cadastrado.
                                    </td>
                                </tr>

                            )}


                        {/* ==========================================
                            AGENDAMENTOS
                            ========================================== */}

                        {!loading &&
                            schedules.map(
                                (schedule) => (

                                    <ScheduleRow
                                        key={schedule.id}
                                        schedule={schedule}
                                        onEdit={onEdit}
                                        onToggleStatus={
                                            onToggleStatus
                                        }
                                        onDelete={onDelete}
                                    />

                                )
                            )}

                    </tbody>

                </table>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default SchedulesTable;
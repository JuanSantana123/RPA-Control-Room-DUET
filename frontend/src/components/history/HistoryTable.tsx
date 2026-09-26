// ============================================================
// DUET CORE - HISTORY - TABLE
// ============================================================
//
// Painel e tabela principal do histórico de execuções.
//
// Responsabilidade:
// - apresentar cabeçalho do painel;
// - apresentar cabeçalho da tabela;
// - apresentar loading;
// - apresentar erro;
// - apresentar estado vazio;
// - renderizar HistoryRow para cada execução.
//
// Este componente NÃO:
// - consulta o backend;
// - controla polling;
// - calcula duração;
// - formata datas;
// - traduz status.
//
// Dados e estados são recebidos através de props.
// ============================================================

import HistoryRow
    from "./HistoryRow";

import { TableSkeleton }
    from "../ui/Skeletons";
import EmptyState from "../ui/EmptyState";
import { FileClock } from "lucide-react";

import type {
    HistoryExecution,
} from "../../types/history";


// ============================================================
// PROPS
// ============================================================

interface HistoryTableProps {
    executions:
        HistoryExecution[];

    loading:
        boolean;

}


// ============================================================
// COMPONENTE
// ============================================================

function HistoryTable({
    executions,
    loading,
}: HistoryTableProps) {

    return (
        <section className="content-panel history-panel">

            {/* ==================================================
                CABEÇALHO DO PAINEL
                ================================================== */}

            <div className="content-panel-header">

                <div>

                    <h2>
                        Execuções finalizadas
                    </h2>

                    <p>
                        Consulte o histórico das automações executadas.
                    </p>

                </div>

            </div>


            {/* ==================================================
                TABELA
                ================================================== */}

            <div className="history-table-wrapper">

                <table className="history-table">

                    <thead>

                        <tr>

                            <th>ID</th>

                            <th>Robô</th>

                            <th>Pasta</th>

                            <th>Usuário</th>

                            <th>Dispositivo</th>

                            <th>Início</th>

                            <th>Fim</th>

                            <th>Duração</th>

                            <th>Situação</th>

                            <th>Erro</th>

                        </tr>

                    </thead>


                    <tbody>

                        {/* ======================================
                            CARREGANDO
                            ====================================== */}

                        {loading && (

                            <tr>

                                <td colSpan={10}>
                                    <TableSkeleton rows={5} columns={6} />
                                </td>

                            </tr>

                        )}


                        {/* ======================================
                            ESTADO VAZIO
                            ====================================== */}

                        {!loading &&
                            executions.length === 0 && (

                                <tr>

                                    <td colSpan={10}>
                                        <EmptyState
                                            icon={<FileClock />}
                                            title="Nenhuma execução finalizada"
                                            description="As automações concluídas aparecerão aqui com duração, resultado e rastreabilidade."
                                        />
                                    </td>

                                </tr>

                            )}


                        {/* ======================================
                            EXECUÇÕES
                            ====================================== */}

                        {!loading &&
                            executions.map(
                                (execution) => (

                                    <HistoryRow
                                        key={
                                            execution.id
                                        }
                                        execution={
                                            execution
                                        }
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

export default HistoryTable;

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

    error:
        string;
}


// ============================================================
// COMPONENTE
// ============================================================

function HistoryTable({
    executions,
    loading,
    error,
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

                            <th>Agent</th>

                            <th>Início</th>

                            <th>Fim</th>

                            <th>Duração</th>

                            <th>Status</th>

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
                                    Carregando histórico...
                                </td>

                            </tr>

                        )}


                        {/* ======================================
                            ERRO
                            ====================================== */}

                        {!loading && error && (

                            <tr>

                                <td colSpan={10}>
                                    {error}
                                </td>

                            </tr>

                        )}


                        {/* ======================================
                            ESTADO VAZIO
                            ====================================== */}

                        {!loading &&
                            !error &&
                            executions.length === 0 && (

                                <tr>

                                    <td colSpan={10}>
                                        Nenhuma execução finalizada.
                                    </td>

                                </tr>

                            )}


                        {/* ======================================
                            EXECUÇÕES
                            ====================================== */}

                        {!loading &&
                            !error &&
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
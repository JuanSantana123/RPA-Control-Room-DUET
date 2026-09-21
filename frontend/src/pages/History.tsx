// ============================================================
// DUET CORE - HISTORY PAGE
// ============================================================
//
// Página principal do histórico de execuções.
//
// Responsabilidade:
// - compor a interface da área de histórico;
// - conectar os dados fornecidos por useHistoryData;
// - apresentar o cabeçalho;
// - apresentar a tabela de execuções finalizadas.
//
// Arquitetura:
//
// History
//   │
//   ├── useHistoryData
//   │     ├── GET /executions/history
//   │     ├── estado das execuções
//   │     ├── loading / erro
//   │     └── polling de 5 segundos
//   │
//   ├── HistoryHeader
//   │
//   └── HistoryTable
//         └── HistoryRow
//               └── historyFormatters
//
// Esta página NÃO:
// - executa chamadas HTTP diretamente;
// - cria timers diretamente;
// - formata datas;
// - calcula duração;
// - traduz status;
// - renderiza individualmente as linhas da tabela.
//
// A página funciona somente como camada de composição entre
// os dados do histórico e os componentes visuais.
// ============================================================

import HistoryHeader
    from "../components/history/HistoryHeader";

import HistoryTable
    from "../components/history/HistoryTable";

import {
    useHistoryData,
} from "../hooks/history/useHistoryData";


// ============================================================
// PÁGINA DE HISTÓRICO
// ============================================================

function History() {

    // ========================================================
    // DADOS DO HISTÓRICO
    // ========================================================
    //
    // O hook concentra:
    //
    // - primeira consulta ao backend;
    // - atualização automática a cada 5 segundos;
    // - armazenamento das execuções;
    // - estado de carregamento;
    // - tratamento de erro.
    // ========================================================

    const {
        executions,
        loading,
        error,
    } = useHistoryData();


    // ========================================================
    // INTERFACE
    // ========================================================

    return (
        <div className="page-container history-page">

            {/* ==================================================
                CABEÇALHO
                ================================================== */}

            <HistoryHeader />


            {/* ==================================================
                HISTÓRICO DE EXECUÇÕES
                ================================================== */}

            <HistoryTable
                executions={
                    executions
                }
                loading={
                    loading
                }
                error={
                    error
                }
            />

        </div>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default History;
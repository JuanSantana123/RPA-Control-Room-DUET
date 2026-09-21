// ============================================================
// DUET CORE - HISTORY - HEADER
// ============================================================
//
// Cabeçalho visual da página de histórico.
//
// Responsabilidade:
// - identificar a área de histórico;
// - apresentar título;
// - apresentar descrição.
//
// Este componente NÃO:
// - carrega execuções;
// - controla estado;
// - executa chamadas HTTP;
// - possui regras de histórico.
// ============================================================


// ============================================================
// COMPONENTE
// ============================================================

function HistoryHeader() {

    return (
        <section className="page-heading">

            <div>

                <div className="page-eyebrow">
                    EXECUTION HISTORY
                </div>

                <h1>
                    Histórico
                </h1>

                <p>
                    Histórico das execuções finalizadas
                </p>

            </div>

        </section>
    );
}


// ============================================================
// EXPORTAÇÃO
// ============================================================

export default HistoryHeader;
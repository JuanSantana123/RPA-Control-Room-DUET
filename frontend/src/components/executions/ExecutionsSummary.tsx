// ============================================================
// DUET CORE - EXECUTIONS - SUMMARY
// ============================================================
//
// Resumo visual da página de Execuções.
//
// Responsabilidade:
// - apresentar quantidade de execuções visíveis;
// - apresentar quantidade de Agents;
// - apresentar quantidade de execuções em andamento.
//
// Origem dos dados:
// - todos os valores são recebidos através de props.
//
// Este componente NÃO:
// - filtra execuções;
// - consulta API;
// - calcula listas;
// - altera estado;
// - executa ações.
//
// Dessa forma o componente permanece exclusivamente visual.
// ============================================================

import {
    Clock3,
    Loader2,
    ListOrdered,
    Server,
} from "lucide-react";


// ============================================================
// PROPS
// ============================================================

interface ExecutionsSummaryProps {

    // Quantidade após aplicação dos filtros atuais.
    visibleExecutionsCount: number;

    // Quantidade de Agents distintos encontrados.
    agentsCount: number;

    // Quantidade de execuções com status "running".
    runningExecutionsCount: number;
    queuedExecutionsCount: number;
    delayedExecutionsCount: number;
}


// ============================================================
// COMPONENTE
// ============================================================

function ExecutionsSummary({
    visibleExecutionsCount,
    agentsCount,
    runningExecutionsCount,
    queuedExecutionsCount,
    delayedExecutionsCount,
}: ExecutionsSummaryProps) {

    return (
        <div className="execution-summary-grid">

            {/* =================================================
                EXECUÇÕES VISÍVEIS
            ================================================= */}

            <div className="execution-summary-card">

                <div className="execution-summary-icon">
                    <Loader2 size={19} />
                </div>


                <div>
                    <span>
                        Execuções visíveis
                    </span>

                    <strong>
                        {visibleExecutionsCount}
                    </strong>
                </div>

            </div>

            <div className="execution-summary-card">
                <div className="execution-summary-icon">
                    <ListOrdered size={19} />
                </div>
                <div>
                    <span>Na fila</span>
                    <strong>{queuedExecutionsCount}</strong>
                    <small>{delayedExecutionsCount > 0
                        ? `${delayedExecutionsCount} acima da janela de atenção`
                        : "Dentro da janela de atenção"}</small>
                </div>
            </div>


            {/* =================================================
                AGENTS ATIVOS
            ================================================= */}

            <div className="execution-summary-card">

                <div className="execution-summary-icon">
                    <Server size={19} />
                </div>


                <div>
                    <span>
                        Agents ativos
                    </span>

                    <strong>
                        {agentsCount}
                    </strong>
                </div>

            </div>


            {/* =================================================
                EXECUÇÕES EM ANDAMENTO
            ================================================= */}

            <div className="execution-summary-card">

                <div className="execution-summary-icon">
                    <Clock3 size={19} />
                </div>


                <div>
                    <span>
                        Em execução
                    </span>

                    <strong>
                        {runningExecutionsCount}
                    </strong>
                </div>

            </div>

        </div>
    );
}


export default ExecutionsSummary;

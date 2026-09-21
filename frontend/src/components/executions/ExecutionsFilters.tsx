// ============================================================
// DUET CORE - EXECUTIONS - FILTERS
// ============================================================
//
// Componente visual dos filtros da página de Execuções.
//
// Responsabilidade:
// - apresentar seleção de Robot;
// - apresentar seleção de Agent;
// - disparar alteração dos filtros;
// - disponibilizar a ação "Limpar filtros".
//
// Origem dos dados e ações:
// - todos são recebidos através de props;
// - o estado real pertence ao hook useExecutionFilters.
//
// Este componente NÃO:
// - executa filtragem;
// - consulta API;
// - conhece o polling;
// - mantém a lista de execuções;
// - altera execuções.
//
// Preserva os textos, IDs e classes CSS da tela atual.
// ============================================================

import {
    Filter,
} from "lucide-react";


// ============================================================
// PROPS
// ============================================================

interface ExecutionsFiltersProps {

    // Valores atualmente selecionados.
    filtroRobo: string;
    filtroAgent: string;

    // Opções disponíveis.
    robos: string[];
    agents: string[];

    // Atualização dos filtros.
    onFiltroRoboChange: (
        value: string
    ) => void;

    onFiltroAgentChange: (
        value: string
    ) => void;

    // Remove os dois filtros.
    onClearFilters: () => void;
}


// ============================================================
// COMPONENTE
// ============================================================

function ExecutionsFilters({
    filtroRobo,
    filtroAgent,
    robos,
    agents,
    onFiltroRoboChange,
    onFiltroAgentChange,
    onClearFilters,
}: ExecutionsFiltersProps) {

    return (
        <div className="executions-toolbar">

            {/* =================================================
                TÍTULO
            ================================================= */}

            <div className="executions-toolbar-title">

                <Filter size={17} />

                <span>
                    Filtros
                </span>

            </div>


            {/* =================================================
                FILTRO DE ROBOT
            ================================================= */}

            <div className="execution-filter-group">

                <label htmlFor="filtro-robo">
                    Robô
                </label>


                <select
                    id="filtro-robo"
                    value={filtroRobo}
                    onChange={(event) =>
                        onFiltroRoboChange(
                            event.target.value
                        )
                    }
                >
                    <option value="">
                        Todos os robôs
                    </option>


                    {robos.map((robo) => (

                        <option
                            key={robo}
                            value={robo}
                        >
                            {robo}
                        </option>

                    ))}

                </select>

            </div>


            {/* =================================================
                FILTRO DE AGENT
            ================================================= */}

            <div className="execution-filter-group">

                <label htmlFor="filtro-agent">
                    Agent
                </label>


                <select
                    id="filtro-agent"
                    value={filtroAgent}
                    onChange={(event) =>
                        onFiltroAgentChange(
                            event.target.value
                        )
                    }
                >
                    <option value="">
                        Todos os Agents
                    </option>


                    {agents.map((agent) => (

                        <option
                            key={agent}
                            value={agent}
                        >
                            {agent}
                        </option>

                    ))}

                </select>

            </div>


            {/* =================================================
                LIMPAR
            ================================================= */}

            <button
                type="button"
                className="secondary-button"
                onClick={onClearFilters}
            >
                Limpar filtros
            </button>

        </div>
    );
}


export default ExecutionsFilters;
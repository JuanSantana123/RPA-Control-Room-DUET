// ============================================================
// DUET CORE - EXECUTIONS - TABLE
// ============================================================
//
// Componente visual responsável pela tabela de Execuções.
//
// Responsabilidade:
// - apresentar o cabeçalho operacional da tabela;
// - apresentar estado inicial de carregamento;
// - apresentar estado vazio;
// - renderizar uma ExecutionRow para cada execução;
// - encaminhar ações da linha para a camada superior.
//
// Origem dos dados e ações:
// - todos são recebidos através de props.
//
// Este componente NÃO:
// - consulta API;
// - executa polling;
// - filtra dados;
// - executa Stop ou Cancel;
// - mantém estado do modal.
//
// ExecutionRow é responsável apenas pela representação de
// cada registro individual.
// ============================================================

import { Activity } from "lucide-react";

import { TableSkeleton }
    from "../ui/Skeletons";

import type {
    Execution,
} from "../../types/executions";

import ExecutionRow from "./ExecutionRow";
import EmptyState from "../ui/EmptyState";
import AccessModeBadge from "../ui/AccessModeBadge";


// ============================================================
// PROPS
// ============================================================

interface ExecutionsTableProps {

    // Execuções já filtradas pela camada superior.
    executions: Execution[];

    // Loading inicial da coleção.
    loading: boolean;

    // IDs das ações atualmente em andamento.
    parandoExecucao: number | null;
    cancelandoExecucao: number | null;
    queueWarningSeconds: number;
    canStop: boolean;
    canCancel: boolean;

    // Ações encaminhadas às linhas.
    onViewDetails: (
        execution: Execution
    ) => void;

    onStopExecution: (
        executionId: number,
        agentId: string
    ) => void | Promise<void>;

    onCancelExecution: (
        executionId: number
    ) => void | Promise<void>;
}


// ============================================================
// COMPONENTE
// ============================================================

function ExecutionsTable({
    executions,
    loading,
    parandoExecucao,
    cancelandoExecucao,
    queueWarningSeconds,
    canStop,
    canCancel,
    onViewDetails,
    onStopExecution,
    onCancelExecution,
}: ExecutionsTableProps) {

    return (
        <div className="executions-table-card">

            {/* =================================================
                CABEÇALHO
            ================================================= */}

            <div className="executions-table-header">

                <div>

                    <h2>
                        Execuções em andamento
                    </h2>

                    <p>
                        Atualização automática a cada 5 segundos
                    </p>

                </div>


                <div className="executions-table-header__status">
                {!canStop && !canCancel && <AccessModeBadge />}
                <span className="execution-live-indicator">

                    <span />

                    Ao vivo

                </span>
                </div>

            </div>


            {/* =================================================
                TABELA
            ================================================= */}

            <div className="executions-table-wrapper">

                <table className="executions-table">

                    <thead>
                        <tr>
                            <th>ID</th>
                            <th>Robô</th>
                            <th>Pasta</th>
                            <th>Usuário</th>
                            <th>Agent</th>
                            <th>PID</th>
                            <th>Início</th>
                            <th>Duração</th>
                            <th>Status</th>
                            <th>Ações</th>
                        </tr>
                    </thead>


                    <tbody>

                        {/* =====================================
                            LOADING
                        ===================================== */}

                        {loading ? (

                            <tr>
                                <td colSpan={10}>

                                    <TableSkeleton rows={4} columns={6} />

                                </td>
                            </tr>

                        ) : executions.length === 0 ? (

                            /* =================================
                                SEM RESULTADOS
                            ================================= */

                            <tr>
                                <td colSpan={10}>

                                    <EmptyState
                                        icon={<Activity />}
                                        title="Nenhuma execução em andamento"
                                        description="Quando um robô for iniciado, seu progresso e dispositivo aparecerão aqui em tempo real."
                                    />

                                </td>
                            </tr>

                        ) : (

                            /* =================================
                                EXECUÇÕES
                            ================================= */

                            executions.map(
                                (execution) => (

                                    <ExecutionRow
                                        key={
                                            execution.id
                                        }
                                        execution={
                                            execution
                                        }
                                        parandoExecucao={
                                            parandoExecucao
                                        }
                                        cancelandoExecucao={
                                            cancelandoExecucao
                                        }
                                        queueWarningSeconds={queueWarningSeconds}
                                        canStop={canStop}
                                        canCancel={canCancel}
                                        onViewDetails={
                                            onViewDetails
                                        }
                                        onStopExecution={
                                            onStopExecution
                                        }
                                        onCancelExecution={
                                            onCancelExecution
                                        }
                                    />

                                )
                            )
                        )}

                    </tbody>

                </table>

            </div>

        </div>
    );
}


export default ExecutionsTable;

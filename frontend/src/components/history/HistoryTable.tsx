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
import { useMemo, useState } from "react";
import { TextField } from "../ui/TextField";
import PremiumSelect from "../ui/PremiumSelect";
import { Button } from "../ui/Button";

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

    const [search, setSearch] = useState("");
    const [status, setStatus] = useState("all");
    const filteredExecutions = useMemo(() => {
        const term = search.trim().toLocaleLowerCase("pt-BR");

        return executions.filter((execution) => {
            const matchesStatus = status === "all" || execution.status === status;
            const matchesSearch = !term || [
                String(execution.id),
                execution.robot_name ?? "",
                execution.folder_name ?? "",
                execution.user_name ?? "",
                execution.username ?? "",
                execution.agent_name ?? "",
                execution.error_message ?? "",
            ].some((value) => value.toLocaleLowerCase("pt-BR").includes(term));

            return matchesStatus && matchesSearch;
        });
    }, [executions, search, status]);
    const hasFilters = Boolean(search.trim()) || status !== "all";
    const clearFilters = () => {
        setSearch("");
        setStatus("all");
    };

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

                <span className="history-result-count">
                    {hasFilters ? `${filteredExecutions.length}/${executions.length}` : executions.length}
                </span>

            </div>

            {executions.length > 0 && (
                <div className="history-filterbar" aria-label="Filtros do histórico">
                    <TextField
                        label="Pesquisar no histórico"
                        labelHidden
                        type="search"
                        value={search}
                        placeholder="Pesquisar por robô, pasta, usuário, Device ou ID..."
                        onChange={(event) => setSearch(event.target.value)}
                    />
                    <PremiumSelect
                        value={status}
                        aria-label="Filtrar histórico por situação"
                        onChange={(event) => setStatus(event.target.value)}
                    >
                        <option value="all">Todas as situações</option>
                        <option value="success">Sucesso</option>
                        <option value="error">Erro</option>
                        <option value="stopped">Parado</option>
                    </PremiumSelect>
                    <Button size="sm" variant="ghost" disabled={!hasFilters} onClick={clearFilters}>
                        Limpar filtros
                    </Button>
                </div>
            )}


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

                        {!loading && executions.length > 0 && filteredExecutions.length === 0 && (
                            <tr>
                                <td colSpan={10}>
                                    <EmptyState
                                        icon={<FileClock />}
                                        title="Nenhuma execução corresponde aos filtros"
                                        description="Ajuste a pesquisa ou a situação para consultar outros registros."
                                        action={<Button size="sm" onClick={clearFilters}>Limpar filtros</Button>}
                                    />
                                </td>
                            </tr>
                        )}


                        {/* ======================================
                            EXECUÇÕES
                            ====================================== */}

                        {!loading &&
                            filteredExecutions.map(
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

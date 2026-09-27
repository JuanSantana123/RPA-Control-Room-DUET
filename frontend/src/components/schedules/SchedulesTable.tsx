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

import { TableSkeleton }
    from "../ui/Skeletons";
import EmptyState from "../ui/EmptyState";
import { CalendarClock } from "lucide-react";
import AccessModeBadge from "../ui/AccessModeBadge";
import { useMemo, useState } from "react";
import { TextField } from "../ui/TextField";
import PremiumSelect from "../ui/PremiumSelect";
import { Button } from "../ui/Button";

import type {
    Schedule,
} from "../../types/schedules";


// ============================================================
// PROPS
// ============================================================

interface SchedulesTableProps {
    schedules: Schedule[];
    loading: boolean;
    canEdit: boolean;
    canDelete: boolean;

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
    canEdit,
    canDelete,
    onEdit,
    onToggleStatus,
    onDelete,
}: SchedulesTableProps) {

    const [search, setSearch] = useState("");
    const [status, setStatus] = useState<"all" | "active" | "inactive">("all");
    const filteredSchedules = useMemo(() => {
        const term = search.trim().toLocaleLowerCase("pt-BR");

        return schedules.filter((schedule) => {
            const matchesStatus = status === "all"
                || (status === "active" ? schedule.ativo : !schedule.ativo);
            const matchesSearch = !term || [
                String(schedule.id),
                schedule.robot_name,
                schedule.agent_name,
                schedule.agent_id ?? "",
                schedule.tipo,
            ].some((value) => value.toLocaleLowerCase("pt-BR").includes(term));

            return matchesStatus && matchesSearch;
        });
    }, [schedules, search, status]);
    const hasFilters = Boolean(search.trim()) || status !== "all";
    const clearFilters = () => {
        setSearch("");
        setStatus("all");
    };

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

                <div className="schedules-panel-meta">
                    {!canEdit && !canDelete && <AccessModeBadge />}
                    <span className="schedules-result-count">
                        {hasFilters ? `${filteredSchedules.length}/${schedules.length}` : schedules.length}
                    </span>
                </div>

            </div>

            {schedules.length > 0 && (
                <div className="schedules-filterbar" aria-label="Filtros dos agendamentos">
                    <TextField
                        label="Pesquisar agendamentos"
                        labelHidden
                        type="search"
                        value={search}
                        placeholder="Pesquisar por robô, Device, tipo ou ID..."
                        onChange={(event) => setSearch(event.target.value)}
                    />
                    <PremiumSelect
                        value={status}
                        aria-label="Filtrar agendamentos por situação"
                        onChange={(event) => setStatus(event.target.value as "all" | "active" | "inactive")}
                    >
                        <option value="all">Todas as situações</option>
                        <option value="active">Ativos</option>
                        <option value="inactive">Inativos</option>
                    </PremiumSelect>
                    <Button size="sm" variant="ghost" disabled={!hasFilters} onClick={clearFilters}>
                        Limpar filtros
                    </Button>
                </div>
            )}


            <div className="schedules-table-wrapper">

                <table className="schedules-table">

                    <thead>

                        <tr>
                            <th>Robô</th>
                            <th>Dispositivo</th>
                            <th>Tipo</th>
                            <th>Horário</th>
                            <th>Próxima execução</th>
                            <th>Situação</th>
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
                                    className="table-loading-state"
                                >
                                    <TableSkeleton rows={4} columns={5} />
                                </td>
                            </tr>

                        )}


                        {/* ==========================================
                            LISTA VAZIA
                            ========================================== */}

                        {!loading &&
                            schedules.length === 0 && (

                                <tr>
                                    <td colSpan={7}>
                                        <EmptyState
                                            icon={<CalendarClock />}
                                            title="Nenhum agendamento cadastrado"
                                            description="Crie um agendamento para executar robôs automaticamente em datas e horários definidos."
                                        />
                                    </td>
                                </tr>

                            )}

                        {!loading && schedules.length > 0 && filteredSchedules.length === 0 && (
                            <tr>
                                <td colSpan={7}>
                                    <EmptyState
                                        icon={<CalendarClock />}
                                        title="Nenhum agendamento corresponde aos filtros"
                                        description="Ajuste a pesquisa ou a situação para localizar outros agendamentos."
                                        action={<Button size="sm" onClick={clearFilters}>Limpar filtros</Button>}
                                    />
                                </td>
                            </tr>
                        )}


                        {/* ==========================================
                            AGENDAMENTOS
                            ========================================== */}

                        {!loading &&
                            filteredSchedules.map(
                                (schedule) => (

                                    <ScheduleRow
                                        key={schedule.id}
                                        schedule={schedule}
                                        canEdit={canEdit}
                                        canDelete={canDelete}
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

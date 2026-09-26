import { RotateCcw, SlidersHorizontal } from "lucide-react";
import PremiumSelect from "../../ui/PremiumSelect";
import { Button } from "../../ui/Button";

export type DevelopmentStatusFilter = "all" | "draft" | "modified" | "published";
export type DevelopmentOriginFilter = "all" | "new" | "existing";
export type DevelopmentSort = "updated-desc" | "created-desc" | "name-asc" | "due-asc";

interface DevelopmentFiltersBarProps {
  status: DevelopmentStatusFilter;
  origin: DevelopmentOriginFilter;
  sort: DevelopmentSort;
  visibleCount: number;
  totalCount: number;
  onStatusChange: (value: DevelopmentStatusFilter) => void;
  onOriginChange: (value: DevelopmentOriginFilter) => void;
  onSortChange: (value: DevelopmentSort) => void;
  onReset: () => void;
}

export default function DevelopmentFiltersBar({ status, origin, sort, visibleCount, totalCount, onStatusChange, onOriginChange, onSortChange, onReset }: DevelopmentFiltersBarProps) {
  const hasFilters = status !== "all" || origin !== "all" || sort !== "updated-desc";

  return (
    <div className="development-filters">
      <div className="development-filters__label">
        <SlidersHorizontal size={16} strokeWidth={1.8} aria-hidden="true" />
        <span>Organizar visão</span>
      </div>
      <PremiumSelect value={status} onChange={(event) => onStatusChange(event.target.value as DevelopmentStatusFilter)} aria-label="Filtrar por situação">
        <option value="all">Todas as situações</option>
        <option value="draft">Rascunhos</option>
        <option value="modified">Com alterações</option>
        <option value="published">Publicados</option>
      </PremiumSelect>
      <PremiumSelect value={origin} onChange={(event) => onOriginChange(event.target.value as DevelopmentOriginFilter)} aria-label="Filtrar por origem">
        <option value="all">Todas as origens</option>
        <option value="new">Novos projetos</option>
        <option value="existing">Novas versões</option>
      </PremiumSelect>
      <PremiumSelect value={sort} onChange={(event) => onSortChange(event.target.value as DevelopmentSort)} aria-label="Ordenar projetos">
        <option value="updated-desc">Atualizados recentemente</option>
        <option value="created-desc">Criados recentemente</option>
        <option value="name-asc">Nome: A–Z</option>
        <option value="due-asc">Prazo mais próximo</option>
      </PremiumSelect>
      <span className="development-filters__count">{visibleCount} de {totalCount}</span>
      <Button size="sm" disabled={!hasFilters} onClick={onReset}>
        <RotateCcw size={14} aria-hidden="true" />
        Limpar
      </Button>
    </div>
  );
}

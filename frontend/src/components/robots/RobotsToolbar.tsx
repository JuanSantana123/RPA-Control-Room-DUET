import { Download, LayoutGrid, List, Upload } from "lucide-react";
import PremiumSelect from "../ui/PremiumSelect";
import { Button, IconButton } from "../ui/Button";
import SearchField from "../ui/SearchField";

export type RobotSort = "name-asc" | "name-desc" | "version-desc";
export type RobotView = "grid" | "list";

interface RobotsToolbarProps {
  query: string;
  sort: RobotSort;
  view: RobotView;
  visibleCount: number;
  totalCount: number;
  canImport: boolean;
  canExport: boolean;
  importLocation: string;
  exportDisabled?: boolean;
  onQueryChange: (value: string) => void;
  onSortChange: (value: RobotSort) => void;
  onViewChange: (value: RobotView) => void;
  onImport: () => void;
  onExport: () => void;
}

export default function RobotsToolbar({
  query,
  sort,
  view,
  visibleCount,
  totalCount,
  canImport,
  canExport,
  importLocation,
  exportDisabled = false,
  onQueryChange,
  onSortChange,
  onViewChange,
  onImport,
  onExport,
}: RobotsToolbarProps) {
  return (
    <div className="robots-toolbar">
      <SearchField
        containerClassName="robots-toolbar__search"
        label="Pesquisar robôs nesta localização"
        value={query}
        placeholder="Pesquisar por nome, arquivo ou versão..."
        clearLabel="Limpar pesquisa de robôs"
        onValueChange={onQueryChange}
      />

      <PremiumSelect value={sort} onChange={(event) => onSortChange(event.target.value as RobotSort)} aria-label="Ordenar robôs">
        <option value="name-asc">Nome: A–Z</option>
        <option value="name-desc">Nome: Z–A</option>
        <option value="version-desc">Versão mais recente</option>
      </PremiumSelect>

      <div className="robots-toolbar__view" role="group" aria-label="Visualização dos robôs">
        <IconButton size="sm" label="Visualização em grade" icon={<LayoutGrid size={16} aria-hidden="true" />} aria-pressed={view === "grid"} onClick={() => onViewChange("grid")} />
        <IconButton size="sm" label="Visualização em lista" icon={<List size={16} aria-hidden="true" />} aria-pressed={view === "list"} onClick={() => onViewChange("list")} />
      </div>

      <span className="robots-toolbar__count" aria-live="polite">{visibleCount} de {totalCount}</span>

      <div className="robots-toolbar__actions">
        {canImport && (
          <Button
            variant="primary"
            title={`Importar pacote ZIP para ${importLocation}`}
            onClick={onImport}
          >
            <Upload size={15} strokeWidth={1.9} aria-hidden="true" />
            Importar pacote
          </Button>
        )}

        {canExport && (
          <Button
            variant="secondary"
            title="Exportar um pacote publicado desta localização"
            disabled={exportDisabled}
            onClick={onExport}
          >
            <Download size={15} strokeWidth={1.9} aria-hidden="true" />
            Exportar pacote
          </Button>
        )}
      </div>
    </div>
  );
}

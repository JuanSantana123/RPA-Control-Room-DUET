import PremiumSelect from "../ui/PremiumSelect";
import { Switch } from "../ui/Switch";
import SearchField from "../ui/SearchField";

export type LogLevelFilter = "all" | "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";

interface LogsToolbarProps {
  query: string;
  level: LogLevelFilter;
  autoRefresh: boolean;
  onQueryChange: (value: string) => void;
  onLevelChange: (value: LogLevelFilter) => void;
  onAutoRefreshChange: (value: boolean) => void;
}

export default function LogsToolbar({
  query,
  level,
  autoRefresh,
  onQueryChange,
  onLevelChange,
  onAutoRefreshChange,
}: LogsToolbarProps) {
  return (
    <section className="logs-toolbar" aria-label="Filtros dos registros">
      <SearchField
        label="Pesquisar registros"
        value={query}
        onValueChange={onQueryChange}
        placeholder="Mensagem, evento ou referência da requisição..."
        containerClassName="logs-toolbar__search"
      />

      <div className="logs-toolbar__level">
        <label htmlFor="logs-level-filter">Nível</label>
        <PremiumSelect
          id="logs-level-filter"
          value={level}
          onChange={(event) => onLevelChange(event.target.value as LogLevelFilter)}
        >
          <option value="all">Todos os níveis</option>
          <option value="INFO">Informação</option>
          <option value="WARNING">Avisos</option>
          <option value="ERROR">Erros</option>
          <option value="CRITICAL">Críticos</option>
          <option value="DEBUG">Depuração</option>
        </PremiumSelect>
      </div>

      <Switch
        compact
        checked={autoRefresh}
        onChange={(event) => onAutoRefreshChange(event.target.checked)}
        label="Atualização automática"
        description={autoRefresh ? "Sincronizando a cada 5 segundos" : "Pausada para análise"}
      />
    </section>
  );
}

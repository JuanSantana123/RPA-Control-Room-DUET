import PremiumSelect from "../ui/PremiumSelect";
import { Switch } from "../ui/Switch";
import SearchField from "../ui/SearchField";

export type LogLevelFilter = "all" | "DEBUG" | "INFO" | "WARNING" | "ERROR" | "CRITICAL";
export type LogCategoryFilter =
  | "all"
  | "SYSTEM"
  | "AUDIT"
  | "SECURITY"
  | "INTEGRATION";
interface LogsToolbarProps {
  query: string;
  level: LogLevelFilter;
  category: LogCategoryFilter;
  component: string;
  components: string[];
  autoRefresh: boolean;
  onQueryChange: (value: string) => void;
  onLevelChange: (value: LogLevelFilter) => void;
  onCategoryChange: (value: LogCategoryFilter) => void;
  onComponentChange: (value: string) => void;
  onAutoRefreshChange: (value: boolean) => void;
}

export default function LogsToolbar({
  query,
  level,
  category,
  component,
  components,
  autoRefresh,
  onQueryChange,
  onLevelChange,
  onCategoryChange,
  onComponentChange,
  onAutoRefreshChange,
}: LogsToolbarProps) {
  return (
    <section className="logs-toolbar" aria-label="Filtros dos registros">
      <SearchField
        label="Pesquisar registros"
        value={query}
        onValueChange={onQueryChange}
        placeholder="Mensagem, evento, usuário, recurso ou referência..."
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

      <div className="logs-toolbar__filter">
        <label htmlFor="logs-category-filter">
          Categoria
        </label>

        <PremiumSelect
          id="logs-category-filter"
          value={category}
          onChange={(event) =>
            onCategoryChange(
              event.target.value as LogCategoryFilter
            )
          }
        >
          <option value="all">
            Todas as categorias
          </option>

          <option value="SYSTEM">
            Sistema
          </option>

          <option value="AUDIT">
            Auditoria
          </option>

          <option value="SECURITY">
            Segurança
          </option>

          <option value="INTEGRATION">
            Integrações
          </option>
        </PremiumSelect>
      </div>

      <div className="logs-toolbar__filter">
        <label htmlFor="logs-component-filter">
          Componente
        </label>

        <PremiumSelect
          id="logs-component-filter"
          value={component}
          onChange={(event) =>
            onComponentChange(event.target.value)
          }
        >
          <option value="all">
            Todos os componentes
          </option>

          {components.map((item) => (
            <option
              key={item}
              value={item}
            >
              {item}
            </option>
          ))}
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

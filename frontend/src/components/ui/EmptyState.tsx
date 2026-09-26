import type { ReactNode } from "react";

interface EmptyStateProps {
  icon: ReactNode;
  title: string;
  description: string;
  action?: ReactNode;
  className?: string;
  compact?: boolean;
}

/**
 * Estado vazio compartilhado para listas, tabelas e superfícies operacionais.
 * O ícone comunica o domínio; estrutura, ritmo e hierarquia permanecem iguais.
 */
export default function EmptyState({
  icon,
  title,
  description,
  action,
  className,
  compact = false,
}: EmptyStateProps) {
  return (
    <div
      className={[
        "ui-empty-state",
        compact && "ui-empty-state--compact",
        className,
      ].filter(Boolean).join(" ")}
      role="status"
    >
      <span className="ui-empty-state__icon" aria-hidden="true">{icon}</span>
      <div className="ui-empty-state__copy">
        <h3>{title}</h3>
        <p>{description}</p>
      </div>
      {action && <div className="ui-empty-state__action">{action}</div>}
    </div>
  );
}

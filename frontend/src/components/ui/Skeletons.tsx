interface SkeletonProps {
  className?: string;
}

export function Skeleton({ className = "" }: SkeletonProps) {
  return <span className={`skeleton ${className}`.trim()} aria-hidden="true" />;
}

export function CardGridSkeleton({ count = 3 }: { count?: number }) {
  return (
    <div className="skeleton-card-grid" role="status" aria-label="Carregando conteúdo">
      {Array.from({ length: count }, (_, index) => (
        <div className="skeleton-card" key={index} aria-hidden="true">
          <div className="skeleton-card__top">
            <Skeleton className="skeleton-icon" />
            <Skeleton className="skeleton-chip" />
          </div>
          <Skeleton className="skeleton-line skeleton-line--title" />
          <Skeleton className="skeleton-line" />
          <Skeleton className="skeleton-line skeleton-line--short" />
          <div className="skeleton-card__actions">
            <Skeleton className="skeleton-button" />
            <Skeleton className="skeleton-button" />
          </div>
        </div>
      ))}
      <span className="sr-only">Carregando conteúdo…</span>
    </div>
  );
}

export function TableSkeleton({ rows = 5, columns = 5 }: { rows?: number; columns?: number }) {
  return (
    <div className="skeleton-table" role="status" aria-label="Carregando tabela">
      {Array.from({ length: rows }, (_, row) => (
        <div className="skeleton-table__row" style={{ "--skeleton-columns": columns } as React.CSSProperties} key={row} aria-hidden="true">
          {Array.from({ length: columns }, (_, column) => (
            <Skeleton className={column === 0 ? "skeleton-line skeleton-line--title" : "skeleton-line"} key={column} />
          ))}
        </div>
      ))}
      <span className="sr-only">Carregando tabela…</span>
    </div>
  );
}

export function PanelSkeleton({ lines = 4 }: { lines?: number }) {
  return (
    <div className="skeleton-panel" role="status" aria-label="Carregando conteúdo">
      {Array.from({ length: lines }, (_, index) => (
        <div className="skeleton-panel__row" key={index} aria-hidden="true">
          <Skeleton className="skeleton-icon" />
          <span>
            <Skeleton className="skeleton-line skeleton-line--title" />
            <Skeleton className="skeleton-line skeleton-line--short" />
          </span>
        </div>
      ))}
      <span className="sr-only">Carregando conteúdo…</span>
    </div>
  );
}

export function DashboardSkeleton() {
  return (
    <div className="dashboard-skeleton" role="status" aria-label="Carregando visão geral">
      <div className="dashboard-skeleton__hero" aria-hidden="true">
        <div>
          <Skeleton className="skeleton-chip" />
          <Skeleton className="skeleton-line skeleton-line--heading" />
          <Skeleton className="skeleton-line" />
        </div>
        <Skeleton className="skeleton-orbit" />
      </div>
      <CardGridSkeleton count={4} />
      <div className="dashboard-skeleton__panel" aria-hidden="true">
        <Skeleton className="skeleton-line skeleton-line--title" />
        <TableSkeleton rows={4} columns={4} />
      </div>
      <span className="sr-only">Preparando indicadores e atividade operacional…</span>
    </div>
  );
}

export function PageSkeleton() {
  return (
    <div className="page-skeleton" role="status" aria-label="Carregando módulo">
      <div className="page-skeleton__heading" aria-hidden="true">
        <div>
          <Skeleton className="skeleton-chip" />
          <Skeleton className="skeleton-line skeleton-line--heading" />
          <Skeleton className="skeleton-line" />
        </div>
        <Skeleton className="skeleton-icon skeleton-icon--large" />
      </div>
      <CardGridSkeleton count={3} />
      <span className="sr-only">Carregando módulo…</span>
    </div>
  );
}

export default Skeleton;

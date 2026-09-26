export function BrandMark({ compact = false }: { compact?: boolean }) {
  return (
    <span className={`brand-mark${compact ? " brand-mark--compact" : ""}`} aria-label="DUET CORE">
      <svg viewBox="0 0 36 36" role="img" aria-hidden="true">
        <path d="M7 8.5h8.4c7.7 0 13.1 3.7 13.1 9.5s-5.4 9.5-13.1 9.5H7V8.5Z" />
        <path d="M12.2 13.1h3.1c4.6 0 7.5 1.8 7.5 4.9s-2.9 4.9-7.5 4.9h-3.1v-9.8Z" className="brand-mark-cutout" />
        <circle cx="28.5" cy="8" r="3" className="brand-mark-accent" />
      </svg>
      {!compact && <span className="brand-wordmark"><strong>DUET</strong><small>CORE</small></span>}
    </span>
  );
}

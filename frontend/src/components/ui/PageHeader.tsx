import { useId, type ReactNode } from "react";

interface PageHeaderProps {
  eyebrow: string;
  title: string;
  description: string;
  actions?: ReactNode;
  className?: string;
}

export default function PageHeader({ eyebrow, title, description, actions, className }: PageHeaderProps) {
  const titleId = useId();

  return (
    <header
      className={["page-heading", "ui-page-header", className].filter(Boolean).join(" ")}
      aria-labelledby={titleId}
    >
      <div className="ui-page-header__copy">
        <p className="page-eyebrow ui-page-header__eyebrow">{eyebrow}</p>
        <h1 id={titleId}>{title}</h1>
        <p className="ui-page-header__description">{description}</p>
      </div>
      {actions && <div className="ui-page-header__actions">{actions}</div>}
    </header>
  );
}

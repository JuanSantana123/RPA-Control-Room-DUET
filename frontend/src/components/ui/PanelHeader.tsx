import { useId, type ElementType, type ReactNode } from "react";

interface PanelHeaderProps {
  title: ReactNode;
  description?: ReactNode;
  icon?: ReactNode;
  actions?: ReactNode;
  headingLevel?: 2 | 3;
  titleId?: string;
  className?: string;
}

export default function PanelHeader({
  title,
  description,
  icon,
  actions,
  headingLevel = 2,
  titleId,
  className,
}: PanelHeaderProps) {
  const generatedId = useId();
  const Heading = `h${headingLevel}` as ElementType;

  return (
    <header
      className={["ui-panel-header", className].filter(Boolean).join(" ")}
      aria-labelledby={titleId || generatedId}
    >
      <div className="ui-panel-header__identity">
        {icon && <span className="ui-panel-header__icon" aria-hidden="true">{icon}</span>}
        <div className="ui-panel-header__copy">
          <Heading id={titleId || generatedId}>{title}</Heading>
          {description && <p>{description}</p>}
        </div>
      </div>
      {actions && <div className="ui-panel-header__actions">{actions}</div>}
    </header>
  );
}

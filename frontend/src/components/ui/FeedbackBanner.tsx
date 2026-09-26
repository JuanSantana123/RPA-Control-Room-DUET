import { CheckCircle2, CircleAlert, Info, X } from "lucide-react";
import { Button, IconButton } from "./Button";

interface FeedbackAction {
  label: string;
  onClick: () => void | Promise<void>;
  busy?: boolean;
}

interface FeedbackBannerProps {
  tone?: "error" | "success" | "info";
  title: string;
  message: string;
  hint?: string;
  onDismiss?: () => void;
  action?: FeedbackAction;
}

const icons = {
  error: CircleAlert,
  success: CheckCircle2,
  info: Info,
};

export default function FeedbackBanner({ tone = "info", title, message, hint, onDismiss, action }: FeedbackBannerProps) {
  const Icon = icons[tone];

  return (
    <div className={`feedback-banner feedback-banner--${tone}`} role={tone === "error" ? "alert" : "status"}>
      <span className="feedback-banner__icon" aria-hidden="true">
        <Icon size={19} strokeWidth={1.9} />
      </span>
      <div className="feedback-banner__content">
        <strong>{title}</strong>
        <span>{message}</span>
        {hint && <small>{hint}</small>}
      </div>
      {(action || onDismiss) && (
        <div className="feedback-banner__actions">
          {action && (
            <Button
              size="sm"
              variant="ghost"
              busy={action.busy}
              loadingLabel={`${action.label} em andamento`}
              onClick={action.onClick}
            >
              {action.label}
            </Button>
          )}
          {onDismiss && (
            <IconButton
              size="sm"
              className="feedback-banner__dismiss"
              label="Fechar mensagem"
              icon={<X size={16} aria-hidden="true" />}
              onClick={onDismiss}
            />
          )}
        </div>
      )}
    </div>
  );
}

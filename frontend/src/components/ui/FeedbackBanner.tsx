import { CheckCircle2, CircleAlert, Info, X } from "lucide-react";
import { IconButton } from "./Button";

interface FeedbackBannerProps {
  tone?: "error" | "success" | "info";
  title: string;
  message: string;
  hint?: string;
  onDismiss?: () => void;
}

const icons = {
  error: CircleAlert,
  success: CheckCircle2,
  info: Info,
};

export default function FeedbackBanner({ tone = "info", title, message, hint, onDismiss }: FeedbackBannerProps) {
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
  );
}

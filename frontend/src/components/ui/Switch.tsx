import { forwardRef, type InputHTMLAttributes, type ReactNode } from "react";

interface SwitchProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "type" | "role"> {
  label: ReactNode;
  description?: ReactNode;
  compact?: boolean;
}

export const Switch = forwardRef<HTMLInputElement, SwitchProps>(function Switch(
  { label, description, compact = false, className, ...props },
  ref,
) {
  return (
    <label className={`ui-switch${compact ? " ui-switch--compact" : ""}${className ? ` ${className}` : ""}`}>
      <input {...props} ref={ref} type="checkbox" role="switch" />
      <span className="ui-switch__copy">
        <strong>{label}</strong>
        {description && <small>{description}</small>}
      </span>
    </label>
  );
});

import {
  forwardRef,
  useId,
  type InputHTMLAttributes,
  type ReactNode,
} from "react";

interface TextFieldProps extends Omit<InputHTMLAttributes<HTMLInputElement>, "size"> {
  label: ReactNode;
  description?: string;
  error?: string;
  leadingIcon?: ReactNode;
  trailingAction?: ReactNode;
  labelHidden?: boolean;
  containerClassName?: string;
}

export const TextField = forwardRef<HTMLInputElement, TextFieldProps>(function TextField(
  {
    id: providedId,
    label,
    description,
    error,
    leadingIcon,
    trailingAction,
    labelHidden = false,
    containerClassName,
    className,
    required,
    type = "text",
    ...props
  },
  ref,
) {
  const generatedId = useId();
  const id = providedId ?? generatedId;
  const descriptionId = description ? `${id}-description` : undefined;
  const errorId = error ? `${id}-error` : undefined;
  const describedBy = [props["aria-describedby"], descriptionId, errorId]
    .filter(Boolean)
    .join(" ") || undefined;

  return (
    <div className={["ui-field", containerClassName].filter(Boolean).join(" ")}>
      <label className={labelHidden ? "sr-only" : "ui-field__label"} htmlFor={id}>
        {label}
        {required && <span className="ui-field__required">obrigatório</span>}
      </label>
      {description && !labelHidden && (
        <span className="ui-field__description" id={descriptionId}>{description}</span>
      )}
      <div
        className={[
          "ui-input-shell",
          leadingIcon && "ui-input-shell--leading",
          trailingAction && "ui-input-shell--trailing",
          type === "search" && "ui-input-shell--search",
          error && "ui-input-shell--error",
        ].filter(Boolean).join(" ")}
      >
        {leadingIcon && <span className="ui-input-shell__leading" aria-hidden="true">{leadingIcon}</span>}
        <input
          {...props}
          ref={ref}
          id={id}
          type={type}
          required={required}
          className={["ui-input", className].filter(Boolean).join(" ")}
          aria-invalid={Boolean(error) || undefined}
          aria-describedby={describedBy}
        />
        {trailingAction && <span className="ui-input-shell__trailing">{trailingAction}</span>}
      </div>
      {error && <span className="ui-field__error" id={errorId}>{error}</span>}
    </div>
  );
});

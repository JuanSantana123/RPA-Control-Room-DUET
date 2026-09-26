import {
  forwardRef,
  useId,
  type ReactNode,
  type TextareaHTMLAttributes,
} from "react";

interface TextAreaFieldProps extends TextareaHTMLAttributes<HTMLTextAreaElement> {
  label: string;
  description?: string;
  error?: string;
  labelHidden?: boolean;
  counter?: ReactNode;
  containerClassName?: string;
}

export const TextAreaField = forwardRef<HTMLTextAreaElement, TextAreaFieldProps>(function TextAreaField(
  {
    id: providedId,
    label,
    description,
    error,
    labelHidden = false,
    counter,
    containerClassName,
    className,
    required,
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
    <div className={["ui-field", "ui-textarea-field", containerClassName].filter(Boolean).join(" ")}>
      <div className="ui-textarea-field__heading">
        <label className={labelHidden ? "sr-only" : "ui-field__label"} htmlFor={id}>
          {label}
          {required && <span className="ui-field__required">obrigatório</span>}
        </label>
        {counter && <span className="ui-textarea-field__counter">{counter}</span>}
      </div>
      {description && !labelHidden && (
        <span className="ui-field__description" id={descriptionId}>{description}</span>
      )}
      <textarea
        {...props}
        ref={ref}
        id={id}
        required={required}
        className={["ui-textarea", className].filter(Boolean).join(" ")}
        aria-invalid={Boolean(error) || undefined}
        aria-describedby={describedBy}
      />
      {error && <span className="ui-field__error" id={errorId}>{error}</span>}
    </div>
  );
});

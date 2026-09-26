import { forwardRef, type ButtonHTMLAttributes, type ReactNode } from "react";

export type ButtonVariant = "primary" | "secondary" | "ghost" | "danger";
export type ButtonSize = "sm" | "md" | "lg";

interface ButtonProps extends ButtonHTMLAttributes<HTMLButtonElement> {
  variant?: ButtonVariant;
  size?: ButtonSize;
  busy?: boolean;
  fullWidth?: boolean;
  loadingLabel?: string;
}

function classes(...values: Array<string | false | undefined>) {
  return values.filter(Boolean).join(" ");
}

function buttonClassName({
  variant = "secondary",
  size = "md",
  fullWidth = false,
  className,
}: {
  variant?: ButtonVariant;
  size?: ButtonSize;
  fullWidth?: boolean;
  className?: string;
} = {}) {
  return classes(
    "ui-button",
    `ui-button--${variant}`,
    `ui-button--${size}`,
    fullWidth && "ui-button--full",
    className,
  );
}

export const Button = forwardRef<HTMLButtonElement, ButtonProps>(function Button(
  {
    variant = "secondary",
    size = "md",
    busy = false,
    fullWidth = false,
    loadingLabel = "Processando",
    className,
    disabled,
    type,
    children,
    ...props
  },
  ref,
) {
  return (
    <button
      {...props}
      ref={ref}
      type={type ?? "button"}
      className={buttonClassName({ variant, size, fullWidth, className })}
      aria-busy={busy || undefined}
      disabled={disabled || busy}
      data-loading={busy || undefined}
    >
      <span className="ui-button__content">{children}</span>
      {busy && (
        <>
          <span className="ui-button__spinner" aria-hidden="true" />
          <span className="sr-only">{loadingLabel}</span>
        </>
      )}
    </button>
  );
});

interface IconButtonProps
  extends Omit<ButtonHTMLAttributes<HTMLButtonElement>, "aria-label" | "children"> {
  label: string;
  icon: ReactNode;
  variant?: Exclude<ButtonVariant, "primary">;
  size?: Exclude<ButtonSize, "lg">;
  busy?: boolean;
  tooltip?: string;
}

export const IconButton = forwardRef<HTMLButtonElement, IconButtonProps>(function IconButton(
  {
    label,
    icon,
    variant = "ghost",
    size = "md",
    busy = false,
    tooltip,
    className,
    disabled,
    type,
    ...props
  },
  ref,
) {
  return (
    <button
      {...props}
      ref={ref}
      type={type ?? "button"}
      className={classes(
        "ui-button",
        "ui-button--icon",
        `ui-button--${variant}`,
        `ui-button--${size}`,
        className,
      )}
      aria-label={label}
      aria-busy={busy || undefined}
      title={tooltip}
      disabled={disabled || busy}
      data-loading={busy || undefined}
    >
      <span className="ui-button__content" aria-hidden="true">{icon}</span>
      {busy && <span className="ui-button__spinner" aria-hidden="true" />}
    </button>
  );
});

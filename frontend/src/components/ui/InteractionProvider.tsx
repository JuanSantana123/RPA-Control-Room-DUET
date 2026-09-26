import {
  useCallback,
  useEffect,
  useMemo,
  useRef,
  useState,
  type ReactNode,
} from "react";
import { createPortal } from "react-dom";
import {
  CheckCircle2,
  CircleAlert,
  Info,
  ShieldAlert,
  TriangleAlert,
  X,
} from "lucide-react";
import {
  InteractionContext,
  type ConfirmationOptions,
  type InteractionTone,
  type NotificationOptions,
} from "../../context/interaction-context";
import { useDialogFocus } from "../../hooks/ui/useDialogFocus";
import { Button, IconButton } from "./Button";
import { TextField } from "./TextField";

interface PendingConfirmation extends ConfirmationOptions {
  id: number;
  resolve: (confirmed: boolean) => void;
}

interface NotificationItem extends Required<Pick<NotificationOptions, "title" | "tone">> {
  id: number;
  message?: string;
}

const notificationIcons: Record<InteractionTone, typeof Info> = {
  info: Info,
  success: CheckCircle2,
  warning: TriangleAlert,
  danger: CircleAlert,
};

export default function InteractionProvider({ children }: { children: ReactNode }) {
  const sequence = useRef(0);
  const activeConfirmation = useRef<PendingConfirmation | null>(null);
  const confirmationQueue = useRef<PendingConfirmation[]>([]);
  const notificationTimers = useRef(new Map<number, number>());
  const [confirmation, setConfirmation] = useState<PendingConfirmation | null>(null);
  const [confirmationText, setConfirmationText] = useState("");
  const [notifications, setNotifications] = useState<NotificationItem[]>([]);

  const removeNotification = useCallback((id: number) => {
    const timer = notificationTimers.current.get(id);
    if (timer !== undefined) window.clearTimeout(timer);
    notificationTimers.current.delete(id);
    setNotifications((current) => current.filter((item) => item.id !== id));
  }, []);

  const notify = useCallback((options: NotificationOptions) => {
    const id = ++sequence.current;
    const tone = options.tone ?? "info";
    const item: NotificationItem = {
      id,
      title: options.title,
      tone,
      ...(options.message ? { message: options.message } : {}),
    };

    setNotifications((current) => [...current.slice(-3), item]);

    const timeoutMs = options.timeoutMs === undefined
      ? (tone === "danger" ? 7_000 : 4_500)
      : options.timeoutMs;

    if (timeoutMs !== null && timeoutMs > 0) {
      const timer = window.setTimeout(() => removeNotification(id), timeoutMs);
      notificationTimers.current.set(id, timer);
    }
  }, [removeNotification]);

  const confirm = useCallback((options: ConfirmationOptions) => (
    new Promise<boolean>((resolve) => {
      const request: PendingConfirmation = {
        ...options,
        id: ++sequence.current,
        resolve,
      };

      if (activeConfirmation.current) {
        confirmationQueue.current.push(request);
        return;
      }

      activeConfirmation.current = request;
      setConfirmationText("");
      setConfirmation(request);
    })
  ), []);

  const completeConfirmation = useCallback((confirmed: boolean) => {
    const current = activeConfirmation.current;
    if (!current) return;

    current.resolve(confirmed);
    const next = confirmationQueue.current.shift() ?? null;
    activeConfirmation.current = next;
    setConfirmationText("");
    setConfirmation(next);
  }, []);

  useEffect(() => () => {
    activeConfirmation.current?.resolve(false);
    confirmationQueue.current.forEach((item) => item.resolve(false));
    notificationTimers.current.forEach((timer) => window.clearTimeout(timer));
  }, []);

  const contextValue = useMemo(() => ({ confirm, notify }), [confirm, notify]);

  return (
    <InteractionContext.Provider value={contextValue}>
      {children}
      {confirmation && (
        <ConfirmationDialog
          confirmation={confirmation}
          confirmationText={confirmationText}
          onConfirmationTextChange={setConfirmationText}
          onCancel={() => completeConfirmation(false)}
          onConfirm={() => completeConfirmation(true)}
        />
      )}
      {typeof document !== "undefined" && createPortal(
        <div className="ui-toast-region" aria-label="Notificações" aria-live="polite">
          {notifications.map((item) => {
            const Icon = notificationIcons[item.tone];
            return (
              <article className={`ui-toast ui-toast--${item.tone}`} key={item.id} role={item.tone === "danger" ? "alert" : "status"}>
                <span className="ui-toast__icon" aria-hidden="true"><Icon size={18} /></span>
                <div className="ui-toast__content">
                  <strong>{item.title}</strong>
                  {item.message && <p>{item.message}</p>}
                </div>
                <IconButton
                  size="sm"
                  label="Fechar notificação"
                  icon={<X size={15} />}
                  onClick={() => removeNotification(item.id)}
                />
              </article>
            );
          })}
        </div>,
        document.body,
      )}
    </InteractionContext.Provider>
  );
}

function ConfirmationDialog({
  confirmation,
  confirmationText,
  onConfirmationTextChange,
  onCancel,
  onConfirm,
}: {
  confirmation: PendingConfirmation;
  confirmationText: string;
  onConfirmationTextChange: (value: string) => void;
  onCancel: () => void;
  onConfirm: () => void;
}) {
  const titleId = `confirmation-title-${confirmation.id}`;
  const descriptionId = `confirmation-description-${confirmation.id}`;
  const dangerous = confirmation.tone === "danger";
  const confirmedText = !confirmation.requireText
    || confirmationText === confirmation.requireText.expected;
  const dialogRef = useDialogFocus<HTMLDivElement>({
    open: true,
    onClose: onCancel,
  });

  return createPortal(
    <div className="ui-confirmation-backdrop" onMouseDown={(event) => {
      if (event.currentTarget === event.target) onCancel();
    }}>
      <div
        ref={dialogRef}
        className="ui-confirmation-dialog"
        role="alertdialog"
        aria-modal="true"
        aria-labelledby={titleId}
        aria-describedby={descriptionId}
        tabIndex={-1}
      >
        <div className={`ui-confirmation-dialog__icon ${dangerous ? "is-danger" : ""}`} aria-hidden="true">
          {dangerous ? <ShieldAlert size={22} /> : <Info size={22} />}
        </div>
        <div className="ui-confirmation-dialog__body">
          <span className="ui-confirmation-dialog__eyebrow">Confirmação necessária</span>
          <h2 id={titleId}>{confirmation.title}</h2>
          <p id={descriptionId}>{confirmation.description}</p>
          {confirmation.detail && <div className="ui-confirmation-dialog__detail">{confirmation.detail}</div>}
          {confirmation.requireText && (
            <TextField
              data-autofocus
              label={confirmation.requireText.label ?? `Digite “${confirmation.requireText.expected}” para confirmar`}
              value={confirmationText}
              placeholder={confirmation.requireText.placeholder ?? confirmation.requireText.expected}
              autoComplete="off"
              onChange={(event) => onConfirmationTextChange(event.target.value)}
              onKeyDown={(event) => {
                if (event.key === "Enter" && confirmedText) onConfirm();
              }}
            />
          )}
        </div>
        <div className="ui-confirmation-dialog__actions">
          <Button data-autofocus={!confirmation.requireText || undefined} variant="ghost" onClick={onCancel}>
            {confirmation.cancelLabel ?? "Cancelar"}
          </Button>
          <Button variant={dangerous ? "danger" : "primary"} disabled={!confirmedText} onClick={onConfirm}>
            {confirmation.confirmLabel ?? "Confirmar"}
          </Button>
        </div>
      </div>
    </div>,
    document.body,
  );
}

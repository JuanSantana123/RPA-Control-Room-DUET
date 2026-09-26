import { createContext } from "react";

export type InteractionTone = "info" | "success" | "warning" | "danger";

export interface ConfirmationTextRequirement {
  expected: string;
  label?: string;
  placeholder?: string;
}

export interface ConfirmationOptions {
  title: string;
  description: string;
  confirmLabel?: string;
  cancelLabel?: string;
  tone?: "default" | "danger";
  detail?: string;
  requireText?: ConfirmationTextRequirement;
}

export interface NotificationOptions {
  title: string;
  message?: string;
  tone?: InteractionTone;
  timeoutMs?: number | null;
}

export interface InteractionContextValue {
  confirm: (options: ConfirmationOptions) => Promise<boolean>;
  notify: (options: NotificationOptions) => void;
}

export const InteractionContext = createContext<InteractionContextValue | null>(null);

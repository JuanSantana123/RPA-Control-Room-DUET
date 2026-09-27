import { useEffect, useRef } from "react";

const FOCUSABLE_SELECTOR = [
  "button:not([disabled])",
  "[href]",
  "input:not([disabled])",
  "select:not([disabled])",
  "textarea:not([disabled])",
  "[tabindex]:not([tabindex='-1'])",
].join(",");

interface DialogFocusOptions {
  open: boolean;
  onClose: () => void;
  closeOnEscape?: boolean;
}

export function useDialogFocus<T extends HTMLElement>({
  open,
  onClose,
  closeOnEscape = true,
}: DialogFocusOptions) {
  const dialogRef = useRef<T>(null);
  const onCloseRef = useRef(onClose);

  useEffect(() => {
    onCloseRef.current = onClose;
  }, [onClose]);

  useEffect(() => {
    if (!open) return;

    const previousFocus = document.activeElement instanceof HTMLElement
      ? document.activeElement
      : null;
    const previousOverflow = document.body.style.overflow;
    document.body.style.overflow = "hidden";

    // Enquanto um diálogo modal estiver ativo, todo conteúdo adjacente fica
    // indisponível também para leitores de tela e navegação programática.
    // O percurso por ancestrais funciona sem exigir um portal específico.
    const hiddenSiblings: Array<{
      element: HTMLElement;
      inert: boolean;
      ariaHidden: string | null;
    }> = [];
    let currentNode: HTMLElement | null = dialogRef.current;
    while (currentNode?.parentElement && currentNode.parentElement !== document.body) {
      const parent: HTMLElement = currentNode.parentElement;
      for (const sibling of parent.children) {
        if (sibling === currentNode || !(sibling instanceof HTMLElement)) continue;
        hiddenSiblings.push({
          element: sibling,
          inert: sibling.inert,
          ariaHidden: sibling.getAttribute("aria-hidden"),
        });
        sibling.inert = true;
        sibling.setAttribute("aria-hidden", "true");
      }
      currentNode = parent;
    }

    const focusInitialControl = window.requestAnimationFrame(() => {
      const dialog = dialogRef.current;
      const preferredControl = dialog?.querySelector<HTMLElement>("[data-autofocus]");
      const firstControl = dialog?.querySelector<HTMLElement>(FOCUSABLE_SELECTOR);
      (preferredControl ?? firstControl ?? dialog)?.focus();
    });

    const handleKeyDown = (event: KeyboardEvent) => {
      const dialog = dialogRef.current;
      if (!dialog) return;

      if (event.key === "Escape" && closeOnEscape) {
        event.preventDefault();
        onCloseRef.current();
        return;
      }

      if (event.key !== "Tab") return;

      const controls = [...dialog.querySelectorAll<HTMLElement>(FOCUSABLE_SELECTOR)]
        .filter((element) => !element.hidden && element.getClientRects().length > 0);
      const firstControl = controls[0];
      const lastControl = controls.at(-1);

      if (!firstControl || !lastControl) {
        event.preventDefault();
        dialog.focus();
        return;
      }

      if (event.shiftKey && document.activeElement === firstControl) {
        event.preventDefault();
        lastControl.focus();
      } else if (!event.shiftKey && document.activeElement === lastControl) {
        event.preventDefault();
        firstControl.focus();
      }
    };

    document.addEventListener("keydown", handleKeyDown);
    return () => {
      window.cancelAnimationFrame(focusInitialControl);
      document.removeEventListener("keydown", handleKeyDown);
      document.body.style.overflow = previousOverflow;
      for (const { element, inert, ariaHidden } of hiddenSiblings) {
        element.inert = inert;
        if (ariaHidden === null) element.removeAttribute("aria-hidden");
        else element.setAttribute("aria-hidden", ariaHidden);
      }
      previousFocus?.focus();
    };
  }, [closeOnEscape, open]);

  return dialogRef;
}

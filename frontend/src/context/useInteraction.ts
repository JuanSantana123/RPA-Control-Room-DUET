import { useContext } from "react";
import { InteractionContext } from "./interaction-context";

export function useInteraction() {
  const context = useContext(InteractionContext);

  if (!context) {
    throw new Error("useInteraction deve ser utilizado dentro de InteractionProvider.");
  }

  return context;
}

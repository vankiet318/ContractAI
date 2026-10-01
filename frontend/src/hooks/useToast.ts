import { createContext, useContext } from "react";

export type ToastVariant = "error" | "success" | "info";

export interface ToastApi {
  showToast: (message: string, variant?: ToastVariant) => void;
}

export const ToastContext = createContext<ToastApi | null>(null);

export function useToast(): ToastApi {
  const toast = useContext(ToastContext);

  if (!toast) {
    throw new Error("useToast must be used inside <ToastProvider>");
  }

  return toast;
}

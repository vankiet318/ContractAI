import { useCallback, useMemo, useState } from "react";
import { TOAST_DURATION_MS } from "../constants";
import { ToastContext, type ToastVariant } from "../hooks/useToast";
import { generateId } from "../lib/id";

const STYLES: Record<ToastVariant, string> = {
  error: "border-red-200 bg-red-50 text-red-800",
  success: "border-emerald-200 bg-emerald-50 text-emerald-800",
  info: "border-slate-200 bg-white text-slate-800",
};

interface Toast {
  id: string;
  message: string;
  variant: ToastVariant;
}

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [toasts, setToasts] = useState<Toast[]>([]);

  const dismiss = useCallback((id: string) => {
    setToasts((previous) => previous.filter((toast) => toast.id !== id));
  }, []);

  const showToast = useCallback(
    (message: string, variant: ToastVariant = "info") => {
      const id = generateId();

      setToasts((previous) => [...previous, { id, message, variant }]);
      setTimeout(() => dismiss(id), TOAST_DURATION_MS);
    },
    [dismiss],
  );

  const toastApi = useMemo(() => ({ showToast }), [showToast]);

  return (
    <ToastContext.Provider value={toastApi}>
      {children}

      <div
        aria-live="polite"
        className="fixed bottom-4 right-4 z-50 flex w-80 flex-col gap-2"
      >
        {toasts.map((toast) => (
          <div
            key={toast.id}
            role={toast.variant === "error" ? "alert" : "status"}
            className={`flex items-start gap-2 rounded-md border px-3 py-2 text-sm shadow-md ${STYLES[toast.variant]}`}
          >
            <p className="flex-1">{toast.message}</p>
            <button
              type="button"
              title="Đóng"
              onClick={() => dismiss(toast.id)}
              className="flex h-5 w-5 shrink-0 items-center justify-center rounded-full opacity-60 hover:opacity-100"
            >
              ×
            </button>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

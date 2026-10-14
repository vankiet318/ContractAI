import { CircleAlert, CircleCheck, Info } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { TOAST_DURATION_MS } from "../constants";
import { ToastContext, type ToastVariant } from "../hooks/useToast";
import { generateId } from "../lib/id";

// Same dark surface as the primary button; only the icon tells variants apart.
const ICONS: Record<ToastVariant, React.ReactNode> = {
  error: <CircleAlert className="h-4 w-4 shrink-0 text-red-400" />,
  success: <CircleCheck className="h-4 w-4 shrink-0 text-emerald-400" />,
  info: <Info className="h-4 w-4 shrink-0 text-slate-400" />,
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
          <button
            key={toast.id}
            type="button"
            role={toast.variant === "error" ? "alert" : "status"}
            title="Bấm để đóng"
            onClick={() => dismiss(toast.id)}
            className="flex items-start gap-2.5 rounded-md bg-slate-900 px-3 py-2.5 text-left text-sm text-white shadow-lg"
          >
            <span className="mt-0.5">{ICONS[toast.variant]}</span>
            <span className="flex-1">{toast.message}</span>
          </button>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

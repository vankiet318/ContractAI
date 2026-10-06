import { X } from "lucide-react";
import { useCallback, useMemo, useState } from "react";
import { TOAST_DURATION_MS } from "../constants";
import { ToastContext, type ToastVariant } from "../hooks/useToast";
import { generateId } from "../lib/id";
import { IconButton } from "./ui/Button";

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
            className={`flex items-start gap-2 rounded-lg border px-3 py-2 text-sm shadow-md ${STYLES[toast.variant]}`}
          >
            <p className="flex-1 py-0.5">{toast.message}</p>
            <IconButton
              title="Đóng"
              onClick={() => dismiss(toast.id)}
              className="-my-1 -mr-1.5"
            >
              <X className="w-4 h-4" />
            </IconButton>
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

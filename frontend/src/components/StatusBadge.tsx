import type { DocumentStatus } from "../types";

const STYLES: Record<DocumentStatus, string> = {
  processing: "bg-amber-100 text-amber-800",
  ready: "bg-emerald-100 text-emerald-800",
  failed: "bg-red-100 text-red-800",
};

const LABELS: Record<DocumentStatus, string> = {
  processing: "Processing",
  ready: "Ready",
  failed: "Failed",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <span
      className={`px-2 py-0.5 rounded-full text-xs font-medium ${STYLES[status]}`}
    >
      {LABELS[status]}
    </span>
  );
}

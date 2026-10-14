import type { DocumentStatus } from "../types";

// Colour is limited to a small dot; the label stays in the text colour.
const DOT_STYLES: Record<DocumentStatus, string> = {
  processing: "bg-slate-400 animate-pulse",
  ready: "bg-emerald-500",
  failed: "bg-red-500",
};

const LABELS: Record<DocumentStatus, string> = {
  processing: "Đang xử lý",
  ready: "Sẵn sàng",
  failed: "Lỗi",
};

export function StatusBadge({ status }: { status: DocumentStatus }) {
  return (
    <span className="inline-flex items-center gap-1.5 text-xs text-slate-500">
      <span className={`h-1.5 w-1.5 rounded-full ${DOT_STYLES[status]}`} />
      {LABELS[status]}
    </span>
  );
}
